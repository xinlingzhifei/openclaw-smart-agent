# Smart Agent API Reference

## Endpoints

### `POST /api/v1/agents/create`

Request:

```json
{
  "identity": "Python开发"
}
```

Response fields:

- `profile`: enhanced role profile from templates
- `agent`: registered agent record with `agent_id`, `status`, skills, load, and timestamps

### `GET /api/v1/agents/status`

Response:

```json
{
  "agents": []
}
```

Use this for registry, health, and load inspection.

### `POST /api/v1/agents/heartbeat`

Request:

```json
{
  "agent_id": "agent-xxxx",
  "cpu_percent": 20,
  "memory_percent": 25,
  "consecutive_errors": 0,
  "current_task_id": "task-xxxx"
}
```

Response fields:

- `agent.status`
- `agent.cpu_percent`
- `agent.memory_percent`
- `agent.current_task_id`
- `agent.last_heartbeat_at`

### `POST /api/v1/tasks/publish`

Request:

```json
{
  "task_desc": "Implement parser",
  "required_skills": ["python"],
  "priority": 5
}
```

Response fields:

- `task.task_id`
- `task.status`
- `task.assigned_agent_id`
- `task.required_skills`
