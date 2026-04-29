---
name: start
description: Initialize the productivity system and open the dashboard. Use when setting up the plugin for the first time, bootstrapping working memory from your existing task list, or decoding the shorthand (nicknames, acronyms, project codenames) you use in your todos.
---

# Start Command

> If you see unfamiliar placeholders or need to check which tools are connected, see [CONNECTORS.md](../../CONNECTORS.md).

Initialize the task and memory systems, then open the unified dashboard.

## Instructions

### 1. Check What Exists

Check the working directory for:
- `TASKS.md` — task list
- `AGENTS.md` — working memory (thClaws also reads this; see note below)
- `memory/` — deep memory directory
- `dashboard.html` — the visual UI

> **Note for thClaws users:** thClaws already loads `AGENTS.md` from the
> project root automatically as part of its built-in context, and has its
> own auto-memory system at `~/.config/thclaws/memory/` for cross-project
> facts (see ch08 of the user manual). This skill's `AGENTS.md` and
> `memory/` files live in the **project working directory** — they
> coexist with thClaws's user-level auto-memory, not replace it.
> Project-level facts live here; cross-project facts live in
> `~/.config/thclaws/memory/`.

### 2. Create What's Missing

Run these as concrete Bash commands — the SKILL.md text alone is insufficient guidance for the model; the actual file operations are what creates the system. Use the Bash tool, do not improvise.

**Step A — Copy the dashboard** (idempotent):

```bash
cp -f "{skill_dir}/../dashboard.html" ./dashboard.html
```

(`-f` overwrites because the dashboard's snapshot block needs a fresh template each time — user customizations don't belong in dashboard.html anyway, only in TASKS.md / AGENTS.md.)

**Step B — Create TASKS.md if missing.** Use the Write tool with **exactly** this template, byte-for-byte. Do **not** add example tasks, welcome messages, "your first task here" placeholders, or instructional comments. The user adds their own tasks; an empty section means an empty section.

```markdown
# Tasks

## Active

## Waiting On

## Someday

## Done
```

That's the entire file content — four headers under `# Tasks` with blank space between them. No other text. If TASKS.md already exists, do **not** overwrite — read what's there and proceed.

**Step C — Inline TASKS.md content into the dashboard so it auto-loads with zero clicks.** Run this single-line command:

```bash
python3 "{skill_dir}/../../scripts/regen_dashboard.py"
```

This is what makes the dashboard render the board on first open without any file picker.

**If `AGENTS.md` and `memory/` don't exist:** this is a fresh setup — after the dashboard steps, begin the memory bootstrap workflow (see below). Both files/dirs go in the current working directory.

### 3. Open the Dashboard

Tell the user where to find it: "Dashboard is ready at `dashboard.html` in your project root. Open it from your file browser to get started."

Do NOT try to spawn `open` / `xdg-open` / `start` from a subprocess — the agent may not have access to the user's actual desktop session (sandboxed environments, remote sessions, headless servers). Letting the user open it themselves is more portable.

### 4. Orient the User

If everything was already initialized:
```
Dashboard ready. Your tasks and memory are both loaded.
- /update to sync tasks and check memory
- /update --comprehensive for a deep scan of all activity
```

If memory hasn't been bootstrapped yet, continue to step 5.

### 5. Bootstrap Memory (First Run Only)

Only do this if `AGENTS.md` and `memory/` don't exist yet.

The best source of workplace language is the user's actual task list. Real tasks = real shorthand.

**Source-of-tasks detection.** Default to the project's `TASKS.md` — thClaws is folder-based and the user already pointed at this directory by running `/start` here, so they implicitly chose this as the working context. Don't ask "where do you keep your tasks?" if `TASKS.md` exists in the cwd; just read it and proceed.

```text
Pseudocode:
- If `TASKS.md` exists in cwd  → use it as the source, skip the question.
- Else if a known external MCP is installed (Asana, Linear, etc.)
                                  → ask the user which one to scan.
- Else                            → ask once: "Should I scan an external
                                    task source (Asana / Linear / Notion)
                                    via /mcp install, or start fresh
                                    with an empty memory and let it grow
                                    from conversation?"
```

Use `AskUserQuestion` only in the second/third branch — never in the first. When you do ask, keep the prompt to one line; multi-line text in the tool label garbles the terminal.

**Once you have the task source:**

For each task item, analyze it for potential shorthand:
- Names that might be nicknames
- Acronyms or abbreviations
- Project references or codenames
- Internal terms or jargon

**For each item, decode it interactively:**

```
Task: "Send PSR to Todd re: Phoenix blockers"

I see some terms I want to make sure I understand:

1. **PSR** - What does this stand for?
2. **Todd** - Who is Todd? (full name, role)
3. **Phoenix** - Is this a project codename? What's it about?
```

Continue through each task, asking only about terms you haven't already decoded.

### 6. Comprehensive Scan (deferred to `/update --comprehensive`)

Don't offer a comprehensive scan during `/start`. The canonical place
for that flow is `/update --comprehensive`, which scans every available
MCP source and proposes new memories. Offering both here and in
`/update` confuses the boundary between "first-time setup" and "daily
refresh." Just mention it in the wrap-up message (step 8) and let the
user opt in when ready.

### 7. Write Memory Files

From everything gathered, create:

**AGENTS.md** (working memory, ~50-80 lines):
```markdown
# Memory

## Me
[Name], [Role] on [Team].

## People
| Who | Role |
|-----|------|
| **[Nickname]** | [Full Name], [role] |

## Terms
| Term | Meaning |
|------|---------|
| [acronym] | [expansion] |

## Projects
| Name | What |
|------|------|
| **[Codename]** | [description] |

## Preferences
- [preferences discovered]
```

**memory/** directory:
- `memory/glossary.md` — full decoder ring (acronyms, terms, nicknames, codenames)
- `memory/people/{name}.md` — individual profiles
- `memory/projects/{name}.md` — project details
- `memory/context/company.md` — teams, tools, processes

### 8. Report Results

```
Productivity system ready:
- Tasks: TASKS.md (X items)
- Memory: X people, X terms, X projects
- Dashboard: open dashboard.html in your browser

Use /update to keep things current (add --comprehensive for a deep scan).
```

## Notes

- If memory is already initialized, this just opens the dashboard
- Nicknames are critical — always capture how people are actually referred to
- If a source isn't available (no MCP installed for that category), skip it and note the gap
- Memory grows organically through natural conversation after bootstrap
