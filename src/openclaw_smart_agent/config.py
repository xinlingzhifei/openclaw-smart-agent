from dataclasses import dataclass, field
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
    system: SystemConfig = field(default_factory=SystemConfig)
    router: RouterConfig = field(default_factory=RouterConfig)
    monitor: MonitorConfig = field(default_factory=MonitorConfig)


def dump_runtime_config(config: RuntimeConfig | None = None) -> str:
    active = config or RuntimeConfig()
    payload = {
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

    system = payload.get("system", {})
    router = payload.get("router", {})
    monitor = payload.get("monitor", {})

    return RuntimeConfig(
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
