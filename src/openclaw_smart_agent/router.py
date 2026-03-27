from dataclasses import dataclass

from openclaw_smart_agent.models import RegisteredAgent, TaskRecord
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
        candidates = self.registry.eligible_agents(required_skills)
        if not candidates:
            return task

        best_agent = max(candidates, key=lambda agent: self._score(agent, required_skills, priority))
        return self.registry.assign_task(task.task_id, best_agent.agent_id)

    def _score(self, agent: RegisteredAgent, required_skills: list[str], priority: int) -> float:
        required = {skill.casefold() for skill in required_skills} or {""}
        agent_skills = {skill.casefold() for skill in agent.skills}
        capability_match = len(required & agent_skills) / len(required)
        load_penalty = min(
            1.0,
            (agent.running_tasks / 5.0 + agent.cpu_percent / 100.0 + agent.memory_percent / 100.0) / 3.0,
        )
        low_load = 1.0 - load_penalty
        priority_bias = min(priority / 10.0, 1.0) * agent.resource_weight
        return (
            capability_match * self.weights.capability
            + low_load * self.weights.load
            + priority_bias * self.weights.priority
        )
