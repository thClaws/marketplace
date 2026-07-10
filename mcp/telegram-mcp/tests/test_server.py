"""Offline tests for thclaws-telegram MCP.

The tests patch httpx so they never call the real Telegram Bot API.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from telegram_mcp.server import (
    TelegramApiError,
    TelegramConfigError,
    _allowed_file_roots,
    _api_url,
    _chat_id_from_update,
    _check_chat_allowed,
    _compact_update,
    _open_allowed_file,
    _telegram_response,
    _telegram_result,
    main,
    telegram_get_updates,
    telegram_send_document,
    telegram_send_message,
    telegram_send_photo,
)


@pytest.fixture(autouse=True)
def telegram_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "123,-456")


def _fake_response(data: dict) -> AsyncMock:
    response = AsyncMock()
    response.raise_for_status = lambda: None
    response.json = lambda: data
    return response


def test_missing_bot_token_fails_clearly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN")
    with pytest.raises(TelegramConfigError, match="TELEGRAM_BOT_TOKEN"):
        _api_url("sendMessage")


def test_allowed_chat_id_passes() -> None:
    assert _check_chat_allowed("123") == "123"
    assert _check_chat_allowed(-456) == "-456"


def test_disallowed_chat_id_fails() -> None:
    with pytest.raises(TelegramConfigError, match="not allowed"):
        _check_chat_allowed("999")


def test_missing_allowlist_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TELEGRAM_ALLOWED_CHAT_IDS")
    with pytest.raises(TelegramConfigError, match="TELEGRAM_ALLOWED_CHAT_IDS"):
        _check_chat_allowed("123")


def test_allowed_file_roots_cache_tracks_env_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()

    monkeypatch.setenv("TELEGRAM_ALLOWED_FILE_ROOTS", str(first))
    assert _allowed_file_roots() == (first.resolve(),)
    # Same env value returns the cached tuple.
    assert _allowed_file_roots() == (first.resolve(),)

    monkeypatch.setenv("TELEGRAM_ALLOWED_FILE_ROOTS", str(second))
    assert _allowed_file_roots() == (second.resolve(),)


@pytest.mark.asyncio
async def test_send_message_builds_telegram_request() -> None:
    fake_post = AsyncMock(
        return_value=_fake_response(
            {
                "ok": True,
                "result": {
                    "message_id": 42,
                    "date": 1710000000,
                    "chat": {"id": 123, "type": "private"},
                },
            }
        )
    )

    with patch("telegram_mcp.server.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = fake_post
        out = await telegram_send_message("123", "hello", parse_mode="HTML")

    assert "Telegram message sent" in out
    assert '"message_id": 42' in out
    fake_post.assert_awaited_once()
    _, kwargs = fake_post.await_args
    assert kwargs["json"] == {
        "chat_id": "123",
        "text": "hello",
        "parse_mode": "HTML",
    }
    assert kwargs["timeout"] == 20.0


@pytest.mark.asyncio
async def test_telegram_http_error_body_is_preserved() -> None:
    request = httpx.Request("POST", "https://api.telegram.org/bottest/sendMessage")
    response = httpx.Response(
        400,
        json={"ok": False, "error_code": 400, "description": "chat not found"},
        request=request,
    )

    with pytest.raises(TelegramApiError, match="chat not found"):
        await _telegram_response(response, "sendMessage")


@pytest.mark.asyncio
async def test_get_updates_filters_to_allowed_chats() -> None:
    fake_post = AsyncMock(
        return_value=_fake_response(
            {
                "ok": True,
                "result": [
                    {
                        "update_id": 1,
                        "message": {
                            "message_id": 10,
                            "date": 1710000000,
                            "chat": {"id": 123, "type": "private"},
                            "from": {"username": "allowed"},
                            "text": "ping",
                        },
                    },
                    {
                        "update_id": 2,
                        "message": {
                            "message_id": 11,
                            "date": 1710000001,
                            "chat": {"id": 999, "type": "private"},
                            "from": {"username": "blocked"},
                            "text": "secret",
                        },
                    },
                ],
            }
        )
    )

    with patch("telegram_mcp.server.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = fake_post
        out = await telegram_get_updates(limit=200, offset=3)

    data = json.loads(out)
    assert len(data) == 1
    assert data[0]["chat_id"] == 123
    assert data[0]["text"] == "ping"
    _, kwargs = fake_post.await_args
    assert kwargs["json"] == {"limit": 100, "timeout": 0, "offset": 3}


@pytest.mark.asyncio
async def test_get_updates_webhook_conflict_has_hint() -> None:
    request = httpx.Request("POST", "https://api.telegram.org/bottest/getUpdates")
    response = httpx.Response(
        409,
        json={
            "ok": False,
            "error_code": 409,
            "description": "Conflict: can't use getUpdates method while webhook is active",
        },
        request=request,
    )

    with pytest.raises(TelegramApiError, match="deleteWebhook"):
        await _telegram_response(response, "getUpdates")


@pytest.mark.asyncio
async def test_file_upload_rejects_missing_file() -> None:
    with pytest.raises(TelegramConfigError, match="does not exist"):
        await telegram_send_photo("123", "/tmp/not-a-real-telegram-file.png")


@pytest.mark.asyncio
async def test_file_upload_rejects_url() -> None:
    with pytest.raises(TelegramConfigError, match="local path"):
        await telegram_send_document("123", "https://example.com/report.pdf")


@pytest.mark.asyncio
async def test_file_upload_rejects_path_outside_allowed_roots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    allowed = tmp_path / "allowed"
    outside = tmp_path / "outside"
    allowed.mkdir()
    outside.mkdir()
    doc = outside / "secret.txt"
    doc.write_text("secret", encoding="utf-8")
    monkeypatch.setenv("TELEGRAM_ALLOWED_FILE_ROOTS", str(allowed))

    with pytest.raises(TelegramConfigError, match="outside TELEGRAM_ALLOWED_FILE_ROOTS"):
        await telegram_send_document("123", str(doc))


def test_open_allowed_file_uses_nofollow_when_available(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    doc = tmp_path / "report.txt"
    doc.write_text("hello", encoding="utf-8")
    monkeypatch.setenv("TELEGRAM_ALLOWED_FILE_ROOTS", str(tmp_path))
    real_open = os.open
    seen: dict[str, int] = {}

    def recording_open(path: Path, flags: int) -> int:
        seen["flags"] = flags
        return real_open(path, flags)

    with patch("telegram_mcp.server.os.open", side_effect=recording_open):
        _, handle = _open_allowed_file(str(doc), 100)
        handle.close()

    nofollow = getattr(os, "O_NOFOLLOW", 0)
    if nofollow:
        assert seen["flags"] & nofollow


@pytest.mark.asyncio
async def test_file_upload_rejects_oversized_document(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    doc = tmp_path / "report.txt"
    doc.write_text("hello", encoding="utf-8")
    monkeypatch.setenv("TELEGRAM_ALLOWED_FILE_ROOTS", str(tmp_path))
    monkeypatch.setattr("telegram_mcp.server.MAX_DOCUMENT_BYTES", 3)

    with pytest.raises(TelegramConfigError, match="too large"):
        await telegram_send_document("123", str(doc))


@pytest.mark.asyncio
async def test_send_document_uploads_local_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    doc = tmp_path / "report.txt"
    doc.write_text("hello", encoding="utf-8")
    monkeypatch.setenv("TELEGRAM_ALLOWED_FILE_ROOTS", str(tmp_path))
    fake_post = AsyncMock(
        return_value=_fake_response(
            {
                "ok": True,
                "result": {
                    "message_id": 77,
                    "date": 1710000000,
                    "chat": {"id": 123, "type": "private"},
                },
            }
        )
    )

    with patch("telegram_mcp.server.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = fake_post
        out = await telegram_send_document("123", str(doc), caption="report")

    assert "Telegram document sent" in out
    _, kwargs = fake_post.await_args
    assert kwargs["data"] == {"chat_id": "123", "caption": "report"}
    assert "document" in kwargs["files"]


@pytest.mark.asyncio
async def test_send_message_rejects_invalid_parse_mode() -> None:
    with pytest.raises(TelegramConfigError, match="parse_mode"):
        await telegram_send_message("123", "hello", parse_mode="NotAMode")


@pytest.mark.asyncio
async def test_send_message_rejects_too_long_text() -> None:
    with pytest.raises(TelegramConfigError, match="4096"):
        await telegram_send_message("123", "x" * 4097)


def test_telegram_api_error_surfaces() -> None:
    with pytest.raises(TelegramApiError, match=r"\[400\] Bad Request"):
        _telegram_result(
            {"ok": False, "error_code": 400, "description": "Bad Request"},
            "sendMessage",
        )


def test_update_chat_id_supports_membership_updates() -> None:
    update = {
        "update_id": 100,
        "chat_join_request": {
            "chat": {"id": -456, "type": "supergroup"},
            "from": {"username": "reviewer"},
        },
    }

    assert _chat_id_from_update(update) == "-456"
    compact = _compact_update(update)
    assert compact["kind"] == "chat_join_request"
    assert compact["chat_id"] == -456


def test_compact_update_callback_query_branch() -> None:
    compact = _compact_update(
        {
            "update_id": 101,
            "callback_query": {
                "id": "cb-1",
                "from": {"username": "alice"},
                "data": "approve",
            },
        }
    )

    assert compact["kind"] == "callback_query"
    assert compact["callback_query_id"] == "cb-1"
    assert compact["data"] == "approve"


def test_sse_transport_binds_localhost_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_TRANSPORT", "sse")
    monkeypatch.delenv("MCP_HOST", raising=False)

    with patch("telegram_mcp.server.mcp.run") as run:
        main()

    run.assert_called_once_with(transport="sse")
    from telegram_mcp.server import mcp

    assert mcp.settings.host == "127.0.0.1"
