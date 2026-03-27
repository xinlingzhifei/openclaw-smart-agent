# OpenClaw Skill Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align the repository with its intended role as an OpenClaw skill by adding a real heartbeat input path, clarifying installation and integration, and documenting template extension.

**Architecture:** Keep the current skill + plugin + Python runtime layout, but treat the runtime as a support layer for the skill instead of a full agent supervisor. Add one minimal heartbeat ingestion API, thread it through runtime, store, and plugin, then tighten docs so the capability boundary matches what the code actually does.

**Tech Stack:** Python 3.14, FastAPI, SQLite, pytest, TypeScript, npm, GitHub Actions

---

### Task 1: Add heartbeat ingestion to the runtime and REST API

**Files:**
- Modify: `src/openclaw_smart_agent/models.py`
- Modify: `src/openclaw_smart_agent/store.py`
- Modify: `src/openclaw_smart_agent/registry.py`
- Modify: `src/openclaw_smart_agent/runtime.py`
- Modify: `src/openclaw_smart_agent/api.py`
- Test: `tests/test_api.py`
- Test: `tests/test_monitor.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_heartbeat_api_updates_agent_health_snapshot(tmp_path):
    response = client.post(
        "/api/v1/agents/heartbeat",
        json={
            "agent_id": agent_id,
            "cpu_percent": 22.0,
            "memory_percent": 31.0,
            "consecutive_errors": 0,
            "current_task_id": None,
        },
    )
    assert response.status_code == 200
    assert response.json()["agent"]["last_heartbeat_at"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_api.py tests/test_monitor.py -q`
Expected: FAIL because heartbeat endpoint and persisted heartbeat fields do not exist yet

- [ ] **Step 3: Write minimal implementation**

```python
@app.post("/api/v1/agents/heartbeat")
def record_heartbeat(payload: AgentHeartbeatRequest) -> dict:
    agent = active_runtime.record_heartbeat(...)
    return {"agent": active_runtime.serialize_agent(agent)}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_api.py tests/test_monitor.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/openclaw_smart_agent/models.py src/openclaw_smart_agent/store.py src/openclaw_smart_agent/registry.py src/openclaw_smart_agent/runtime.py src/openclaw_smart_agent/api.py tests/test_api.py tests/test_monitor.py
git commit -m "feat: add heartbeat ingestion api"
```

### Task 2: Expose heartbeat through the OpenClaw plugin

**Files:**
- Modify: `plugin/src/index.ts`
- Test: `npm --prefix plugin run check`

- [ ] **Step 1: Write the failing test**

```text
Verification target: plugin should expose a `smart_agent_heartbeat` tool that forwards heartbeat payloads to `/api/v1/agents/heartbeat`.
```

- [ ] **Step 2: Run check to verify the new tool is missing**

Run: `npm --prefix plugin run check`
Expected: still PASS before the new tool exists, so confirm by inspecting code diff target rather than expecting a broken build

- [ ] **Step 3: Write minimal implementation**

```typescript
api.registerTool({
  name: "smart_agent_heartbeat",
  parameters: Type.Object({...}),
  async execute(_id, params) {
    return asTextContent(await callRuntime("/api/v1/agents/heartbeat", {...}));
  },
});
```

- [ ] **Step 4: Run check to verify it passes**

Run: `npm --prefix plugin run check`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add plugin/src/index.ts
git commit -m "feat: expose heartbeat tool in plugin"
```

### Task 3: Clarify install and integration flows for a skill-first repository

**Files:**
- Modify: `scripts/install.sh`
- Modify: `README.md`
- Create: `docs/openclaw-integration.md`
- Test: `tests/test_ci_files.py`

- [ ] **Step 1: Write the failing test**

```python
assert "docs/openclaw-integration.md" in readme_text
assert "smart_agent_heartbeat" in readme_text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_ci_files.py -q`
Expected: FAIL because README does not reference the new integration guide or heartbeat tool yet

- [ ] **Step 3: Write minimal implementation**

```markdown
See [docs/openclaw-integration.md](docs/openclaw-integration.md) for local setup, runtime verification, and plugin installation paths.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_ci_files.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/install.sh README.md docs/openclaw-integration.md tests/test_ci_files.py
git commit -m "docs: clarify openclaw integration flow"
```

### Task 4: Document template extension for skill users

**Files:**
- Create: `docs/template-guide.md`
- Modify: `README.md`
- Modify: `skills/openclaw-smart-agent/SKILL.md`
- Test: `tests/test_ci_files.py`

- [ ] **Step 1: Write the failing test**

```python
assert "docs/template-guide.md" in readme_text
assert "template" in skill_text.casefold()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_ci_files.py -q`
Expected: FAIL because the template guide does not exist and the skill does not direct users to it

- [ ] **Step 3: Write minimal implementation**

```markdown
Create a YAML file in `src/openclaw_smart_agent/templates/` with `role`, `keywords`, `skills`, `tools`, `system_prompt`, and `resource_weight`.
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_ci_files.py tests/test_identity.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add docs/template-guide.md README.md skills/openclaw-smart-agent/SKILL.md tests/test_ci_files.py
git commit -m "docs: add template extension guide"
```
