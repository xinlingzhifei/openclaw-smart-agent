import json
import sqlite3
from pathlib import Path

from openclaw_smart_agent.models import AgentStatus, RegisteredAgent, TaskRecord, TaskStatus


class StateStore:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                identity TEXT NOT NULL,
                role TEXT NOT NULL,
                skills TEXT NOT NULL,
                tools TEXT NOT NULL,
                system_prompt TEXT NOT NULL,
                resource_weight REAL NOT NULL,
                status TEXT NOT NULL,
                running_tasks INTEGER NOT NULL,
                cpu_percent REAL NOT NULL,
                memory_percent REAL NOT NULL,
                consecutive_errors INTEGER NOT NULL,
                current_task_id TEXT,
                last_heartbeat_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(identity, role)
            );

            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                task_desc TEXT NOT NULL,
                required_skills TEXT NOT NULL,
                priority INTEGER NOT NULL,
                status TEXT NOT NULL,
                assigned_agent_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        self._ensure_agent_columns()
        self.connection.commit()

    def _ensure_agent_columns(self) -> None:
        columns = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(agents)").fetchall()
        }
        if "current_task_id" not in columns:
            self.connection.execute("ALTER TABLE agents ADD COLUMN current_task_id TEXT")
        if "last_heartbeat_at" not in columns:
            self.connection.execute("ALTER TABLE agents ADD COLUMN last_heartbeat_at TEXT")

    def get_agent(self, agent_id: str) -> RegisteredAgent | None:
        row = self.connection.execute(
            "SELECT * FROM agents WHERE agent_id = ?",
            (agent_id,),
        ).fetchone()
        return self._row_to_agent(row) if row else None

    def find_agent_by_identity(self, identity: str, role: str) -> RegisteredAgent | None:
        row = self.connection.execute(
            "SELECT * FROM agents WHERE identity = ? AND role = ?",
            (identity, role),
        ).fetchone()
        return self._row_to_agent(row) if row else None

    def list_agents(self) -> list[RegisteredAgent]:
        rows = self.connection.execute("SELECT * FROM agents").fetchall()
        return [self._row_to_agent(row) for row in rows]

    def save_agent(self, agent: RegisteredAgent) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO agents (
                agent_id, identity, role, skills, tools, system_prompt,
                resource_weight, status, running_tasks, cpu_percent,
                memory_percent, consecutive_errors, current_task_id,
                last_heartbeat_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                agent.agent_id,
                agent.identity,
                agent.role,
                json.dumps(agent.skills),
                json.dumps(agent.tools),
                agent.system_prompt,
                agent.resource_weight,
                agent.status.value,
                agent.running_tasks,
                agent.cpu_percent,
                agent.memory_percent,
                agent.consecutive_errors,
                agent.current_task_id,
                agent.last_heartbeat_at,
                agent.created_at,
                agent.updated_at,
            ),
        )
        self.connection.commit()

    def get_task(self, task_id: str) -> TaskRecord | None:
        row = self.connection.execute(
            "SELECT * FROM tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        return self._row_to_task(row) if row else None

    def save_task(self, task: TaskRecord) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO tasks (
                task_id, task_desc, required_skills, priority, status,
                assigned_agent_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task.task_id,
                task.task_desc,
                json.dumps(task.required_skills),
                task.priority,
                task.status.value,
                task.assigned_agent_id,
                task.created_at,
                task.updated_at,
            ),
        )
        self.connection.commit()

    def list_tasks(self) -> list[TaskRecord]:
        rows = self.connection.execute("SELECT * FROM tasks").fetchall()
        return [self._row_to_task(row) for row in rows]

    @staticmethod
    def _row_to_agent(row: sqlite3.Row) -> RegisteredAgent:
        return RegisteredAgent(
            agent_id=row["agent_id"],
            identity=row["identity"],
            role=row["role"],
            skills=json.loads(row["skills"]),
            tools=json.loads(row["tools"]),
            system_prompt=row["system_prompt"],
            resource_weight=row["resource_weight"],
            status=AgentStatus(row["status"]),
            running_tasks=row["running_tasks"],
            cpu_percent=row["cpu_percent"],
            memory_percent=row["memory_percent"],
            consecutive_errors=row["consecutive_errors"],
            current_task_id=row["current_task_id"],
            last_heartbeat_at=row["last_heartbeat_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_task(row: sqlite3.Row) -> TaskRecord:
        return TaskRecord(
            task_id=row["task_id"],
            task_desc=row["task_desc"],
            required_skills=json.loads(row["required_skills"]),
            priority=row["priority"],
            status=TaskStatus(row["status"]),
            assigned_agent_id=row["assigned_agent_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
