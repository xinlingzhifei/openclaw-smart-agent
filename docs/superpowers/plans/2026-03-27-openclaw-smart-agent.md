# OpenClaw Smart Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a GitHub-publishable OpenClaw plugin + Python runtime + workspace skill that provides identity enhancement, agent registration, smart task routing, health monitoring, and recovery for single-machine multi-agent orchestration.

**Architecture:** Use a Python package as the system of record for templates, registry state, routing, monitoring, persistence, and REST/CLI access. Expose that runtime through a thin OpenClaw plugin and a workspace skill that teaches the host agent when and how to invoke the plugin tools.

**Tech Stack:** Python 3.14, pytest, FastAPI, SQLite, PyYAML, Node 24, TypeScript, OpenClaw plugin SDK

---

### Task 1: Bootstrap the repository and test harness

**Files:**
- Create: `pyproject.toml`
- Create: `setup.py`
- Create: `.gitignore`
- Create: `README.md`
- Create: `CONTRIBUTING.md`
- Create: `tests/conftest.py`
- Test: `python -m pytest tests -q`

- [ ] **Step 1: Write the failing test**

```python
def test_package_version_is_importable():
    import openclaw_smart_agent

    assert openclaw_smart_agent.__version__ == "0.1.0"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'openclaw_smart_agent'`

- [ ] **Step 3: Write minimal implementation**

