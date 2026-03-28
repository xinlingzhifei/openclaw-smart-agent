# Smart Agent Routing Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Smart Agent routing reflect real skill match ratios, load-aware choice, and priority-ordered dispatch.

**Architecture:** Keep the current runtime shape, but move routing from a single-task immediate assignment model toward a small dispatch pass over pending tasks. The registry will expose dispatchable tasks and candidate selection helpers, while the router will sort tasks by priority and score candidates using partial skill overlap plus load and urgency.

**Tech Stack:** Python 3.11+, FastAPI, SQLite, pytest

---

### Task 1: Add failing routing tests

**Files:**
- Create: `E:\subAgent\tests\test_router.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_router_prefers_higher_partial_skill_match(...):
    ...

def test_router_prefers_lower_load_for_equal_skills(...):
    ...

def test_router_dispatches_high_priority_pending_task_first(...):
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_router.py -q`
Expected: FAIL because partial matches and priority-ordered dispatch are not implemented yet

- [ ] **Step 3: Write minimal implementation**

```python
tasks = registry.list_dispatchable_tasks()
for task in tasks:
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_router.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_router.py src/openclaw_smart_agent/router.py src/openclaw_smart_agent/registry.py
git commit -m "feat: improve smart agent routing semantics"
```

### Task 2: Integrate the new routing flow with publish-task behavior

**Files:**
- Modify: `E:\subAgent\src\openclaw_smart_agent\router.py`
- Modify: `E:\subAgent\tests\test_api.py`

- [ ] **Step 1: Write the failing test**

```python
def test_publish_task_api_uses_low_load_agent_when_skills_are_equal(...):
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_api.py -q`
Expected: FAIL because current API coverage does not prove low-load preference

- [ ] **Step 3: Write minimal implementation**

```python
task = self.registry.create_task(...)
self.dispatch_pending_tasks()
return self.registry.get_task(task.task_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_api.py tests/test_router.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/openclaw_smart_agent/router.py tests/test_api.py tests/test_router.py
git commit -m "test: cover routing priority and load behavior"
```
