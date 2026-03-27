from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class AgentStatus(StrEnum):
    STARTING = "starting"
    HEALTHY = "healthy"
    BUSY = "busy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    RESTARTING = "restarting"
    OFFLINE = "offline"


class TaskStatus(StrEnum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUEUED = "requeued"


@dataclass(slots=True)
class AgentProfile:
    identity: str
    role: str
    skills: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    system_prompt: str = ""
    resource_weight: float = 1.0


@dataclass(slots=True)
class RegisteredAgent(AgentProfile):
    agent_id: str = ""
    status: AgentStatus = AgentStatus.STARTING
    running_tasks: int = 0
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    consecutive_errors: int = 0
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


@dataclass(slots=True)
class TaskRecord:
    task_id: str
    task_desc: str
    required_skills: list[str] = field(default_factory=list)
    priority: int = 1
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent_id: str | None = None
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