```python
__version__ = "0.1.0"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests -q`
Expected: PASS for the import test

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml setup.py .gitignore README.md CONTRIBUTING.md tests/conftest.py src/openclaw_smart_agent/__init__.py
git commit -m "chore: bootstrap smart agent repository"
```

### Task 2: Implement identity enhancement from templates

**Files:**
- Create: `src/openclaw_smart_agent/models.py`
- Create: `src/openclaw_smart_agent/config.py`
- Create: `src/openclaw_smart_agent/identity.py`
- Create: `src/openclaw_smart_agent/templates/python-developer.yaml`
- Create: `src/openclaw_smart_agent/templates/data-analyst.yaml`
- Create: `tests/test_identity.py`
- Test: `tests/test_identity.py`

- [ ] **Step 1: Write the failing test**

```python
def test_identity_enhancer_uses_keyword_template_match(tmp_path):
    enhancer = IdentityEnhancer(template_dir=template_dir)
    profile = enhancer.enhance("Senior Python开发")

    assert profile.role == "python-developer"
    assert "python" in profile.skills
    assert profile.system_prompt
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_identity.py -q`
Expected: FAIL because `IdentityEnhancer` is undefined

- [ ] **Step 3: Write minimal implementation**

```python
class IdentityEnhancer:
    def enhance(self, identity: str) -> AgentProfile:
        ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_identity.py -q`
Expected: PASS with template-backed profile output

- [ ] **Step 5: Commit**

```bash
git add src/openclaw_smart_agent/models.py src/openclaw_smart_agent/config.py src/openclaw_smart_agent/identity.py src/openclaw_smart_agent/templates tests/test_identity.py
git commit -m "feat: add identity enhancement templates"
```

### Task 3: Implement registry persistence and task routing

**Files:**
- Create: `src/openclaw_smart_agent/store.py`
- Create: `src/openclaw_smart_agent/registry.py`
- Create: `src/openclaw_smart_agent/router.py`
- Create: `tests/test_registry.py`
- Create: `tests/test_router.py`
- Test: `tests/test_registry.py`
- Test: `tests/test_router.py`

- [ ] **Step 1: Write the failing test**

```python
def test_router_prefers_best_skill_match_with_lower_load(runtime):
    first = runtime.create_agent("Python开发")
    second = runtime.create_agent("Python开发")
    runtime.registry.update_load(first.agent_id, running_tasks=3, cpu_percent=45.0, memory_percent=35.0)
    runtime.registry.update_load(second.agent_id, running_tasks=1, cpu_percent=12.0, memory_percent=10.0)

    task = runtime.publish_task("Implement parser", ["python"])

    assert task.assigned_agent_id == second.agent_id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_registry.py tests/test_router.py -q`
Expected: FAIL because registry, store, or router classes are missing

- [ ] **Step 3: Write minimal implementation**

```python
score = capability_match * weights.capability + low_load * weights.load + priority_bias * weights.priority
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_registry.py tests/test_router.py -q`
Expected: PASS with SQLite-backed agent and task state

- [ ] **Step 5: Commit**

```bash
git add src/openclaw_smart_agent/store.py src/openclaw_smart_agent/registry.py src/openclaw_smart_agent/router.py tests/test_registry.py tests/test_router.py
git commit -m "feat: add registry persistence and smart router"
```

### Task 4: Implement health monitoring and recovery

**Files:**
- Create: `src/openclaw_smart_agent/monitor.py`
- Create: `src/openclaw_smart_agent/recovery.py`
- Create: `tests/test_monitor.py`
- Test: `tests/test_monitor.py`

- [ ] **Step 1: Write the failing test**

```python
def test_monitor_marks_agent_unhealthy_and_requeues_tasks(runtime):
    agent = runtime.create_agent("Python开发")
    task = runtime.publish_task("Fix bug", ["python"])
    runtime.start_task(task.task_id, agent.agent_id)

    runtime.monitor.record_heartbeat(agent.agent_id, cpu_percent=95.0, memory_percent=91.0, consecutive_errors=4)
    runtime.monitor.evaluate()

    refreshed = runtime.registry.get_agent(agent.agent_id)
    retried_task = runtime.registry.get_task(task.task_id)

    assert refreshed.status == AgentStatus.UNHEALTHY
    assert retried_task.status == TaskStatus.REQUEUED
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_monitor.py -q`
Expected: FAIL because monitor or recovery code is missing

- [ ] **Step 3: Write minimal implementation**

```python
if heartbeat.cpu_percent >= thresholds.max_cpu_percent or heartbeat.consecutive_errors >= thresholds.max_consecutive_errors:
    registry.mark_unhealthy(agent_id)
    recovery.requeue_running_tasks(agent_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_monitor.py -q`
Expected: PASS with unhealthy agents blocked from new work

- [ ] **Step 5: Commit**

```bash
git add src/openclaw_smart_agent/monitor.py src/openclaw_smart_agent/recovery.py tests/test_monitor.py
git commit -m "feat: add health monitoring and recovery"
```

### Task 5: Implement runtime facade, REST API, and CLI

**Files:**
- Create: `src/openclaw_smart_agent/runtime.py`
- Create: `src/openclaw_smart_agent/api.py`
- Create: `src/openclaw_smart_agent/cli.py`
- Create: `config/config.example.yaml`
- Create: `tests/test_api.py`
- Test: `tests/test_api.py`

- [ ] **Step 1: Write the failing test**

```python
def test_create_agent_api_returns_generated_profile(client):
    response = client.post("/api/v1/agents/create", json={"identity": "Python开发"})

    assert response.status_code == 200
    body = response.json()
    assert body["profile"]["role"] == "python-developer"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_api.py -q`
Expected: FAIL because FastAPI app or runtime facade is missing

- [ ] **Step 3: Write minimal implementation**

```python
@app.post("/api/v1/agents/create")
def create_agent(payload: CreateAgentRequest) -> dict:
    return runtime.create_agent_response(payload.identity)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_api.py -q`
Expected: PASS for create agent, status query, and task publish routes

- [ ] **Step 5: Commit**

```bash
git add src/openclaw_smart_agent/runtime.py src/openclaw_smart_agent/api.py src/openclaw_smart_agent/cli.py config/config.example.yaml tests/test_api.py
git commit -m "feat: add runtime facade api and cli"
```

### Task 6: Implement OpenClaw plugin and workspace skill

**Files:**
- Create: `plugin/package.json`
- Create: `plugin/tsconfig.json`
- Create: `plugin/openclaw.plugin.json`
- Create: `plugin/src/index.ts`
- Create: `skills/openclaw-smart-agent/SKILL.md`
- Create: `skills/openclaw-smart-agent/agents/openai.yaml`
- Create: `skills/openclaw-smart-agent/references/api.md`
- Test: `npm --prefix plugin run check`

- [ ] **Step 1: Write the failing test**

```typescript
// Pseudotest target: `npm --prefix plugin run check`
// Expected initial failure: missing package manifest or TypeScript sources
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix plugin run check`
Expected: FAIL because plugin package files do not exist yet

- [ ] **Step 3: Write minimal implementation**

```typescript
export default definePluginEntry({
  id: "openclaw-smart-agent",
  name: "OpenClaw Smart Agent",
  description: "Proxy tools for the Smart Agent runtime",
  register(api) {
    api.registerTool(...);
  },
});
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix plugin run check`
Expected: PASS for TypeScript type-checking

- [ ] **Step 5: Commit**

```bash
git add plugin skills/openclaw-smart-agent
git commit -m "feat: add openclaw plugin and workspace skill"
```

### Task 7: Finish install flows and documentation

**Files:**
- Create: `scripts/install.sh`
- Modify: `README.md`
- Modify: `CONTRIBUTING.md`
- Test: `python -m pytest tests -q`
- Test: `npm --prefix plugin run check`

- [ ] **Step 1: Write the failing test**

```text
Verification target: README lacks Quick Start for pip + GitHub + OpenClaw plugin integration.
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests -q`
Expected: PASS for code, but docs/install flow still incomplete until README and install script are added

- [ ] **Step 3: Write minimal implementation**

```bash
python -m pip install "git+https://github.com/<owner>/<repo>.git"
openclaw-smart-agent init-config
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests -q`
Expected: PASS

Run: `npm --prefix plugin run check`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/install.sh README.md CONTRIBUTING.md
git commit -m "docs: add installation and contribution guides"
```
