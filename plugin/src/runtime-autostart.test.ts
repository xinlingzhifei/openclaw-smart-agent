import { EventEmitter } from "node:events";
import path from "node:path";
import test from "node:test";
import assert from "node:assert/strict";

import {
  createRuntimeAutostartSupervisor,
  resolveRuntimeAutostartOptions,
} from "./runtime-autostart.js";

class FakeChildProcess extends EventEmitter {
  exitCode: number | null = null;
  killCalls: Array<NodeJS.Signals | undefined> = [];

  constructor(readonly pid = 4242) {
    super();
  }

  kill(signal?: NodeJS.Signals) {
    this.killCalls.push(signal);
    this.exitCode = 0;
    this.emit("exit", 0, signal ?? null);
    return true;
  }
}

test("resolveRuntimeAutostartOptions prefers explicit runtime config path", () => {
  const options = resolveRuntimeAutostartOptions({
    pluginConfig: {
      autoStartRuntime: true,
      runtimeConfigPath: "configs/runtime.yaml",
    },
    env: {},
    resolvePath: (input) => `E:/subAgent/plugin/${input}`,
    stateDir: "E:/state",
    pathExists: () => false,
  });

  assert.equal(options.autoStartRuntime, true);
  assert.equal(options.runtimeBaseUrl, "http://127.0.0.1:8787");
  assert.equal(options.runtimeConfigPath, "E:/subAgent/plugin/configs/runtime.yaml");
});

test("resolveRuntimeAutostartOptions falls back to plugin state when repo config is absent", () => {
  const options = resolveRuntimeAutostartOptions({
    pluginConfig: {},
    env: {
      OPENCLAW_SMART_AGENT_BASE_URL: "http://127.0.0.1:9898",
    },
    resolvePath: (input) => `E:/subAgent/plugin/${input}`,
    stateDir: "E:/state",
    pathExists: () => false,
  });

  assert.equal(options.autoStartRuntime, true);
  assert.equal(options.runtimeBaseUrl, "http://127.0.0.1:9898");
  assert.equal(options.runtimeConfigPath, path.join("E:/state", "config.yaml"));
});

test("supervisor does not spawn when the runtime is already reachable", async () => {
  let spawnCount = 0;
  const supervisor = createRuntimeAutostartSupervisor({
    probeRuntime: async () => true,
    spawnRuntime: () => {
      spawnCount += 1;
      return new FakeChildProcess();
    },
    wait: async () => {},
  });

  const result = await supervisor.start({
    autoStartRuntime: true,
    runtimeBaseUrl: "http://127.0.0.1:8787",
    runtimeConfigPath: "E:/state/config.yaml",
    probeAttempts: 1,
    probeDelayMs: 0,
  });

  assert.equal(result.status, "reachable");
  assert.equal(spawnCount, 0);
  await supervisor.stop();
});

test("supervisor spawns and owns the runtime only when the first probe fails", async () => {
  let probeCalls = 0;
  let spawnCount = 0;
  let child: FakeChildProcess | undefined;
  const supervisor = createRuntimeAutostartSupervisor({
    probeRuntime: async () => {
      probeCalls += 1;
      return probeCalls >= 2;
    },
    spawnRuntime: () => {
      spawnCount += 1;
      child = new FakeChildProcess();
      return child;
    },
    wait: async () => {},
  });

  const result = await supervisor.start({
    autoStartRuntime: true,
    runtimeBaseUrl: "http://127.0.0.1:8787",
    runtimeConfigPath: "E:/state/config.yaml",
    probeAttempts: 3,
    probeDelayMs: 0,
  });

  assert.equal(result.status, "started");
  assert.equal(result.pid, 4242);
  assert.equal(spawnCount, 1);

  await supervisor.stop();
  assert.deepEqual(child?.killCalls, [undefined]);
});

test("supervisor respects disabled auto-start and leaves runtime unmanaged", async () => {
  let spawnCount = 0;
  const supervisor = createRuntimeAutostartSupervisor({
    probeRuntime: async () => false,
    spawnRuntime: () => {
      spawnCount += 1;
      return new FakeChildProcess();
    },
    wait: async () => {},
  });

  const result = await supervisor.start({
    autoStartRuntime: false,
    runtimeBaseUrl: "http://127.0.0.1:8787",
    runtimeConfigPath: "E:/state/config.yaml",
    probeAttempts: 1,
    probeDelayMs: 0,
  });

  assert.equal(result.status, "disabled");
  assert.equal(spawnCount, 0);
  await supervisor.stop();
});
