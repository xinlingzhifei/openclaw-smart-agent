from openclaw_smart_agent.models import AgentProfile


def test_registry_registers_and_persists_agents(tmp_path):
    from openclaw_smart_agent.registry import AgentRegistry
    from openclaw_smart_agent.store import StateStore

    db_path = tmp_path / "smart-agent.db"
    store = StateStore(db_path)
    registry = AgentRegistry(store)

    profile = AgentProfile(
        identity="Python开发",
        role="python-developer",
        skills=["python", "testing"],
        tools=["shell"],
        system_prompt="You are a Python specialist.",
        resource_weight=0.8,
    )

    first = registry.register(profile)
    second = registry.register(profile)
    reloaded = AgentRegistry(StateStore(db_path))
    restored = reloaded.get_agent(first.agent_id)

    assert second.agent_id == first.agent_id
    assert restored is not None
    assert restored.role == "python-developer"
    assert restored.skills == ["python", "testing"]
