from openclaw_smart_agent.models import AgentStatus, TaskRecord
from openclaw_smart_agent.registry import AgentRegistry


class RecoveryManager:
    def __init__(self, registry: AgentRegistry, max_retry_count: int = 3) -> None:
        self.registry = registry
        self.max_retry_count = max_retry_count
        self.retry_attempts: dict[str, int] = {}

    def mark_degraded(self, agent_id: str) -> None:
        self.registry.update_status(agent_id, AgentStatus.DEGRADED)

    def handle_unhealthy(self, agent_id: str) -> list[TaskRecord]:
        self.retry_attempts[agent_id] = self.retry_attempts.get(agent_id, 0) + 1
        self.registry.update_status(agent_id, AgentStatus.UNHEALTHY)
        return self.registry.requeue_tasks_for_agent(agent_id)
