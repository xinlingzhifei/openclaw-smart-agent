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


def test_publish_task_api_prefers_lower_load_agent_when_skills_are_equal(tmp_path):
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

    busy_agent_id = client.post("/api/v1/agents/create", json={"identity": "Senior Python开发"}).json()["agent"]["agent_id"]
    healthy_agent_id = client.post("/api/v1/agents/create", json={"identity": "Backend python engineer"}).json()["agent"]["agent_id"]

    client.post(
        "/api/v1/agents/heartbeat",
        json={
            "agent_id": busy_agent_id,
            "cpu_percent": 72.0,
            "memory_percent": 61.0,
            "consecutive_errors": 0,
            "current_task_id": "task-busy",
        },
    )
    runtime.registry.update_load(
        busy_agent_id,
        running_tasks=2,
        cpu_percent=72.0,
        memory_percent=61.0,
        consecutive_errors=0,
        current_task_id="task-busy",
    )

    client.post(
        "/api/v1/agents/heartbeat",
        json={
            "agent_id": healthy_agent_id,
            "cpu_percent": 8.0,
            "memory_percent": 15.0,
            "consecutive_errors": 0,
            "current_task_id": None,
        },
    )

    response = client.post(
        "/api/v1/tasks/publish",
        json={"task_desc": "Implement API endpoint", "required_skills": ["python", "api"], "priority": 5},
    )

    assert response.status_code == 200
    assert response.json()["task"]["assigned_agent_id"] == healthy_agent_id


def test_publish_task_api_prefers_stronger_partial_skill_match(tmp_path):
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    _write_template(
        template_dir / "java-api-developer.yaml",
        """
role: java-api-developer
keywords:
  - Java API开发
skills:
  - java
  - api
tools:
  - shell
system_prompt: You are a Java API developer.
resource_weight: 0.6
""".strip(),
    )
    _write_template(
        template_dir / "java-maintainer.yaml",
        """
role: java-maintainer
keywords:
  - Java维护
skills:
  - java
tools:
  - shell
system_prompt: You maintain Java systems.
resource_weight: 0.6
""".strip(),
    )

    from openclaw_smart_agent.api import create_app
    from openclaw_smart_agent.runtime import SmartAgentRuntime

    runtime = SmartAgentRuntime(db_path=tmp_path / "smart-agent.db", template_dir=template_dir)
    client = TestClient(create_app(runtime))

    stronger_agent_id = client.post("/api/v1/agents/create", json={"identity": "Java API开发"}).json()["agent"]["agent_id"]
    weaker_agent_id = client.post("/api/v1/agents/create", json={"identity": "Java维护"}).json()["agent"]["agent_id"]

    response = client.post(
        "/api/v1/tasks/publish",
        json={
            "task_desc": "Build backend endpoint",
            "required_skills": ["java", "api", "backend"],
            "priority": 5,
        },
    )

    assert response.status_code == 200
    assert response.json()["task"]["assigned_agent_id"] == stronger_agent_id
    assert response.json()["task"]["assigned_agent_id"] != weaker_agent_id
