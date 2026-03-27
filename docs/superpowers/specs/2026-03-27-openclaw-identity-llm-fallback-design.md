# OpenClaw Identity LLM Fallback Design

**Goal:** When an identity string does not match any local YAML template, generate a structured agent profile through OpenClaw's own model stack instead of falling back immediately to the generic profile.

## Context

The current runtime resolves identities in two stages:

1. Match a YAML template from `src/openclaw_smart_agent/templates/`
2. If no template matches, return the default `generalist` profile

This is reliable, but it leaves long-tail identities underpowered. The repository already exposes a clean enhancement seam in `IdentityEnhancer`, so the missing piece is a concrete provider for unmatched-template generation.

## Chosen Approach

Use OpenClaw Gateway's HTTP `POST /tools/invoke` endpoint to call the optional `llm-task` tool. `llm-task` is JSON-only, supports JSON Schema validation, and runs through OpenClaw's configured provider/model/auth profile stack.

The runtime will:

1. Try the local YAML templates first
2. If no template matches and the feature is enabled, call OpenClaw `llm-task`
3. Validate and normalize the returned profile fields
4. Fall back to the existing default profile if the gateway call fails or returns unusable data

## Boundaries

- The Python runtime remains the single source of truth for registration and persistence
- OpenClaw is used only for profile generation, not for task routing or registry writes
- The new path is optional and disabled unless explicitly configured
- Failures in OpenClaw generation must never prevent agent creation

## Configuration

Add a new `identity` config section with:

- `fallback_strategy`: `defaults` or `openclaw_llm`
- `openclaw_gateway_url`
- `gateway_bearer_token`
- `session_key`
- `thinking`
- `provider`
- `model`
- `auth_profile_id`
- `timeout_ms`
- `max_tokens`

Environment-variable defaults are acceptable for gateway auth secrets.

## Data Flow

1. `POST /api/v1/agents/create` receives `identity`
2. `SmartAgentRuntime.create_agent()` asks `IdentityEnhancer.enhance()`
3. `IdentityEnhancer` checks YAML templates
4. If unmatched and `fallback_strategy == "openclaw_llm"`, call a new OpenClaw client
5. The client invokes `llm-task` with a strict schema for:
   - `role`
   - `skills`
   - `tools`
   - `system_prompt`
   - `resource_weight`
6. The enhancer sanitizes the output and returns an `AgentProfile`
7. Registration continues unchanged

## Error Handling

- Gateway request failure: log/ignore and use defaults
- Missing auth configuration: skip LLM fallback and use defaults
- Invalid schema output: skip LLM fallback and use defaults
- Partial output: normalize lists/strings, clamp `resource_weight`, then continue

## Testing

- Identity unit test for unmatched-template OpenClaw fallback
- Identity unit test for failed gateway fallback returning defaults
- Config test for new identity settings
- API regression test proving create-agent returns LLM-generated profile when configured

## Documentation

Update:

- `README.md`
- `docs/openclaw-integration.md`
- `skills/openclaw-smart-agent/SKILL.md`
- `skills/openclaw-smart-agent/references/api.md`
- `config/config.example.yaml`

Document that `llm-task` must be enabled and allowlisted in OpenClaw for the fallback to work.
