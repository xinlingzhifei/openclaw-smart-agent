from openclaw_smart_agent.models import AgentProfile, AgentStatus, TaskStatus


def test_router_prefers_best_skill_match_with_lower_load(tmp_path):
    from openclaw_smart_agent.registry import AgentRegistry
    from openclaw_smart_agent.router import TaskRouter
    from openclaw_smart_agent.store import StateStore

    store = StateStore(tmp_path / "smart-agent.db")
    registry = AgentRegistry(store)

    first = registry.register(
        AgentProfile(
            identity="Python开发",
            role="python-developer",
            skills=["python", "api"],
            tools=["shell"],
            system_prompt="Python",
            resource_weight=0.8,
        )
    )
    second = registry.register(
        AgentProfile(
            identity="Python测试工程师",
            role="python-tester",
            skills=["python", "testing"],
            tools=["shell"],
            system_prompt="Python testing",
            resource_weight=0.7,
        )
    )

    registry.update_status(first.agent_id, AgentStatus.HEALTHY)
    registry.update_status(second.agent_id, AgentStatus.HEALTHY)
    registry.update_load(first.agent_id, running_tasks=3, cpu_percent=45.0, memory_percent=35.0)
    registry.update_load(second.agent_id, running_tasks=1, cpu_percent=12.0, memory_percent=10.0)

    router = TaskRouter(registry)
    task = router.publish_task("Implement parser", ["python"], priority=5)

    assert task.assigned_agent_id == second.agent_id
    assert task.status == TaskStatus.ASSIGNED
    assert registry.get_task(task.task_id).status == TaskStatus.ASSIGNED
