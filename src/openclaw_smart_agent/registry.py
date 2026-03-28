from uuid import uuid4

from openclaw_smart_agent.models import AgentProfile, AgentStatus, RegisteredAgent, TaskRecord, TaskStatus, utc_now
from openclaw_smart_agent.store import StateStore


class AgentRegistry:
    def __init__(self, store: StateStore) -> None:
        self.store = store

    def register(self, profile: AgentProfile) -> RegisteredAgent:
        existing = self.store.find_agent_by_identity(profile.identity, profile.role)
        if existing:
            return existing

        now = utc_now()
        agent = RegisteredAgent(
            agent_id=f"agent-{uuid4().hex[:12]}",
            identity=profile.identity,
            role=profile.role,
            skills=list(profile.skills),
            tools=list(profile.tools),
            system_prompt=profile.system_prompt,
            resource_weight=profile.resource_weight,
            status=AgentStatus.STARTING,
            created_at=now,
            updated_at=now,
        )
        self.store.save_agent(agent)
        return agent

    def get_agent(self, agent_id: str) -> RegisteredAgent | None:
        return self.store.get_agent(agent_id)

    def list_agents(self) -> list[RegisteredAgent]:
        return self.store.list_agents()

    def eligible_agents(
        self,
        required_skills: list[str],
        *,
        allowed_statuses: set[AgentStatus] | None = None,
    ) -> list[RegisteredAgent]:
        candidates: list[RegisteredAgent] = []
        required = self._normalize_skills(required_skills)
        active_statuses = allowed_statuses or {AgentStatus.HEALTHY, AgentStatus.BUSY}
        for agent in self.store.list_agents():
            if agent.status not in active_statuses:
                continue
            agent_skills = self._normalize_skills(agent.skills)
            if not required or required & agent_skills:
                candidates.append(agent)
        return candidates

    def list_dispatchable_tasks(self) -> list[TaskRecord]:
        dispatchable = [
            task
            for task in self.store.list_tasks()
            if task.status in {TaskStatus.PENDING, TaskStatus.REQUEUED}
        ]
        return sorted(
            dispatchable,
            key=lambda task: (-task.priority, task.created_at, task.task_id),
        )

    def update_status(self, agent_id: str, status: AgentStatus) -> RegisteredAgent:
        agent = self._require_agent(agent_id)
        agent.status = status
        agent.updated_at = utc_now()
        self.store.save_agent(agent)
        return agent

    def update_load(
        self,
        agent_id: str,
        *,
        running_tasks: int,
        cpu_percent: float,
        memory_percent: float,
        consecutive_errors: int = 0,
        current_task_id: str | None = None,
        last_heartbeat_at: str | None = None,
    ) -> RegisteredAgent:
        agent = self._require_agent(agent_id)
        agent.running_tasks = running_tasks
        agent.cpu_percent = cpu_percent
        agent.memory_percent = memory_percent
        agent.consecutive_errors = consecutive_errors
        agent.current_task_id = current_task_id
        agent.last_heartbeat_at = last_heartbeat_at
        agent.updated_at = utc_now()
        self.store.save_agent(agent)
        return agent

    def create_task(self, task_desc: str, required_skills: list[str], priority: int = 1) -> TaskRecord:
        now = utc_now()
        task = TaskRecord(
            task_id=f"task-{uuid4().hex[:12]}",
            task_desc=task_desc,
            required_skills=list(required_skills),
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        self.store.save_task(task)
        return task

    def assign_task(self, task_id: str, agent_id: str) -> TaskRecord:
        task = self._require_task(task_id)
        task.assigned_agent_id = agent_id
        task.status = TaskStatus.ASSIGNED
        task.updated_at = utc_now()
        self.store.save_task(task)

        agent = self._require_agent(agent_id)
        agent.running_tasks += 1
        if agent.status == AgentStatus.HEALTHY:
            agent.status = AgentStatus.BUSY
        agent.updated_at = utc_now()
        self.store.save_agent(agent)
        return task

    def get_task(self, task_id: str) -> TaskRecord | None:
        return self.store.get_task(task_id)

    def start_task(self, task_id: str) -> TaskRecord:
        task = self._require_task(task_id)
        if not task.assigned_agent_id:
            raise ValueError(f"Task {task_id} is not assigned to any agent")
        task.status = TaskStatus.RUNNING
        task.updated_at = utc_now()
        self.store.save_task(task)
        return task

    def requeue_tasks_for_agent(self, agent_id: str) -> list[TaskRecord]:
        updated_tasks: list[TaskRecord] = []
        for task in self.store.list_tasks():
            if task.assigned_agent_id != agent_id:
                continue
            if task.status not in {TaskStatus.ASSIGNED, TaskStatus.RUNNING}:
                continue
            task.assigned_agent_id = None
            task.status = TaskStatus.REQUEUED
            task.updated_at = utc_now()
            self.store.save_task(task)
            updated_tasks.append(task)

        agent = self._require_agent(agent_id)
        agent.running_tasks = 0
        agent.updated_at = utc_now()
        self.store.save_agent(agent)
        return updated_tasks

    def _require_agent(self, agent_id: str) -> RegisteredAgent:
        agent = self.store.get_agent(agent_id)
        if not agent:
            raise KeyError(f"Unknown agent: {agent_id}")
        return agent

    def _require_task(self, task_id: str) -> TaskRecord:
        task = self.store.get_task(task_id)
        if not task:
            raise KeyError(f"Unknown task: {task_id}")
        return task

    @staticmethod
    def _normalize_skills(skills: list[str]) -> set[str]:
        return {
            skill.strip().casefold()
            for skill in skills
            if isinstance(skill, str) and skill.strip()
        }
