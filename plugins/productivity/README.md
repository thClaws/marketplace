# Productivity Plugin (thClaws)

Task management, workplace memory, and a visual dashboard. thClaws learns your people, projects, and terminology so it can act like a colleague, not a chatbot.

> **Forked from [anthropics/knowledge-work-plugins/productivity](https://github.com/anthropics/knowledge-work-plugins/tree/main/productivity)** (Apache-2.0). The original was designed for Anthropic's Cowork product and shipped pre-configured with 10 hosted MCP servers. This thClaws fork ships with **no MCP servers** by default — install the connectors you actually need via `/mcp install` from the marketplace, or `/mcp add` with your own URLs. See `NOTICE.md` for the full modification list.

## Installation

```
/plugin install productivity
```

(Once added to the thClaws marketplace catalog. For now, install directly via git URL: `/plugin install https://github.com/thClaws/marketplace.git#main:plugins/productivity`)

## What it does

This plugin gives thClaws a persistent understanding of your work:

- **Task management** — A markdown task list (`TASKS.md`) thClaws reads, writes, and executes against. Add tasks naturally; thClaws tracks status, triages stale items, and syncs with external tools (when you've installed the matching MCP connector).
- **Workplace memory** — A two-tier memory system that teaches thClaws your shorthand, people, projects, and terminology. Say "ask todd to do the PSR for oracle" and thClaws knows exactly who, what, and which deal.
- **Visual dashboard** — A local HTML file with a board view of your tasks and a live view of thClaws's workplace knowledge. Edit from the board or the file — they stay in sync.

## Commands

| Command | What it does |
|---------|--------------|
| `/start` | Initialize tasks + memory, open the dashboard |
| `/update` | Triage stale items, check memory for gaps, sync from connected MCP tools |
| `/update --comprehensive` | Deep scan all connected sources — flag missed todos, suggest new memories |

## Skills

| Skill | Description |
|-------|-------------|
| `task-management` | Markdown-based task tracking using a shared TASKS.md file |
| `memory-management` | Two-tier memory: AGENTS.md for working memory, memory/ directory for deep storage |

## Adding connectors

The plugin works connector-agnostically using `~~placeholder` references in its workflow files (see [CONNECTORS.md](CONNECTORS.md)). Concrete MCP servers are wired separately so you only install what you actually use.

| Category | Placeholder | Suggested MCP servers |
|----------|-------------|-----------------------|
| Chat | `~~chat` | Slack, Microsoft Teams, Discord, Line |
| Email | `~~email` | Microsoft 365, Gmail |
| Calendar | `~~calendar` | Google Calendar, Microsoft 365 |
| Knowledge base | `~~knowledge base` | Notion, Confluence, Guru |
| Project tracker | `~~project tracker` | Asana, Linear, Jira, monday.com, ClickUp |

To add one:

```
/mcp marketplace            # browse what's curated
/mcp install <name>         # install a vetted entry
/mcp add <name> <url>       # or add a custom MCP URL directly
```

The plugin's skills will pick up whatever's in `mcp.json` automatically — no plugin reconfiguration needed.

## Example workflows

### Getting started

```
You: /start

thClaws: [creates TASKS.md, AGENTS.md, memory/ directory, and dashboard.html]
         [shows you the dashboard path]
         [asks about your role, team, and current priorities to seed memory]
```

### Adding tasks naturally

```
You: I need to review the budget proposal for Sarah by Friday,
     draft the Q2 roadmap after syncing with Greg, and follow up
     on the API spec from the Platform team

thClaws: [adds all three tasks to TASKS.md with context]
         [dashboard updates automatically]
```

### Morning sync (with connectors installed)

```
You: /update --comprehensive

thClaws: [scans connected email/calendar/chat for new action items]
         [flags: "Budget proposal review is due tomorrow — still open"]
         [suggests: "New person mentioned in 3 threads: Jamie Park,
          Design Lead — add to memory?"]
         [updates stale tasks and fills memory gaps]
```

### Workplace shorthand

Once memory is populated, thClaws decodes your shorthand instantly:

```
You: ask todd to do the PSR for oracle

thClaws: "Ask Todd Martinez (Finance lead) to prepare the Pipeline
          Status Report for the Oracle Systems deal ($2.3M, closing Q2)"
```

No clarifying questions. No round trips.

## License

Apache-2.0 — see [LICENSE](./LICENSE) (preserved from upstream). All Anthropic copyright notices intact. Modifications listed in [NOTICE.md](./NOTICE.md) per Apache 2.0 §4(b).
