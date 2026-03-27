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
