from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

from openclaw_smart_agent.config import load_runtime_config
from openclaw_smart_agent.runtime import SmartAgentRuntime


class CreateAgentRequest(BaseModel):
    identity: str = Field(min_length=1)


class PublishTaskRequest(BaseModel):
    task_desc: str = Field(min_length=1)
    required_skills: list[str] = Field(default_factory=list)
    priority: int = 1


def create_app(runtime: SmartAgentRuntime | None = None) -> FastAPI:
    app = FastAPI(title="OpenClaw Smart Agent", version="0.1.0")
    active_runtime = runtime or SmartAgentRuntime(
        db_path=Path("data") / "smart-agent.db",
        config=load_runtime_config(Path("config") / "config.yaml") if Path("config/config.yaml").exists() else None,
    )

    @app.post("/api/v1/agents/create")
    def create_agent(payload: CreateAgentRequest) -> dict:
        profile, agent = active_runtime.create_agent(payload.identity)
        return {
            "profile": active_runtime.serialize_profile(profile),
            "agent": active_runtime.serialize_agent(agent),
        }

    @app.get("/api/v1/agents/status")
    def get_agent_status() -> dict:
        return {
            "agents": [active_runtime.serialize_agent(agent) for agent in active_runtime.get_agents_status()]
        }

    @app.post("/api/v1/tasks/publish")
    def publish_task(payload: PublishTaskRequest) -> dict:
        task = active_runtime.publish_task(
            payload.task_desc,
            payload.required_skills,
            payload.priority,
        )
        return {"task": active_runtime.serialize_task(task)}

    return app
