declare module "openclaw/plugin-sdk/plugin-entry" {
  type ToolResult = {
    content: Array<{
      type: "text";
      text: string;
    }>;
  };

  type ToolDefinition<TParameters> = {
    name: string;
    description: string;
    parameters: unknown;
    execute: (id: string, params: TParameters) => Promise<ToolResult> | ToolResult;
  };

  type PluginLogger = {
    debug?: (message: string) => void;
    info: (message: string) => void;
    warn: (message: string) => void;
    error: (message: string) => void;
  };

  type ServiceContext = {
    config: unknown;
    workspaceDir?: string;
    stateDir: string;
    logger: PluginLogger;
  };

  type ServiceDefinition = {
    id: string;
    start: (ctx: ServiceContext) => Promise<void> | void;
    stop?: (ctx: ServiceContext) => Promise<void> | void;
  };

  type PluginApi = {
    registrationMode?: "full" | "setup-only" | "setup-runtime";
    pluginConfig: Record<string, unknown>;
    resolvePath: (input: string) => string;
    registerTool: <TParameters>(tool: ToolDefinition<TParameters>) => void;
    registerService: (service: ServiceDefinition) => void;
  };

  export function definePluginEntry(entry: {
    id: string;
    name: string;
    description: string;
    register: (api: PluginApi) => void;
  }): unknown;
}
