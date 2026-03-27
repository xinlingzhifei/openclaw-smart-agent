# OpenClaw Identity LLM Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional OpenClaw-backed `llm-task` fallback so unmatched identity strings can generate structured agent profiles before registration.

**Architecture:** Keep template matching as the primary path. Add a small OpenClaw Gateway client that invokes `llm-task`, wire it into `IdentityEnhancer` through configuration, and preserve the current default profile fallback whenever OpenClaw is unavailable or returns invalid data.

**Tech Stack:** Python 3.11+, FastAPI, pytest, OpenClaw Gateway `/tools/invoke`, YAML config

---

### Task 1: Define the new configuration surface

**Files:**
- Modify: `E:\subAgent\src\openclaw_smart_agent\config.py`
- Modify: `E:\subAgent\config\config.example.yaml`
- Test: `E:\subAgent\tests\test_identity.py`

- [ ] Add `IdentityConfig` and nest it into `RuntimeConfig`
- [ ] Cover config loading/dumping with a failing test first
- [ ] Expose gateway URL, auth token, session key, provider/model, thinking, timeout, and max token settings

### Task 2: Add OpenClaw Gateway client + unmatched-template fallback

**Files:**
- Create: `E:\subAgent\src\openclaw_smart_agent\openclaw_llm.py`
- Modify: `E:\subAgent\src\openclaw_smart_agent\identity.py`
- Modify: `E:\subAgent\src\openclaw_smart_agent\runtime.py`
- Test: `E:\subAgent\tests\test_identity.py`
- Test: `E:\subAgent\tests\test_api.py`

- [ ] Write failing tests for unmatched-template LLM generation and failure fallback
- [ ] Implement a minimal client for `POST /tools/invoke`
- [ ] Sanitize returned role/skills/tools/system prompt/resource weight
- [ ] Wire the client into `IdentityEnhancer` only when configured

### Task 3: Document how to enable the fallback in OpenClaw

**Files:**
- Modify: `E:\subAgent\README.md`
- Modify: `E:\subAgent\docs\openclaw-integration.md`
- Modify: `E:\subAgent\skills\openclaw-smart-agent\SKILL.md`
- Modify: `E:\subAgent\skills\openclaw-smart-agent\references\api.md`

- [ ] Document required `llm-task` plugin enablement and allowlist
- [ ] Show the new config block
- [ ] Explain that template match still wins and OpenClaw fallback is only used for misses

### Task 4: Verify the feature end to end

**Files:**
- Test only

- [ ] Run targeted identity and API tests
- [ ] Run the full test suite
- [ ] Run plugin typecheck to confirm no unrelated regressions
