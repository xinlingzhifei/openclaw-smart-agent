from openclaw_smart_agent.models import AgentProfile, AgentStatus, TaskStatus
from openclaw_smart_agent.registry import AgentRegistry
from openclaw_smart_agent.router import TaskRouter
from openclaw_smart_agent.store import StateStore


def _register_agent(
    registry: AgentRegistry,
    *,
    identity: str,
    role: str,
    skills: list[str],
    resource_weight: float = 0.5,
    status: AgentStatus = AgentStatus.HEALTHY,
):
    agent = registry.register(
        AgentProfile(
            identity=identity,
            role=role,
            skills=skills,
            tools=["shell"],
            system_prompt=f"You are {role}.",
            resource_weight=resource_weight,
        )
    )
    return registry.update_status(agent.agent_id, status)


def test_router_prefers_higher_partial_skill_match(tmp_path):
    store = StateStore(tmp_path / "smart-agent.db")
    registry = AgentRegistry(store)
    router = TaskRouter(registry)

    strong_partial = _register_agent(
        registry,
        identity="Java API开发",
        role="java-api-developer",
        skills=["java", "api"],
        resource_weight=0.6,
    )
    weak_partial = _register_agent(
        registry,
        identity="Java维护",
        role="java-maintainer",
        skills=["java"],
        resource_weight=0.6,
    )

    task = router.publish_task(
        "Build backend endpoint",
        ["java", "api", "backend"],
        priority=5,
    )

    assert task.status == TaskStatus.ASSIGNED
    assert task.assigned_agent_id == strong_partial.agent_id
    assert task.assigned_agent_id != weak_partial.agent_id


def test_router_prefers_healthy_agent_for_routine_priority(tmp_path):
    store = StateStore(tmp_path / "smart-agent.db")
    registry = AgentRegistry(store)
    router = TaskRouter(registry)

    busy_agent = _register_agent(
        registry,
        identity="Busy Python开发",
        role="busy-python",
        skills=["python", "api"],
        resource_weight=0.9,
        status=AgentStatus.BUSY,
    )
    healthy_agent = _register_agent(
        registry,
        identity="Healthy Python开发",
        role="healthy-python",
        skills=["python", "api"],
        resource_weight=0.4,
        status=AgentStatus.HEALTHY,
    )

    registry.update_load(
        busy_agent.agent_id,
        running_tasks=1,
        cpu_percent=5,
        memory_percent=10,
    )
    registry.update_load(
        healthy_agent.agent_id,
        running_tasks=0,
        cpu_percent=15,
        memory_percent=20,
    )

    task = router.publish_task(
        "Routine API cleanup",
        ["python", "api"],
        priority=3,
    )

    assert task.status == TaskStatus.ASSIGNED
    assert task.assigned_agent_id == healthy_agent.agent_id
    assert task.assigned_agent_id != busy_agent.agent_id


def test_router_dispatches_high_priority_pending_task_first(tmp_path):
    store = StateStore(tmp_path / "smart-agent.db")
    registry = AgentRegistry(store)
    router = TaskRouter(registry)

    agent = _register_agent(
        registry,
        identity="Python开发",
        role="python-developer",
        skills=["python", "api"],
        resource_weight=0.6,
    )

    low_priority = registry.create_task("Low priority task", ["python"], priority=2)
    high_priority = registry.create_task("High priority task", ["python"], priority=9)

    dispatched = router.dispatch_pending_tasks()

    refreshed_high = registry.get_task(high_priority.task_id)
    refreshed_low = registry.get_task(low_priority.task_id)

    assert dispatched
    assert refreshed_high.status == TaskStatus.ASSIGNED
    assert refreshed_high.assigned_agent_id == agent.agent_id
    assert refreshed_low.status == TaskStatus.PENDING
    assert refreshed_low.assigned_agent_id is None
