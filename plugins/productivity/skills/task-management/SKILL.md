---
name: task-management
description: Simple task management using a shared TASKS.md file. Reference this when the user asks about their tasks, wants to add/complete tasks, or needs help tracking commitments.
user-invocable: false
---

# Task Management

Tasks are tracked in a simple `TASKS.md` file that both you and the user can edit.

## File Location

**Always use `TASKS.md` in the current working directory.**

- If it exists, read/write to it
- If it doesn't exist, create it with the template below

## Dashboard Setup (First Run)

A visual dashboard is available for managing tasks and memory. **On first interaction with tasks:**

1. Check if `dashboard.html` exists in the current working directory
2. If not, run this Bash command to copy it (the `-n` flag is a no-op if it already exists):
   ```bash
   cp -n "{skill_dir}/../dashboard.html" ./dashboard.html
   ```
3. Inform the user: "I've added the dashboard. Run `/start` to set up the full system."

The task board:
- Reads and writes to the same `TASKS.md` file
- Auto-saves changes
- Watches for external changes (syncs when you edit via CLI)
- Supports drag-and-drop reordering of tasks and sections

## Format & Template

When creating a new TASKS.md, use this exact template (without example tasks):

```markdown
# Tasks

## Active

## Waiting On

## Someday

## Done
```

Task format:
- `- [ ] **Task title** - context, for whom, due date`
- Sub-bullets for additional details
- Completed: `- [x] ~~Task~~ (date)`

## ALWAYS regenerate the dashboard snapshot after writing TASKS.md

The dashboard renders from a snapshot inlined into `dashboard.html` —
it does **not** re-read `TASKS.md` on every browser open (browser
security forbids that from `file://`). So **every time you mutate
`TASKS.md` (add, complete, edit, reorder a task), immediately run this
Bash command** to refresh the snapshot — otherwise the user sees the
old state in the dashboard:

```bash
python3 - <<'PY'
import pathlib, re
dash = pathlib.Path('dashboard.html')
tasks = pathlib.Path('TASKS.md')
if not (dash.exists() and tasks.exists()):
    raise SystemExit(0)
html = dash.read_text()
content = tasks.read_text()
new = re.sub(
    r'<!--\s*thclaws-tasks-begin\s*-->[\s\S]*?<!--\s*thclaws-tasks-end\s*-->',
    f'<!-- thclaws-tasks-begin -->\n{content}\n<!-- thclaws-tasks-end -->',
    html,
    count=1,
)
if new != html:
    dash.write_text(new)
PY
```

This is idempotent and a no-op if `dashboard.html` doesn't exist
(user hasn't run `/start` yet) or if the snapshot already matches.

## How to Interact

**When user asks "what's on my plate" / "my tasks":**
- Read TASKS.md
- Summarize Active and Waiting On sections
- Highlight anything overdue or urgent
- *(Read-only — no snapshot regen needed)*

**When user says "add a task" / "remind me to":**
- Add to Active section with `- [ ] **Task**` format
- Include context if provided (who it's for, due date)
- **Run the snapshot-regen Bash command above.**

**When user says "done with X" / "finished X":**
- Find the task
- Change `[ ]` to `[x]`
- Add strikethrough: `~~task~~`
- Add completion date
- Move to Done section
- **Run the snapshot-regen Bash command above.**

**When user asks "what am I waiting on":**
- Read the Waiting On section
- Note how long each item has been waiting
- *(Read-only — no snapshot regen needed)*

## Conventions

- **Bold** the task title for scannability
- Include "for [person]" when it's a commitment to someone
- Include "due [date]" for deadlines
- Include "since [date]" for waiting items
- Sub-bullets for additional context
- Keep Done section for ~1 week, then clear old items

## Extracting Tasks

When summarizing meetings or conversations, offer to add extracted tasks:
- Commitments the user made ("I'll send that over")
- Action items assigned to them
- Follow-ups mentioned

Ask before adding - don't auto-add without confirmation.
