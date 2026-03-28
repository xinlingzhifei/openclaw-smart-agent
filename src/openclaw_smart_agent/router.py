from dataclasses import dataclass

from openclaw_smart_agent.models import AgentStatus, RegisteredAgent, TaskRecord
from openclaw_smart_agent.registry import AgentRegistry


@dataclass(slots=True)
class RouterWeights:
    capability: float = 0.5
    load: float = 0.3
    priority: float = 0.2


class TaskRouter:
    def __init__(self, registry: AgentRegistry, weights: RouterWeights | None = None) -> None:
        self.registry = registry
        self.weights = weights or RouterWeights()

    def publish_task(self, task_desc: str, required_skills: list[str], priority: int = 1) -> TaskRecord:
        task = self.registry.create_task(task_desc, required_skills, priority)
        self.dispatch_pending_tasks()
        return self.registry.get_task(task.task_id) or task

    def dispatch_pending_tasks(self) -> list[TaskRecord]:
        dispatched: list[TaskRecord] = []
        for task in self.registry.list_dispatchable_tasks():
            candidates = self.registry.eligible_agents(
                task.required_skills,
                allowed_statuses=self._allowed_statuses(task.priority),
            )
            if not candidates:
                continue

            best_agent = max(
                candidates,
                key=lambda agent: self._score(agent, task.required_skills, task.priority),
            )
            dispatched.append(self.registry.assign_task(task.task_id, best_agent.agent_id))
        return dispatched

    def _score(self, agent: RegisteredAgent, required_skills: list[str], priority: int) -> float:
        required = self._normalize_skills(required_skills)
        agent_skills = self._normalize_skills(agent.skills)
        capability_match = len(required & agent_skills) / len(required) if required else 1.0
        load_penalty = min(
            1.0,
            (agent.running_tasks / 5.0 + agent.cpu_percent / 100.0 + agent.memory_percent / 100.0) / 3.0,
        )
        low_load = 1.0 - load_penalty
        urgency = min(max(priority, 1) / 10.0, 1.0)
        capability_weight = min(0.75, self.weights.capability + urgency * 0.2)
        load_weight = max(0.15, self.weights.load - urgency * 0.1)
        priority_weight = max(0.05, 1.0 - capability_weight - load_weight)
        return (
            capability_match * capability_weight
            + low_load * load_weight
            + agent.resource_weight * priority_weight
        )

    @staticmethod
    def _allowed_statuses(priority: int) -> set[AgentStatus]:
        if priority >= 8:
            return {AgentStatus.HEALTHY, AgentStatus.BUSY}
        return {AgentStatus.HEALTHY}

    @staticmethod
    def _normalize_skills(skills: list[str]) -> set[str]:
        return {
            skill.strip().casefold()
            for skill in skills
            if isinstance(skill, str) and skill.strip()
        }
