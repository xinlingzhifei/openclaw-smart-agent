import { spawn, type ChildProcess } from "node:child_process";
import path from "node:path";
import { setTimeout as delay } from "node:timers/promises";

export const DEFAULT_RUNTIME_BASE_URL = "http://127.0.0.1:8787";
export const DEFAULT_RUNTIME_COMMAND = "openclaw-smart-agent";
export const DEFAULT_RUNTIME_CONFIG_BASENAME = "config.yaml";

const DEFAULT_PROBE_ATTEMPTS = 10;
const DEFAULT_PROBE_DELAY_MS = 500;
const DEFAULT_STOP_TIMEOUT_MS = 3000;
const RUNTIME_STATUS_PATH = "/api/v1/agents/status";

export type RuntimeAutostartLogger = {
  debug?: (message: string) => void;
  info?: (message: string) => void;
  warn?: (message: string) => void;
  error?: (message: string) => void;
};

export type RuntimeAutostartOptions = {
  autoStartRuntime: boolean;
  runtimeBaseUrl: string;
  runtimeConfigPath: string;
  probeAttempts?: number;
  probeDelayMs?: number;
};

export type RuntimeAutostartStartResult =
  | { status: "reachable" }
  | { status: "disabled" }
  | { status: "started"; pid?: number }
  | { status: "failed"; pid?: number };

export type ManagedChildProcess = Pick<ChildProcess, "pid" | "exitCode" | "kill"> & {
  once(event: "exit", listener: (code: number | null, signal: NodeJS.Signals | null) => void): ManagedChildProcess;
};

type ResolveRuntimeAutostartOptionsArgs = {
  pluginConfig: Record<string, unknown>;
  env: NodeJS.ProcessEnv;
  resolvePath: (input: string) => string;
  stateDir: string;
  pathExists: (targetPath: string) => boolean;
};

type RuntimeAutostartDeps = {
  probeRuntime?: (baseUrl: string) => Promise<boolean>;
  spawnRuntime?: (options: RuntimeAutostartOptions) => ManagedChildProcess;
  wait?: (ms: number) => Promise<void>;
};

function normalizeBaseUrl(rawValue: string | undefined): string {
  const candidate = rawValue?.trim();
  if (!candidate) {
    return DEFAULT_RUNTIME_BASE_URL;
  }
  return candidate.replace(/\/+$/, "");
}

function resolveConfiguredPath(input: string, resolvePath: (value: string) => string): string {
  if (path.isAbsolute(input)) {
    return input;
  }
  return resolvePath(input);
}

function waitForChildExit(
  child: ManagedChildProcess,
  timeoutMs: number,
  wait: (ms: number) => Promise<void>,
): Promise<void> {
  if (child.exitCode !== null) {
    return Promise.resolve();
  }

  return new Promise((resolve) => {
    let settled = false;
    const finish = () => {
      if (settled) {
        return;
      }
      settled = true;
      resolve();
    };

    child.once("exit", () => finish());
    void wait(timeoutMs).then(() => finish());
  });
}

function defaultSpawnRuntime(options: RuntimeAutostartOptions): ManagedChildProcess {
  return spawn(
    DEFAULT_RUNTIME_COMMAND,
    ["serve", "--config", options.runtimeConfigPath],
    {
      stdio: "ignore",
      windowsHide: true,
    },
  ) as ManagedChildProcess;
}

export async function probeRuntime(
  baseUrl: string,
  fetchImpl: typeof fetch = fetch,
): Promise<boolean> {
  try {
    const response = await fetchImpl(`${normalizeBaseUrl(baseUrl)}${RUNTIME_STATUS_PATH}`, {
      method: "GET",
    });
    return response.ok;
  } catch {
    return false;
  }
}

export function resolveRuntimeAutostartOptions({
  pluginConfig,
  env,
  resolvePath,
  stateDir,
  pathExists,
}: ResolveRuntimeAutostartOptionsArgs): RuntimeAutostartOptions {
  const configuredPath =
    typeof pluginConfig.runtimeConfigPath === "string" && pluginConfig.runtimeConfigPath.trim()
      ? resolveConfiguredPath(pluginConfig.runtimeConfigPath.trim(), resolvePath)
      : null;
  const repoDefaultPath = resolvePath("../config/config.yaml");
  const runtimeConfigPath =
    configuredPath ?? (pathExists(repoDefaultPath) ? repoDefaultPath : path.join(stateDir, DEFAULT_RUNTIME_CONFIG_BASENAME));

  return {
    autoStartRuntime: typeof pluginConfig.autoStartRuntime === "boolean" ? pluginConfig.autoStartRuntime : true,
    runtimeBaseUrl: normalizeBaseUrl(env.OPENCLAW_SMART_AGENT_BASE_URL),
    runtimeConfigPath,
  };
}

