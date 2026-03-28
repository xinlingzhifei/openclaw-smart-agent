# OpenClaw Runtime Auto-Start Design

**Goal:** Start the Smart Agent runtime automatically when the OpenClaw plugin loads during Gateway startup, while keeping the existing plugin-to-HTTP-runtime architecture.

## Context

Today the plugin only proxies tool calls to `http://127.0.0.1:8787`. Users still need to start `openclaw-smart-agent serve` manually, which breaks the "install once, use on startup" experience.

The feature should solve three practical problems:

1. Probe the runtime first so we do not launch duplicates.
2. Start the runtime only when it is missing and auto-start is enabled.
3. Stop only the child process that this plugin started, leaving user-managed runtimes alone.

## Chosen Approach

Use the official OpenClaw plugin background service API:

- register a `runtime-autostart` service only in `registrationMode === "full"`
- on service start, probe the runtime base URL
- if unreachable and auto-start is enabled, spawn `openclaw-smart-agent serve --config <path>`
- poll the runtime until it responds or startup times out
- remember whether the runtime was plugin-owned
- on service stop, terminate only the owned child process

## Configuration

Add two plugin config options:

- `autoStartRuntime: boolean` with a default of `true`
- `runtimeConfigPath: string` optional override for the runtime config file

Config path resolution order:

1. explicit `runtimeConfigPath`
2. repository-local `../config/config.yaml` if it exists
3. plugin state fallback `stateDir/config.yaml`

The runtime base URL continues to come from `OPENCLAW_SMART_AGENT_BASE_URL`, with `http://127.0.0.1:8787` as the default.

## Runtime Semantics

- If the runtime is already reachable, do nothing and do not claim ownership.
- If auto-start is disabled, do nothing and log that startup was skipped.
- If spawning succeeds and the probe later passes, mark the runtime as owned by the plugin.
- If startup never becomes reachable, log the failure and clean up the spawned process.

This is intentionally a minimal lifecycle manager, not a full supervisor.

## Testing

Add focused plugin tests for:

1. config path resolution
2. skip-spawn behavior when the runtime is already reachable
3. spawn-and-cleanup behavior when the runtime must be started
4. disabled auto-start behavior

## Non-Goals

- No restart loop for crashed runtimes after startup
- No multi-instance coordination
- No automatic port reassignment
- No embedded Python runtime inside the plugin
