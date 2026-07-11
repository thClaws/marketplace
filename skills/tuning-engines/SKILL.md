---
name: tuning-engines
description: Use Tuning Engines for governed AI inference, MCP/agent/skill access, runtime traces, approvals, request capture, and fine-tuning loops.
short_description: Governed inference, traces, approvals, and fine-tuning loops.
---

# Tuning Engines

Use this skill when a coding-agent or workflow needs a governed AI control layer
around model calls, MCP tools, agent delegation, skills, traces, approvals, cost
tracking, request capture, or fine-tuning loops.

Tuning Engines provides:

- OpenAI-compatible governed inference at `https://api.tuningengines.com/v1`
- MCP, agent, and skill registry access scoped by tenant roles
- runtime traces for model, MCP, skill, agent, approval, and state events
- governance policies, guardrails, and approval workflows
- request capture and feedback loops for evals and fine-tuning

## MCP Setup

```json
{
  "mcpServers": {
    "tuning-engines": {
      "command": "npx",
      "args": ["-y", "tuningengines-cli", "mcp", "serve"],
      "env": {
        "TE_API_KEY": "te_...",
        "TE_API_URL": "https://app.tuningengines.com"
      }
    }
  }
}
```

Registry write tools are disabled by default. Start the MCP server with
`--enable-registry-writes` only when the user explicitly wants the agent to
create or update registry resources.

## Governed Inference

Use a Tuning Engines inference key with any OpenAI-compatible client:

```bash
export OPENAI_API_KEY="sk-te-..."
export OPENAI_BASE_URL="https://api.tuningengines.com/v1"
```

## Trace Events

For agent observability, include `run_id` and `request_id` on model, MCP, skill,
agent, approval, and outcome events. Tuning Engines links these into trace
timelines and usage analytics.
