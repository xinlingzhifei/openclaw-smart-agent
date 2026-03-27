from dataclasses import dataclass
from datetime import UTC, datetime

from openclaw_smart_agent.recovery import RecoveryManager
from openclaw_smart_agent.registry import AgentRegistry


@dataclass(slots=True)
class MonitorThresholds:
    heartbeat_timeout_sec: int = 15
    max_cpu_percent: float = 90.0
    max_memory_percent: float = 90.0
    max_consecutive_errors: int = 3


@dataclass(slots=True)
class HeartbeatSnapshot:
    agent_id: str
    cpu_percent: float
    memory_percent: float
    consecutive_errors: int
    received_at: datetime


class HealthMonitor:
    def __init__(
        self,
        registry: AgentRegistry,
        recovery: RecoveryManager,
        thresholds: MonitorThresholds | None = None,
    ) -> None:
        self.registry = registry
        self.recovery = recovery
        self.thresholds = thresholds or MonitorThresholds()
        self.heartbeats: dict[str, HeartbeatSnapshot] = {}

    def record_heartbeat(
        self,
        agent_id: str,
        *,
        cpu_percent: float,
        memory_percent: float,
        consecutive_errors: int = 0,
        current_task_id: str | None = None,
        received_at: datetime | None = None,
    ) -> HeartbeatSnapshot:
        snapshot = HeartbeatSnapshot(
            agent_id=agent_id,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            consecutive_errors=consecutive_errors,
            received_at=received_at or datetime.now(UTC),
        )
        self.heartbeats[agent_id] = snapshot
        self.registry.update_load(
            agent_id,
            running_tasks=self.registry.get_agent(agent_id).running_tasks,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            consecutive_errors=consecutive_errors,
            current_task_id=current_task_id,
            last_heartbeat_at=snapshot.received_at.isoformat(),
        )
        return snapshot

    def evaluate(self, now: datetime | None = None) -> None:
        reference_time = now or datetime.now(UTC)
        for agent in self.registry.list_agents():
            heartbeat = self.heartbeats.get(agent.agent_id)
            if heartbeat is None:
                continue

            age_seconds = (reference_time - heartbeat.received_at).total_seconds()
            if age_seconds > self.thresholds.heartbeat_timeout_sec:
                self.recovery.mark_degraded(agent.agent_id)
                continue

            if (
                heartbeat.cpu_percent >= self.thresholds.max_cpu_percent
                or heartbeat.memory_percent >= self.thresholds.max_memory_percent
                or heartbeat.consecutive_errors > self.thresholds.max_consecutive_errors
            ):
                self.recovery.handle_unhealthy(agent.agent_id)
