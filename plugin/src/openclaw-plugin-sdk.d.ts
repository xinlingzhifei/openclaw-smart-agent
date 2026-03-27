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

  type PluginApi = {
    registerTool: <TParameters>(tool: ToolDefinition<TParameters>) => void;
  };

  export function definePluginEntry(entry: {
    id: string;
    name: string;
    description: string;
    register: (api: PluginApi) => void;
  }): unknown;
}
