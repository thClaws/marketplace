# NOTICE

This plugin is a derivative work of the `productivity` plugin from
[anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins/tree/main/productivity),
licensed under the Apache License 2.0.

Original copyright © Anthropic, PBC. All rights reserved by the original
authors except where modified below.

## Modifications by ThaiGPT Co., Ltd. (the thClaws project)

The following changes were made when redistributing this plugin via the
thClaws marketplace at `github.com/thClaws/marketplace`:

1. **`.claude-plugin/plugin.json`** — `name` unchanged (`productivity`),
   `version` reset to `0.1.0` (this is a thClaws-specific lineage),
   `author.name` set to "ThaiGPT Co., Ltd. (thClaws project)",
   description rewritten to mention the MCP-decoupling.

2. **`.mcp.json`** — emptied. The original shipped with 10 pre-configured
   MCP servers pointing at Anthropic-hosted endpoints
   (`mcp.slack.com/mcp`, `mcp.notion.com/mcp`, etc.) which are
   Cowork-specific services and not appropriate for non-Anthropic
   accounts. This fork lets the user install whichever MCP servers
   they actually use via `/mcp install` (from the thClaws marketplace)
   or `/mcp add <name> <url>` (custom URLs). The `~~placeholder`
   abstraction in `CONNECTORS.md` is preserved unchanged so the skills
   stay tool-agnostic.

3. **`README.md`** — rewritten throughout: replaces "Claude / Cowork"
   product references with "thClaws", updates the install command,
   updates the MCP-server discussion to reflect the empty `.mcp.json`
   and the `/mcp install` / `/mcp add` discovery path. Plugin's
   functional description (task management + memory + dashboard) is
   unchanged.

4. **`skills/start/SKILL.md`** —
   - replaced the Cowork-specific "shell open commands won't reach the
     user's browser" guidance with a more general "tell the user the
     file path to open" instruction (works in any environment, not
     just sandboxed VMs).
   - changed the path placeholder `${CLAUDE_PLUGIN_ROOT}/skills/dashboard.html`
     to `{skill_dir}/../dashboard.html` (thClaws's skill placeholder
     convention).
   - replaced `/productivity:update` with `/update` (consistent with
     thClaws's flat slash-command exposure).
   - added a "Note for thClaws users" callout explaining how this
     plugin's project-scope `CLAUDE.md` and `memory/` coexist with
     thClaws's user-scope auto-memory at `~/.config/thclaws/memory/`,
     so users don't get confused about which memory store wins.
   - softened the "scan all sources" guidance to skip categories where
     no MCP is installed (since we no longer ship pre-configured MCPs).

5. **`skills/task-management/SKILL.md`** — replaced
   `${CLAUDE_PLUGIN_ROOT}/skills/dashboard.html` with
   `{skill_dir}/../dashboard.html` and `/productivity:start` with
   `/start`. No other changes.

6. **`skills/update/SKILL.md`** — replaced `/productivity:update` with
   `/update` and `/productivity:start` with `/start`. No other changes.

7. **`skills/memory-management/SKILL.md`** — replaced
   `/productivity:start` with `/start`. No other changes.

8. **`skills/dashboard.html`** — visual rebrand only:
   - `<title>` and header `<h1>` changed from "Productivity" to
     "thClaws Productivity"
   - accent color (`--accent` CSS var, favicon SVG, header logo SVG)
     changed from Anthropic coral `#D97757` to thClaws teal-green
     `#3ecf8e` and hover variant from `#c4684a` to `#2a9d6a`
   - layout, JavaScript, and DOM structure unchanged

9. **Working-memory file renamed `CLAUDE.md` → `AGENTS.md`** — across
   `start/SKILL.md`, `update/SKILL.md`, `memory-management/SKILL.md`,
   `dashboard.html`, and `README.md`. Reason: `AGENTS.md` is the
   neutral, agent-tool-agnostic name (also recognized by thClaws's
   built-in context loader, alongside `CLAUDE.md`). Internal JS
   variable names in `dashboard.html` (`claudeMd`, `claudeFileHandle`)
   are kept as-is to avoid bulk-rename typos — they're identifiers,
   not user-visible strings, and renaming would touch 10+ unrelated
   lines.

10. **Inlined snapshot for zero-click dashboard view** — added a
    `<script id="thclaws-tasks-snapshot">` block in `dashboard.html`
    plus a `tryInlinedSnapshot()` boot path. `start/SKILL.md` and
    `update/SKILL.md` regenerate the snapshot from current `TASKS.md`
    via a Python one-liner (Bash heredoc form). Lets users open
    `dashboard.html` and see the board immediately without picking a
    file. Live read-write back to `TASKS.md` still uses the original
    File System Access API picker (one click per browser session,
    persisted via IndexedDB after first pick). Browser security
    forbids `file://` HTML from reading sibling files without a user
    gesture, so inlining at write-time is the cleanest path to
    "no-click first view" without requiring a local HTTP server.

11. **`start/SKILL.md` Step B inlines the TASKS.md template** instead
    of saying "see the task-management skill" — agents were fabricating
    placeholder tasks ("Welcome to your new dashboard!", "Add your
    first task...") instead of following the canonical four-section
    template. Inlining the template byte-for-byte and adding an
    explicit "do not add example tasks or boilerplate" guard fixes the
    drift. Same pattern: agents follow what they can copy verbatim,
    not what they have to fetch from another file.

12. **`start/SKILL.md` Step 6 dropped the redundant comprehensive-scan
    offer** — that flow now lives only in `/update --comprehensive`.
    Offering it twice (once at /start, again in /update) confused the
    boundary between first-time setup and daily refresh.

13. **This `NOTICE.md`** — added per Apache 2.0 §4(b) "stating that you
    changed the files".

The original `LICENSE` (Apache License, Version 2.0) is preserved
unchanged. All Anthropic copyright notices in any source files are
preserved.

The `CONNECTORS.md` abstraction (using `~~category` placeholders so
skills work with any MCP in that category) was left intact — it's a
clean design that the thClaws fork benefits from directly.
