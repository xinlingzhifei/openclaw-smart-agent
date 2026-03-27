from dataclasses import asdict
from pathlib import Path

from openclaw_smart_agent.config import RuntimeConfig
from openclaw_smart_agent.identity import IdentityEnhancer
from openclaw_smart_agent.models import AgentProfile, AgentStatus, RegisteredAgent, TaskRecord
from openclaw_smart_agent.monitor import HealthMonitor, MonitorThresholds
from openclaw_smart_agent.recovery import RecoveryManager
from openclaw_smart_agent.registry import AgentRegistry
from openclaw_smart_agent.router import RouterWeights, TaskRouter
from openclaw_smart_agent.store import StateStore


class SmartAgentRuntime:
    def __init__(
        self,
        *,
        db_path: str | Path,
        template_dir: str | Path | None = None,
        config: RuntimeConfig | None = None,
    ) -> None:
        self.config = config or RuntimeConfig()
        self.template_dir = Path(template_dir) if template_dir else self.default_template_dir()
        self.store = StateStore(db_path)
        self.identity = IdentityEnhancer(template_dir=self.template_dir)
        self.registry = AgentRegistry(self.store)
        self.router = TaskRouter(
            self.registry,
            weights=RouterWeights(
                capability=self.config.router.capability_weight,
                load=self.config.router.load_weight,
                priority=self.config.router.priority_weight,
            ),
        )
        self.recovery = RecoveryManager(self.registry, max_retry_count=self.config.system.max_retry_count)
        self.monitor = HealthMonitor(
            self.registry,
            self.recovery,
            thresholds=MonitorThresholds(
                heartbeat_timeout_sec=self.config.monitor.heartbeat_timeout_sec,
                max_cpu_percent=self.config.monitor.max_cpu_percent,
                max_memory_percent=self.config.monitor.max_memory_percent,
                max_consecutive_errors=self.config.monitor.max_consecutive_errors,
            ),
        )

    @staticmethod
    def default_template_dir() -> Path:
        return Path(__file__).with_name("templates")

    def create_agent(self, identity: str) -> tuple[AgentProfile, RegisteredAgent]:
        profile = self.identity.enhance(identity)
        agent = self.registry.register(profile)
        if agent.status == AgentStatus.STARTING:
            agent = self.registry.update_status(agent.agent_id, AgentStatus.HEALTHY)
        return profile, agent

    def get_agents_status(self) -> list[RegisteredAgent]:
        return self.registry.list_agents()

    def publish_task(self, task_desc: str, required_skills: list[str], priority: int = 1) -> TaskRecord:
        return self.router.publish_task(task_desc, required_skills, priority)

    @staticmethod
    def serialize_profile(profile: AgentProfile) -> dict:
        return asdict(profile)

    @staticmethod
    def serialize_agent(agent: RegisteredAgent) -> dict:
        payload = asdict(agent)
        payload["status"] = agent.status.value
        return payload

    @staticmethod
    def serialize_task(task: TaskRecord) -> dict:
        payload = asdict(task)
        payload["status"] = task.status.value
        return payload
