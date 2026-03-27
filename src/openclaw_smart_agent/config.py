from dataclasses import dataclass, field
import os
from pathlib import Path

import yaml


@dataclass(slots=True)
class IdentityDefaults:
    role: str = "generalist"
    skills: list[str] = field(default_factory=lambda: ["general"])
    tools: list[str] = field(default_factory=lambda: ["shell"])
    system_prompt: str = "You are a versatile agent that can accept general tasks."
    resource_weight: float = 0.5


@dataclass(slots=True)
class IdentityConfig:
    fallback_strategy: str = "defaults"
    openclaw_gateway_url: str = "http://127.0.0.1:18789"
    gateway_bearer_token: str | None = None
    session_key: str = "main"
    thinking: str = "low"
    provider: str | None = None
    model: str | None = None
    auth_profile_id: str | None = None
    timeout_ms: int = 30000
    max_tokens: int = 800


@dataclass(slots=True)
class SystemConfig:
    heartbeat_interval_sec: int = 5
    max_retry_count: int = 3


@dataclass(slots=True)
class RouterConfig:
    strategy: str = "smart_scoring"
    capability_weight: float = 0.5
    load_weight: float = 0.3
    priority_weight: float = 0.2


@dataclass(slots=True)
class MonitorConfig:
    auto_restart_on_crash: bool = True
    heartbeat_timeout_sec: int = 15
    max_cpu_percent: float = 90.0
    max_memory_percent: float = 90.0
    max_consecutive_errors: int = 3


@dataclass(slots=True)
class RuntimeConfig:
    identity: IdentityConfig = field(default_factory=IdentityConfig)
    system: SystemConfig = field(default_factory=SystemConfig)
    router: RouterConfig = field(default_factory=RouterConfig)
    monitor: MonitorConfig = field(default_factory=MonitorConfig)


def dump_runtime_config(config: RuntimeConfig | None = None) -> str:
    active = config or RuntimeConfig()
    payload = {
        "identity": {
            "fallback_strategy": active.identity.fallback_strategy,
            "openclaw_gateway_url": active.identity.openclaw_gateway_url,
            "gateway_bearer_token": active.identity.gateway_bearer_token,
            "session_key": active.identity.session_key,
            "thinking": active.identity.thinking,
            "provider": active.identity.provider,
            "model": active.identity.model,
            "auth_profile_id": active.identity.auth_profile_id,
            "timeout_ms": active.identity.timeout_ms,
            "max_tokens": active.identity.max_tokens,
        },
        "system": {
            "heartbeat_interval_sec": active.system.heartbeat_interval_sec,
            "max_retry_count": active.system.max_retry_count,
        },
        "router": {
            "strategy": active.router.strategy,
            "capability_weight": active.router.capability_weight,
            "load_weight": active.router.load_weight,
            "priority_weight": active.router.priority_weight,
        },
        "monitor": {
            "auto_restart_on_crash": active.monitor.auto_restart_on_crash,
            "heartbeat_timeout_sec": active.monitor.heartbeat_timeout_sec,
            "max_cpu_percent": active.monitor.max_cpu_percent,
            "max_memory_percent": active.monitor.max_memory_percent,
            "max_consecutive_errors": active.monitor.max_consecutive_errors,
        },
    }
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)


def load_runtime_config(path: str | Path | None = None) -> RuntimeConfig:
    config = RuntimeConfig()
    if not path:
        return config

    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}

    identity = payload.get("identity", {})
    system = payload.get("system", {})
    router = payload.get("router", {})
    monitor = payload.get("monitor", {})

    return RuntimeConfig(
        identity=IdentityConfig(
            fallback_strategy=identity.get("fallback_strategy", config.identity.fallback_strategy),
            openclaw_gateway_url=identity.get(
                "openclaw_gateway_url",
                config.identity.openclaw_gateway_url,
            ),
            gateway_bearer_token=identity.get("gateway_bearer_token")
            or os.getenv("OPENCLAW_GATEWAY_TOKEN")
            or os.getenv("OPENCLAW_GATEWAY_PASSWORD")
            or config.identity.gateway_bearer_token,
            session_key=identity.get("session_key", config.identity.session_key),
            thinking=identity.get("thinking", config.identity.thinking),
            provider=identity.get("provider", config.identity.provider),
            model=identity.get("model", config.identity.model),
            auth_profile_id=identity.get("auth_profile_id", config.identity.auth_profile_id),
            timeout_ms=identity.get("timeout_ms", config.identity.timeout_ms),
            max_tokens=identity.get("max_tokens", config.identity.max_tokens),
        ),
        system=SystemConfig(
            heartbeat_interval_sec=system.get("heartbeat_interval_sec", config.system.heartbeat_interval_sec),
            max_retry_count=system.get("max_retry_count", config.system.max_retry_count),
        ),
        router=RouterConfig(
            strategy=router.get("strategy", config.router.strategy),
            capability_weight=router.get("capability_weight", config.router.capability_weight),
            load_weight=router.get("load_weight", config.router.load_weight),
            priority_weight=router.get("priority_weight", config.router.priority_weight),
        ),
        monitor=MonitorConfig(
            auto_restart_on_crash=monitor.get("auto_restart_on_crash", config.monitor.auto_restart_on_crash),
            heartbeat_timeout_sec=monitor.get("heartbeat_timeout_sec", config.monitor.heartbeat_timeout_sec),
            max_cpu_percent=monitor.get("max_cpu_percent", config.monitor.max_cpu_percent),
            max_memory_percent=monitor.get("max_memory_percent", config.monitor.max_memory_percent),
            max_consecutive_errors=monitor.get(
                "max_consecutive_errors",
                config.monitor.max_consecutive_errors,
            ),
        ),
    )
