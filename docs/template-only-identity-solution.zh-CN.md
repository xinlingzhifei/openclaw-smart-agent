# 未命中模板且不使用 OpenClaw LLM 的解决方案

这份文档说明一种更稳定、可控的做法：

- 未命中身份模板时，不启用 OpenClaw `llm-task`
- 继续使用本地 YAML 模板完成身份补全
- 通过补模板来解决 `Java开发`、`资深作家` 这类长尾身份变成 `generalist` 的问题

## 适用场景

适合下面这些情况：

- 你不想依赖 OpenClaw 大模型生成身份
- 你希望角色定义可审计、可复现
- 你更在意技能字段的稳定性，而不是生成式灵活性

## 当前默认行为

如果 `identity.fallback_strategy` 不是 `openclaw_llm`，运行时会先做模板匹配：

1. 扫描 `src/openclaw_smart_agent/templates/` 下的 `.yaml`
2. 用 `keywords` 对输入身份做不区分大小写的包含匹配
3. 如果命中模板，返回模板里的 `role`、`skills`、`tools`
4. 如果没有命中，回退到默认配置：
   - `role: generalist`
   - `skills: ["general"]`
   - `tools: ["shell"]`

所以像 `Java开发` 没有模板时，出现的结果就是 `generalist + general`。

## 推荐解决方式

最推荐的方式是：

1. 保持 LLM fallback 关闭
2. 为你需要的角色补本地模板
3. 用模板关键词覆盖常见输入说法

这条路径的优点是：

- 路由技能稳定
- 输出一致，不会因为模型波动而变化
- 不依赖 Gateway、token、provider、auth profile

## 配置方式

创建或修改 `config/config.yaml`，保持下面这个配置：

```yaml
identity:
  fallback_strategy: "defaults"
  openclaw_gateway_url: "http://127.0.0.1:18789"
  gateway_bearer_token: null
  session_key: "main"
  thinking: "low"
  provider: null
  model: null
  auth_profile_id: null
  timeout_ms: 30000
  max_tokens: 800

system:
  heartbeat_interval_sec: 5
  max_retry_count: 3

router:
  strategy: "smart_scoring"
  capability_weight: 0.5
  load_weight: 0.3
  priority_weight: 0.2

monitor:
  auto_restart_on_crash: true
  heartbeat_timeout_sec: 15
  max_cpu_percent: 90
  max_memory_percent: 90
  max_consecutive_errors: 3
```

关键点只有一个：

```yaml
identity:
  fallback_strategy: "defaults"
```

这表示未命中模板时，直接走默认兜底，不调用 OpenClaw `llm-task`。

## 如何补一个 Java 模板

在 `src/openclaw_smart_agent/templates/` 下创建 `java-developer.yaml`：

```yaml
role: java-developer
keywords:
  - java
  - Java开发
  - Java工程师
  - 后端Java
skills:
  - java
  - spring
  - backend
  - api
tools:
  - shell
system_prompt: You are a Java development specialist focused on backend services and reliable delivery.
resource_weight: 0.8
```

这样输入下面这些身份时，就会命中这个模板：

- `Java开发`
- `高级Java工程师`
- `后端Java`

## 如何补一个作家模板

如果你希望 `资深作家agent` 也能被本地模板识别，可以再加一个 `writer.yaml`：

```yaml
role: writer
keywords:
  - 作家
  - 写作者
  - 文案
  - 内容创作
skills:
  - writing
  - editing
  - storytelling
tools:
  - shell
system_prompt: You are a writing specialist focused on clarity, structure, and strong narrative delivery.
resource_weight: 0.6
```

## 模板设计建议

- `keywords` 要覆盖用户真实会输入的说法
- `skills` 要用后续任务路由时真正会引用的名字
- 避免过宽关键词，比如只写 `开发`，容易误匹配
- 如果同一角色有多种说法，尽量都放到同一个模板里

## 验证方法

启动 runtime：

```bash
openclaw-smart-agent serve --config config/config.yaml
```

然后创建 agent：

```bash
curl -X POST http://127.0.0.1:8787/api/v1/agents/create \
  -H "content-type: application/json" \
  -d '{"identity":"Java开发"}'
```

如果模板正确命中，返回里的 `profile` 应该类似：

```json
{
  "identity": "Java开发",
  "role": "java-developer",
  "skills": ["java", "spring", "backend", "api"],
  "tools": ["shell"],
  "resource_weight": 0.8
}
```

如果仍然返回：

```json
{
  "role": "generalist",
  "skills": ["general"]
}
```

通常说明：

1. 模板文件没放到 `src/openclaw_smart_agent/templates/`
2. `keywords` 没覆盖到你的输入文本
3. runtime 没重启，仍在使用旧模板

## 什么时候应该继续用模板方案

优先继续用本地模板，而不是切到 LLM fallback 的情况：

- 角色种类有限，而且比较固定
- 你需要稳定的技能命名
- 你希望路由行为可预测
- 你不想处理 OpenClaw Gateway 和 `llm-task` 配置

## 什么时候再考虑 OpenClaw LLM fallback

只有在下面这些情况再考虑开启 `openclaw_llm`：

- 角色输入高度开放，长尾很多
- 你接受生成式结果存在波动
- 你已经稳定配置好了 OpenClaw Gateway、`llm-task`、provider 和 auth profile

## 结论

如果你不想让未命中模板时走 OpenClaw LLM，最直接可靠的解决办法不是改提示词，而是：

1. 保持 `fallback_strategy: defaults`
2. 为常见角色补 YAML 模板
3. 用模板驱动技能和路由

对于 `Java开发` 这种场景，补一个 `java-developer.yaml` 就足够了。
