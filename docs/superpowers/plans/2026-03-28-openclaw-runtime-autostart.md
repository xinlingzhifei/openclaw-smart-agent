# OpenClaw Runtime Auto-Start Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Start and stop the Smart Agent runtime automatically with the OpenClaw plugin lifecycle when the runtime is not already running.

**Architecture:** Extract runtime probing, config resolution, spawn, and owned-child cleanup into a small plugin helper module. The plugin entry will register a background service that delegates lifecycle work to that helper, while the existing tools keep talking to the same HTTP runtime base URL.

**Tech Stack:** TypeScript, Node.js child processes, OpenClaw plugin SDK, Node test runner via `tsx`

---

### Task 1: Add failing auto-start tests

**Files:**
- Modify: `E:\subAgent\plugin\package.json`
- Create: `E:\subAgent\plugin\src\runtime-autostart.test.ts`

- [ ] **Step 1: Write the failing tests**

```ts
test("supervisor does not spawn when the runtime is already reachable", async () => {
  ...
});

test("supervisor spawns and owns the runtime only when the first probe fails", async () => {
  ...
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix plugin test`
Expected: FAIL because `runtime-autostart.ts` does not exist yet

- [ ] **Step 3: Add the test runner dependency**

```json
"scripts": {
  "test": "tsx --test src/**/*.test.ts"
}
```

- [ ] **Step 4: Re-run the test**

Run: `npm --prefix plugin test`
Expected: FAIL with module-not-found or missing export errors, proving the tests are wired up

- [ ] **Step 5: Commit**

```bash
git add plugin/package.json plugin/package-lock.json plugin/src/runtime-autostart.test.ts
git commit -m "test: add runtime auto-start plugin tests"
```

### Task 2: Implement runtime auto-start helper

**Files:**
- Create: `E:\subAgent\plugin\src\runtime-autostart.ts`

- [ ] **Step 1: Write the minimal helper implementation**

```ts
export function resolveRuntimeAutostartOptions(...) {
  ...
}

export function createRuntimeAutostartSupervisor(...) {
  ...
}
```

- [ ] **Step 2: Run plugin tests**

Run: `npm --prefix plugin test`
Expected: PASS

- [ ] **Step 3: Refine cleanup and startup failure handling**

```ts
if (!reachableAfterSpawn) {
  await stopOwnedChild();
}
```

- [ ] **Step 4: Re-run plugin tests**

Run: `npm --prefix plugin test`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add plugin/src/runtime-autostart.ts plugin/src/runtime-autostart.test.ts
git commit -m "feat: add plugin runtime auto-start supervisor"
```

### Task 3: Wire the helper into the plugin entry and docs

**Files:**
- Modify: `E:\subAgent\plugin\src\index.ts`
- Modify: `E:\subAgent\plugin\openclaw.plugin.json`
- Modify: `E:\subAgent\README.md`
- Modify: `E:\subAgent\docs\openclaw-integration.md`
- Modify: `E:\subAgent\tests\test_ci_files.py`

- [ ] **Step 1: Register the background service in the plugin entry**

```ts
api.registerService({
  id: "runtime-autostart",
  async start(ctx) {
    ...
  },
  async stop() {
    ...
  },
});
```

- [ ] **Step 2: Update the manifest config schema**

```json
"properties": {
  "autoStartRuntime": { "type": "boolean", "default": true },
  "runtimeConfigPath": { "type": "string", "minLength": 1 }
}
```

- [ ] **Step 3: Document the new startup behavior**

```md
The plugin can auto-start the runtime when OpenClaw Gateway loads it.
```

- [ ] **Step 4: Run verification**

Run:
- `npm --prefix plugin test`
- `npm --prefix plugin run check`
- `python -m pytest tests/test_ci_files.py -q`
- `python -m pytest tests -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add plugin/src/index.ts plugin/openclaw.plugin.json README.md docs/openclaw-integration.md tests/test_ci_files.py
git commit -m "feat: auto-start smart agent runtime with plugin lifecycle"
```