export function createRuntimeAutostartSupervisor({
  probeRuntime: probe = probeRuntime,
  spawnRuntime = defaultSpawnRuntime,
  wait = async (ms: number) => delay(ms),
}: RuntimeAutostartDeps = {}) {
  let ownedChild: ManagedChildProcess | null = null;
  let startPromise: Promise<RuntimeAutostartStartResult> | null = null;

  const clearOwnedChild = (candidate?: ManagedChildProcess | null) => {
    if (!candidate || ownedChild === candidate) {
      ownedChild = null;
    }
  };

  const stopOwnedChild = async (logger?: RuntimeAutostartLogger) => {
    const child = ownedChild;
    if (!child) {
      return;
    }

    clearOwnedChild(child);

    if (child.exitCode !== null) {
      return;
    }

    try {
      child.kill();
      logger?.info?.("Stopped plugin-owned Smart Agent runtime child process.");
    } catch (error) {
      logger?.warn?.(
        `Failed to stop plugin-owned Smart Agent runtime cleanly: ${String(error)}`,
      );
      return;
    }

    await waitForChildExit(child, DEFAULT_STOP_TIMEOUT_MS, wait);

    if (child.exitCode === null) {
      try {
        child.kill("SIGKILL");
        logger?.warn?.("Force-killed plugin-owned Smart Agent runtime child process.");
      } catch (error) {
        logger?.warn?.(
          `Failed to force-kill plugin-owned Smart Agent runtime: ${String(error)}`,
        );
      }
    }
  };

  return {
    async start(
      options: RuntimeAutostartOptions,
      logger?: RuntimeAutostartLogger,
    ): Promise<RuntimeAutostartStartResult> {
      if (startPromise) {
        return startPromise;
      }

      startPromise = (async () => {
        const isReachable = await probe(options.runtimeBaseUrl);
        if (isReachable) {
          logger?.debug?.("Smart Agent runtime already reachable; auto-start skipped.");
          return { status: "reachable" } as const;
        }

        if (!options.autoStartRuntime) {
          logger?.info?.("Smart Agent runtime auto-start disabled; leaving runtime unmanaged.");
          return { status: "disabled" } as const;
        }

        let child: ManagedChildProcess;
        try {
          child = spawnRuntime(options);
        } catch (error) {
          logger?.error?.(`Failed to spawn Smart Agent runtime: ${String(error)}`);
          return { status: "failed" } as const;
        }

        ownedChild = child;
        child.once("exit", () => {
          clearOwnedChild(child);
        });
        logger?.info?.(
          `Starting Smart Agent runtime at ${options.runtimeBaseUrl} with config ${options.runtimeConfigPath}.`,
        );

        const probeAttempts = options.probeAttempts ?? DEFAULT_PROBE_ATTEMPTS;
        const probeDelayMs = options.probeDelayMs ?? DEFAULT_PROBE_DELAY_MS;

        for (let attempt = 0; attempt < probeAttempts; attempt += 1) {
          if (attempt > 0) {
            await wait(probeDelayMs);
          }

          if (child.exitCode !== null) {
            logger?.warn?.("Smart Agent runtime child exited before it became reachable.");
            break;
          }

          if (await probe(options.runtimeBaseUrl)) {
            logger?.info?.("Smart Agent runtime became reachable after plugin auto-start.");
            return { status: "started", pid: child.pid } as const;
          }
        }

        await stopOwnedChild(logger);
        logger?.error?.("Smart Agent runtime did not become reachable after auto-start.");
        return { status: "failed", pid: child.pid } as const;
      })().finally(() => {
        startPromise = null;
      });

      return startPromise;
    },

    async stop(logger?: RuntimeAutostartLogger): Promise<void> {
      await stopOwnedChild(logger);
    },
  };
}
