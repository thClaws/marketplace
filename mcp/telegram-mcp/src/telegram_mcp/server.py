"""thClaws Telegram MCP server.

This server exposes Telegram Bot API actions as MCP tools so an agent
can notify users, send artifacts, or inspect recent bot updates without
turning Telegram into the primary thClaws UI.
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any, BinaryIO

import httpx
from mcp.server.fastmcp import FastMCP

DEFAULT_API_BASE = "https://api.telegram.org"
MAX_MESSAGE_CHARS = 4096
MAX_PHOTO_BYTES = 10 * 1024 * 1024
MAX_DOCUMENT_BYTES = 50 * 1024 * 1024
PARSE_MODES = {"MarkdownV2", "HTML", "Markdown"}
_ALLOWED_FILE_ROOTS_CACHE: tuple[str, tuple[Path, ...]] | None = None


class TelegramConfigError(RuntimeError):
    """Raised when required Telegram MCP environment is missing."""


class TelegramApiError(RuntimeError):
    """Raised when Telegram returns a non-ok API response."""


def _token() -> str:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise TelegramConfigError("TELEGRAM_BOT_TOKEN is required")
    return token


def _api_base() -> str:
    return os.environ.get("TELEGRAM_API_BASE", DEFAULT_API_BASE).rstrip("/")


def _allowed_chat_ids() -> set[str]:
    raw = os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS", "")
    allowed = {item.strip() for item in raw.split(",") if item.strip()}
    if not allowed:
        raise TelegramConfigError(
            "TELEGRAM_ALLOWED_CHAT_IDS is required; set a comma-separated "
            "allowlist of chat IDs this MCP server may access"
        )
    return allowed


def _normalize_chat_id(chat_id: str | int) -> str:
    normalized = str(chat_id).strip()
    if not normalized:
        raise TelegramConfigError("chat_id is required")
    return normalized


def _check_chat_allowed(chat_id: str | int) -> str:
    normalized = _normalize_chat_id(chat_id)
    if normalized not in _allowed_chat_ids():
        raise TelegramConfigError(
            f"chat_id {normalized!r} is not allowed by TELEGRAM_ALLOWED_CHAT_IDS"
        )
    return normalized


def _api_url(method: str) -> str:
    return f"{_api_base()}/bot{_token()}/{method}"


def _telegram_result(data: dict[str, Any], method: str) -> Any:
    if data.get("ok") is not True:
        description = data.get("description") or "unknown Telegram API error"
        error_code = data.get("error_code")
        if method == "getUpdates" and error_code == 409:
            description = (
                f"{description}. Telegram returned a conflict while polling "
                "updates; if this bot has a webhook configured, call "
                "deleteWebhook before using telegram_get_updates."
            )
        if error_code is None:
            raise TelegramApiError(f"{method}: {description}")
        raise TelegramApiError(f"{method}: [{error_code}] {description}")
    return data.get("result")


async def _telegram_response(resp: httpx.Response, method: str) -> Any:
    """Parse Telegram JSON before raising HTTP status errors.

    Telegram returns useful API errors such as "chat not found" inside a
    JSON body that may arrive with HTTP 400/403. If we call
    raise_for_status() first, that description is lost.
    """
    try:
        data = resp.json()
    except ValueError:
        resp.raise_for_status()
        raise TelegramApiError(f"{method}: response was not valid JSON")
    if isinstance(data, dict):
        result = _telegram_result(data, method)
        resp.raise_for_status()
        return result
    resp.raise_for_status()
    raise TelegramApiError(f"{method}: response JSON was not an object")


async def _post_json(method: str, payload: dict[str, Any]) -> Any:
    async with httpx.AsyncClient() as client:
        resp = await client.post(_api_url(method), json=payload, timeout=20.0)
    return await _telegram_response(resp, method)


def _allowed_file_roots() -> tuple[Path, ...]:
    global _ALLOWED_FILE_ROOTS_CACHE
    raw = os.environ.get("TELEGRAM_ALLOWED_FILE_ROOTS", "")
    if _ALLOWED_FILE_ROOTS_CACHE and _ALLOWED_FILE_ROOTS_CACHE[0] == raw:
        return _ALLOWED_FILE_ROOTS_CACHE[1]

    roots: list[Path] = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        root = Path(item).expanduser().resolve()
        if not root.is_dir():
            raise TelegramConfigError(
                f"TELEGRAM_ALLOWED_FILE_ROOTS entry is not a directory: {item}"
            )
        roots.append(root)
    if not roots:
        raise TelegramConfigError(
            "TELEGRAM_ALLOWED_FILE_ROOTS is required for file uploads; "
            "set a comma-separated list of directories the agent may send from"
        )
    _ALLOWED_FILE_ROOTS_CACHE = (raw, tuple(roots))
    return _ALLOWED_FILE_ROOTS_CACHE[1]


def _resolve_allowed_file(file_path: str) -> Path:
    if str(file_path).startswith(("http://", "https://")):
        raise TelegramConfigError("file_path must be a local path, not a URL")
    try:
        resolved = Path(file_path).expanduser().resolve(strict=True)
    except FileNotFoundError as exc:
        raise TelegramConfigError(f"file_path does not exist or is not a file: {file_path}")
    except OSError as exc:
        raise TelegramConfigError(f"file_path cannot be resolved: {file_path}: {exc}") from exc
    if not resolved.is_file():
        raise TelegramConfigError(f"file_path does not exist or is not a file: {file_path}")
    for root in _allowed_file_roots():
        if resolved == root or root in resolved.parents:
            return resolved
    raise TelegramConfigError(
        f"file_path is outside TELEGRAM_ALLOWED_FILE_ROOTS: {file_path}"
    )


def _open_allowed_file(file_path: str, max_bytes: int) -> tuple[Path, BinaryIO]:
    path = _resolve_allowed_file(file_path)
    flags = os.O_RDONLY
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise TelegramConfigError(f"file_path cannot be opened safely: {file_path}: {exc}") from exc

    try:
        opened_stat = os.fstat(fd)
        if not stat.S_ISREG(opened_stat.st_mode):
            raise TelegramConfigError(f"file_path is not a regular file: {file_path}")
        if opened_stat.st_size > max_bytes:
            raise TelegramConfigError(
                f"file_path is too large: {opened_stat.st_size} bytes "
                f"(max {max_bytes} bytes)"
            )
        return path, os.fdopen(fd, "rb")
    except Exception:
        os.close(fd)
        raise


async def _post_file(
    method: str,
    file_field: str,
    chat_id: str,
    file_path: str,
    caption: str | None,
    max_bytes: int,
) -> Any:
    path, handle = _open_allowed_file(file_path, max_bytes)

    data: dict[str, str] = {"chat_id": chat_id}
    if caption:
        data["caption"] = caption

    with handle:
        files = {file_field: (path.name, handle)}
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                _api_url(method),
                data=data,
                files=files,
                timeout=60.0,
            )
    return await _telegram_response(resp, method)


def _validate_message_text(text: str) -> str:
    if not text:
        raise TelegramConfigError("text is required")
    if len(text) > MAX_MESSAGE_CHARS:
        raise TelegramConfigError(
            f"text exceeds Telegram's {MAX_MESSAGE_CHARS}-character message limit"
        )
    return text


def _validate_parse_mode(parse_mode: str | None) -> str | None:
    if parse_mode is None or parse_mode == "":
        return None
    if parse_mode not in PARSE_MODES:
        allowed = ", ".join(sorted(PARSE_MODES))
        raise TelegramConfigError(f"parse_mode must be one of: {allowed}")
    return parse_mode


def _message_summary(result: dict[str, Any]) -> str:
    chat = result.get("chat") if isinstance(result.get("chat"), dict) else {}
    return json.dumps(
        {
            "message_id": result.get("message_id"),
            "chat_id": chat.get("id"),
            "chat_type": chat.get("type"),
            "date": result.get("date"),
        },
        sort_keys=True,
    )


def _chat_id_from_update(update: dict[str, Any]) -> str | None:
    for key in ("message", "edited_message", "channel_post", "edited_channel_post"):
        msg = update.get(key)
        if isinstance(msg, dict):
            chat = msg.get("chat")
            if isinstance(chat, dict) and chat.get("id") is not None:
                return str(chat["id"])
    for key in ("my_chat_member", "chat_member", "chat_join_request"):
        item = update.get(key)
        if isinstance(item, dict):
            chat = item.get("chat")
            if isinstance(chat, dict) and chat.get("id") is not None:
                return str(chat["id"])
    callback = update.get("callback_query")
    if isinstance(callback, dict):
        msg = callback.get("message")
        if isinstance(msg, dict):
            chat = msg.get("chat")
            if isinstance(chat, dict) and chat.get("id") is not None:
                return str(chat["id"])
    return None


def _compact_update(update: dict[str, Any]) -> dict[str, Any]:
    compact: dict[str, Any] = {"update_id": update.get("update_id")}
    for key in ("message", "edited_message", "channel_post", "edited_channel_post"):
        msg = update.get(key)
        if not isinstance(msg, dict):
            continue
        chat = msg.get("chat") if isinstance(msg.get("chat"), dict) else {}
        sender = msg.get("from") if isinstance(msg.get("from"), dict) else {}
        compact.update(
            {
                "kind": key,
                "message_id": msg.get("message_id"),
                "date": msg.get("date"),
                "chat_id": chat.get("id"),
                "chat_type": chat.get("type"),
                "from_username": sender.get("username"),
                "text": msg.get("text") or msg.get("caption"),
            }
        )
        return compact

    for key in ("my_chat_member", "chat_member", "chat_join_request"):
        item = update.get(key)
        if not isinstance(item, dict):
            continue
        chat = item.get("chat") if isinstance(item.get("chat"), dict) else {}
        sender = item.get("from") if isinstance(item.get("from"), dict) else {}
        compact.update(
            {
                "kind": key,
                "chat_id": chat.get("id"),
                "chat_type": chat.get("type"),
                "from_username": sender.get("username"),
            }
        )
        return compact

    callback = update.get("callback_query")
    if isinstance(callback, dict):
        compact.update(
            {
                "kind": "callback_query",
                "callback_query_id": callback.get("id"),
                "from_username": (callback.get("from") or {}).get("username")
                if isinstance(callback.get("from"), dict)
                else None,
                "data": callback.get("data"),
            }
        )
    return compact


mcp = FastMCP(
    "thclaws-telegram",
    instructions=(
        "Provides Telegram Bot API tools for agent-initiated communication. "
        "Use these tools for notifications, sending artifacts, and reading "
        "recent bot updates. This is not a Telegram UI transport for thClaws."
    ),
)


@mcp.tool()
async def telegram_send_message(
    chat_id: str,
    text: str,
    parse_mode: str | None = None,
) -> str:
    """Send a text message to an allowlisted Telegram chat.

    Args:
        chat_id: Telegram chat ID. Must be listed in TELEGRAM_ALLOWED_CHAT_IDS.
        text: Message body to send.
        parse_mode: Optional Telegram parse mode, e.g. "MarkdownV2" or "HTML".
    """
    allowed_chat_id = _check_chat_allowed(chat_id)
    payload: dict[str, Any] = {
        "chat_id": allowed_chat_id,
        "text": _validate_message_text(text),
    }
    validated_parse_mode = _validate_parse_mode(parse_mode)
    if validated_parse_mode:
        payload["parse_mode"] = validated_parse_mode
    result = await _post_json("sendMessage", payload)
    if not isinstance(result, dict):
        raise TelegramApiError("sendMessage: result was not an object")
    return f"Telegram message sent: {_message_summary(result)}"


@mcp.tool()
async def telegram_send_photo(
    chat_id: str,
    file_path: str,
    caption: str | None = None,
) -> str:
    """Send a local image file to an allowlisted Telegram chat.

    Args:
        chat_id: Telegram chat ID. Must be listed in TELEGRAM_ALLOWED_CHAT_IDS.
        file_path: Local path to the image file. URLs are intentionally not supported.
        caption: Optional caption.
    """
    allowed_chat_id = _check_chat_allowed(chat_id)
    result = await _post_file(
        "sendPhoto",
        "photo",
        allowed_chat_id,
        file_path,
        caption,
        MAX_PHOTO_BYTES,
    )
    if not isinstance(result, dict):
        raise TelegramApiError("sendPhoto: result was not an object")
    return f"Telegram photo sent: {_message_summary(result)}"


@mcp.tool()
async def telegram_send_document(
    chat_id: str,
    file_path: str,
    caption: str | None = None,
) -> str:
    """Send a local document file to an allowlisted Telegram chat.

    Args:
        chat_id: Telegram chat ID. Must be listed in TELEGRAM_ALLOWED_CHAT_IDS.
        file_path: Local path to the document file. URLs are intentionally not supported.
        caption: Optional caption.
    """
    allowed_chat_id = _check_chat_allowed(chat_id)
    result = await _post_file(
        "sendDocument",
        "document",
        allowed_chat_id,
        file_path,
        caption,
        MAX_DOCUMENT_BYTES,
    )
    if not isinstance(result, dict):
        raise TelegramApiError("sendDocument: result was not an object")
    return f"Telegram document sent: {_message_summary(result)}"


@mcp.tool()
async def telegram_get_updates(limit: int = 10, offset: int | None = None) -> str:
    """Read recent Telegram bot updates for allowlisted chats.

    Args:
        limit: Number of updates to request, clamped to Telegram's 1-100 range.
        offset: Optional Telegram update offset for pagination.
    """
    allowed = _allowed_chat_ids()
    requested_limit = max(1, min(int(limit), 100))
    payload: dict[str, Any] = {"limit": requested_limit, "timeout": 0}
    if offset is not None:
        payload["offset"] = int(offset)

    updates = await _post_json("getUpdates", payload)
    if not isinstance(updates, list):
        updates = []

    compact = [
        _compact_update(update)
        for update in updates
        if isinstance(update, dict)
        and (chat_id := _chat_id_from_update(update)) is not None
        and chat_id in allowed
    ]
    if not compact:
        return "No updates for allowlisted Telegram chats."
    return json.dumps(compact, ensure_ascii=False, sort_keys=True)


def main() -> None:
    """Entry point for the `thclaws-telegram` console script."""
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport == "sse":
        port = int(os.environ.get("MCP_PORT", "8000"))
        mcp.settings.host = os.environ.get("MCP_HOST", "127.0.0.1")
        mcp.settings.port = port
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
