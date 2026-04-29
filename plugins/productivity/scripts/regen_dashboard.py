#!/usr/bin/env python3
"""Regenerate the inlined TASKS.md snapshot in dashboard.html.

The dashboard renders the board from a snapshot inlined into
dashboard.html (browser security forbids file:// HTML from reading
sibling files without a user gesture). This script keeps that snapshot
in sync with the canonical TASKS.md after the agent mutates it.

Why a script file rather than an inline Bash heredoc in SKILL.md:
agents sometimes mangle multi-line shell commands (newlines collapse,
heredoc body gets escaped) at the tool boundary. A single-file invocation
(`python3 path/to/regen_dashboard.py`) is one line in the SKILL.md, no
escaping pitfalls.

Idempotent: if dashboard.html doesn't exist (user hasn't run /start),
or if the snapshot already matches TASKS.md, the script silently no-ops.
"""

from __future__ import annotations

import pathlib
import re
import sys


SNAPSHOT_RE = re.compile(
    r"<!--\s*thclaws-tasks-begin\s*-->[\s\S]*?<!--\s*thclaws-tasks-end\s*-->"
)


def main() -> int:
    cwd = pathlib.Path.cwd()
    dashboard = cwd / "dashboard.html"
    tasks = cwd / "TASKS.md"

    if not dashboard.exists():
        # User hasn't run /start yet — nothing to regenerate.
        return 0
    if not tasks.exists():
        # Tasks file was deleted — leave the dashboard's existing
        # snapshot alone rather than blanking it.
        print(
            f"regen_dashboard: TASKS.md not found at {tasks}; nothing to inject",
            file=sys.stderr,
        )
        return 0

    html = dashboard.read_text(encoding="utf-8")
    content = tasks.read_text(encoding="utf-8")

    if not SNAPSHOT_RE.search(html):
        print(
            "regen_dashboard: no <!-- thclaws-tasks-begin/end --> markers in "
            f"{dashboard} — refusing to mutate (likely an old dashboard "
            "template; reinstall the productivity plugin to refresh)",
            file=sys.stderr,
        )
        return 1

    new = SNAPSHOT_RE.sub(
        f"<!-- thclaws-tasks-begin -->\n{content}\n<!-- thclaws-tasks-end -->",
        html,
        count=1,
    )

    if new == html:
        # Already in sync — no write needed.
        return 0

    dashboard.write_text(new, encoding="utf-8")
    line_count = content.count("\n") + 1
    print(
        f"regen_dashboard: snapshot refreshed ({line_count} TASKS.md lines)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
