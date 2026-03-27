---
name: openclaw-smart-agent
description: Use when orchestrating multiple OpenClaw sub-agents on one machine, especially when the user wants to create agents from role descriptions, publish tasks by required skills, inspect agent health and load, or route work through the Smart Agent runtime.
---

# OpenClaw Smart Agent

## Overview

Use this skill to drive the Smart Agent runtime through OpenClaw tools instead of manually tracking which sub-agent should do what.

The workflow is:

1. Create or reuse an agent from a short identity description.
2. Publish a task with required skills.
3. Inspect registry status when routing, health, or load needs confirmation.

## Tool Map

| Tool | Use |
| --- | --- |
| `smart_agent_create` | Turn a short role description into a registered Smart Agent |
| `smart_agent_publish_task` | Submit a task and let the router pick the best worker |
| `smart_agent_status` | Inspect current agents, health state, and load snapshot |

## Operating Pattern

### Create an agent

Use `smart_agent_create` when the user gives you a role such as:

- `Python开发`
- `数据分析`
- `测试工程师`

Pass the shortest accurate identity string. Let the runtime expand it from templates.

### Publish work

Use `smart_agent_publish_task` when the user gives a task but does not name a worker explicitly. Include:

- a clear `task_desc`
- the `required_skills` list
- `priority` only when urgency matters

### Inspect state

Use `smart_agent_status` before retrying, when assignment looks wrong, or when the user asks why a task is blocked.

## Good Requests

- `Create a Python开发 agent and assign it a parser task.`
- `Route this analysis job to the best available worker.`
- `Show me which Smart Agents are healthy right now.`

## Common Mistakes

- Do not invent agent ids before creating or querying them.
- Do not manually choose a worker when routing by skills is enough.
- Do not skip `smart_agent_status` when the user asks for health or load details.

## References

For endpoint details and payload shapes, read [references/api.md](references/api.md).
