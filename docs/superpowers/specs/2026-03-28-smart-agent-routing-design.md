# Smart Agent Routing Enhancement Design

**Goal:** Make task allocation match the advertised behavior more closely by incorporating real skill match ratios, current load, and task priority into dispatch decisions.

## Context

The current router has three problems:

1. Skill matching is effectively binary because candidates are filtered to full matches before scoring.
2. Task priority only adds a small agent-specific bias instead of changing dispatch behavior.
3. Tests do not prove how the router behaves when multiple agents compete.

## Chosen Approach

Upgrade the routing path in three targeted ways:

1. Allow partially matching agents into the candidate pool, as long as they share at least one required skill.
2. Dispatch pending tasks in priority order (`priority desc`, then `created_at asc`) instead of routing only the newly created task in isolation.
3. Treat low-priority and high-priority tasks differently:
   - low-priority tasks only consider `HEALTHY` agents
   - high-priority tasks may consider both `HEALTHY` and `BUSY` agents

This keeps the system simple while making priority materially affect allocation behavior.

## Routing Semantics

### Skill matching

- If a task has required skills, agents need at least one overlapping skill to be considered.
- Skill overlap contributes a real ratio score:
  - `1.0` for full match
  - `0.66`, `0.33`, etc. for partial match
- This means partial matches can still win when no full match exists.

### Load

Load still comes from:

- `running_tasks`
- `cpu_percent`
- `memory_percent`

Lower load improves score.

### Priority

Priority affects routing in two places:

1. Dispatch order across pending tasks
2. Candidate eligibility and weight balance during scoring

For high-priority tasks, capability matters more and busy agents remain eligible. For lower-priority tasks, the router prefers idle agents and leaves already-busy agents for urgent work.

## Registry Changes

Add registry helpers to support the new routing flow:

- list dispatchable tasks in priority order
- find candidate agents for a task under an allowed-status set

The store schema does not need to change.

## Testing

Add explicit tests for:

1. Partial skill match ranking
2. Low-load preference when skills are equal
3. Priority-ordered dispatch where a high-priority task claims a scarce healthy agent before a low-priority task

## Non-Goals

- No full scheduler loop
- No task preemption
- No distributed queueing
- No per-agent capacity model beyond `HEALTHY` vs `BUSY`
