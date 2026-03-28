import { existsSync } from "node:fs";
import { Type } from "@sinclair/typebox";
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import {
  DEFAULT_RUNTIME_BASE_URL,
  createRuntimeAutostartSupervisor,
  resolveRuntimeAutostartOptions,
} from "./runtime-autostart.js";

const runtimeSupervisor = createRuntimeAutostartSupervisor();

function getRuntimeBaseUrl() {
  const candidate = process.env.OPENCLAW_SMART_AGENT_BASE_URL?.trim() || DEFAULT_RUNTIME_BASE_URL;
  return candidate.replace(/\/+$/, "");
}

async function callRuntime(path: string, init?: RequestInit): Promise<unknown> {
  const response = await fetch(`${getRuntimeBaseUrl()}${path}`, {
    headers: {
      "content-type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Smart Agent runtime error (${response.status}): ${body}`);
  }

  return response.json();
}

function asTextContent(payload: unknown) {
  return {
    content: [
      {
        type: "text" as const,
        text: JSON.stringify(payload, null, 2),
      },
    ],
  };
}

export default definePluginEntry({
  id: "openclaw-smart-agent",
  name: "OpenClaw Smart Agent",
  description: "Proxy tools for the Smart Agent runtime.",
  register(api) {
    if (api.registrationMode === "full") {
      api.registerService({
        id: "runtime-autostart",
        async start(ctx) {
          await runtimeSupervisor.start(
            resolveRuntimeAutostartOptions({
              pluginConfig: api.pluginConfig,
              env: process.env,
              resolvePath: api.resolvePath,
              stateDir: ctx.stateDir,
              pathExists: existsSync,
            }),
            ctx.logger,
          );
        },
        async stop(ctx) {
          await runtimeSupervisor.stop(ctx.logger);
        },
      });
    }

    api.registerTool({
      name: "smart_agent_create",
      description: "Create or register a Smart Agent from a short identity description.",
      parameters: Type.Object({
        identity: Type.String({ minLength: 1 }),
      }),
      async execute(_id, params: { identity: string }) {
        const payload = await callRuntime("/api/v1/agents/create", {
          method: "POST",
          body: JSON.stringify({ identity: params.identity }),
        });
        return asTextContent(payload);
      },
    });

    api.registerTool({
      name: "smart_agent_status",
      description: "Get the current Smart Agent registry, health, and load state.",
      parameters: Type.Object({}, { additionalProperties: false }),
      async execute() {
        const payload = await callRuntime("/api/v1/agents/status", {
          method: "GET",
        });
        return asTextContent(payload);
      },
    });

    api.registerTool({
      name: "smart_agent_heartbeat",
      description: "Record a heartbeat snapshot for a Smart Agent and refresh its health state.",
      parameters: Type.Object({
        agent_id: Type.String({ minLength: 1 }),
        cpu_percent: Type.Number({ minimum: 0, maximum: 100 }),
        memory_percent: Type.Number({ minimum: 0, maximum: 100 }),
        consecutive_errors: Type.Optional(Type.Number({ minimum: 0 })),
        current_task_id: Type.Optional(Type.String()),
      }),
      async execute(
        _id,
        params: {
          agent_id: string;
          cpu_percent: number;
          memory_percent: number;
          consecutive_errors?: number;
          current_task_id?: string;
        },
      ) {
        const payload = await callRuntime("/api/v1/agents/heartbeat", {
          method: "POST",
          body: JSON.stringify({
            agent_id: params.agent_id,
            cpu_percent: params.cpu_percent,
            memory_percent: params.memory_percent,
            consecutive_errors: params.consecutive_errors ?? 0,
            current_task_id: params.current_task_id ?? null,
          }),
        });
        return asTextContent(payload);
      },
    });

    api.registerTool({
      name: "smart_agent_publish_task",
      description: "Publish a task and let the Smart Agent router pick the best worker.",
      parameters: Type.Object({
        task_desc: Type.String({ minLength: 1 }),
        required_skills: Type.Array(Type.String()),
        priority: Type.Optional(Type.Number({ minimum: 1, maximum: 10 })),
      }),
      async execute(
        _id,
        params: { task_desc: string; required_skills: string[]; priority?: number },
      ) {
        const payload = await callRuntime("/api/v1/tasks/publish", {
          method: "POST",
          body: JSON.stringify({
            task_desc: params.task_desc,
            required_skills: params.required_skills,
            priority: params.priority ?? 1,
          }),
        });
        return asTextContent(payload);
      },
    });
  },
});
