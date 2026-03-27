from fastapi.testclient import TestClient


def _write_template(path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_create_agent_api_returns_generated_profile(tmp_path):
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    _write_template(
        template_dir / "python-developer.yaml",
        """
role: python-developer
keywords:
  - Python开发
  - python
skills:
  - python
  - api
tools:
  - shell
system_prompt: You are a Python implementation specialist.
resource_weight: 0.8
""".strip(),
    )

    from openclaw_smart_agent.api import create_app
    from openclaw_smart_agent.runtime import SmartAgentRuntime

    runtime = SmartAgentRuntime(db_path=tmp_path / "smart-agent.db", template_dir=template_dir)
    client = TestClient(create_app(runtime))

    response = client.post("/api/v1/agents/create", json={"identity": "Python开发"})

    assert response.status_code == 200
    body = response.json()
    assert body["profile"]["role"] == "python-developer"
    assert body["agent"]["status"] == "healthy"


def test_publish_task_api_assigns_best_available_agent(tmp_path):
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    _write_template(
        template_dir / "python-developer.yaml",
        """
role: python-developer
keywords:
  - Python开发
  - python
skills:
  - python
  - api
tools:
  - shell
system_prompt: You are a Python implementation specialist.
resource_weight: 0.8
""".strip(),
    )

    from openclaw_smart_agent.api import create_app
    from openclaw_smart_agent.runtime import SmartAgentRuntime

    runtime = SmartAgentRuntime(db_path=tmp_path / "smart-agent.db", template_dir=template_dir)
    client = TestClient(create_app(runtime))
    client.post("/api/v1/agents/create", json={"identity": "Python开发"})

    response = client.post(
        "/api/v1/tasks/publish",
        json={"task_desc": "Implement parser", "required_skills": ["python"], "priority": 5},
    )
    status_response = client.get("/api/v1/agents/status")

    assert response.status_code == 200
    body = response.json()
    assert body["task"]["status"] == "assigned"
    assert body["task"]["assigned_agent_id"]
    assert status_response.status_code == 200
    assert len(status_response.json()["agents"]) == 1


def test_heartbeat_api_updates_agent_health_snapshot(tmp_path):
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    _write_template(
        template_dir / "python-developer.yaml",
        """
role: python-developer
keywords:
  - Python开发
  - python
skills:
  - python
tools:
  - shell
system_prompt: You are a Python implementation specialist.
resource_weight: 0.8
""".strip(),
    )

    from openclaw_smart_agent.api import create_app
    from openclaw_smart_agent.runtime import SmartAgentRuntime

    runtime = SmartAgentRuntime(db_path=tmp_path / "smart-agent.db", template_dir=template_dir)
    client = TestClient(create_app(runtime))
    create_response = client.post("/api/v1/agents/create", json={"identity": "Python开发"})
    agent_id = create_response.json()["agent"]["agent_id"]

    response = client.post(
        "/api/v1/agents/heartbeat",
        json={
            "agent_id": agent_id,
            "cpu_percent": 22.0,
            "memory_percent": 31.0,
            "consecutive_errors": 0,
            "current_task_id": "task-demo",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["agent"]["agent_id"] == agent_id
    assert body["agent"]["last_heartbeat_at"]
    assert body["agent"]["current_task_id"] == "task-demo"
    assert body["agent"]["cpu_percent"] == 22.0


def test_create_agent_api_uses_openclaw_llm_fallback_when_configured(tmp_path):
    from openclaw_smart_agent.api import create_app
    from openclaw_smart_agent.config import IdentityConfig, RuntimeConfig
    from openclaw_smart_agent.models import AgentProfile
    from openclaw_smart_agent.runtime import SmartAgentRuntime

    def fake_llm(identity: str, profile: AgentProfile) -> AgentProfile:
        assert identity == "测试工程师"
        assert profile.role == "generalist"
        return AgentProfile(
            identity=identity,
            role="test-engineer",
            skills=["testing", "qa"],
            tools=["shell"],
            system_prompt="You are a testing specialist.",
            resource_weight=0.7,
        )

    runtime = SmartAgentRuntime(
        db_path=tmp_path / "smart-agent.db",
        template_dir=tmp_path / "templates",
        config=RuntimeConfig(
            identity=IdentityConfig(fallback_strategy="openclaw_llm"),
        ),
        llm_enhancer=fake_llm,
    )
    client = TestClient(create_app(runtime))

    response = client.post("/api/v1/agents/create", json={"identity": "测试工程师"})

    assert response.status_code == 200
    body = response.json()
    assert body["profile"]["role"] == "test-engineer"
    assert body["agent"]["role"] == "test-engineer"
