from datetime import UTC, datetime, timedelta

from openclaw_smart_agent.models import AgentProfile, AgentStatus, TaskStatus


def test_monitor_marks_agent_unhealthy_and_requeues_tasks(tmp_path):
    from openclaw_smart_agent.monitor import HealthMonitor, MonitorThresholds
    from openclaw_smart_agent.recovery import RecoveryManager
    from openclaw_smart_agent.registry import AgentRegistry
    from openclaw_smart_agent.router import TaskRouter
    from openclaw_smart_agent.store import StateStore

    store = StateStore(tmp_path / "smart-agent.db")
    registry = AgentRegistry(store)
    recovery = RecoveryManager(registry)
    monitor = HealthMonitor(
        registry,
        recovery,
        thresholds=MonitorThresholds(max_cpu_percent=90.0, max_memory_percent=90.0, max_consecutive_errors=3),
    )

    agent = registry.register(
        AgentProfile(
            identity="Python开发",
            role="python-developer",
            skills=["python"],
            tools=["shell"],
            system_prompt="Python",
            resource_weight=0.8,
        )
    )
    registry.update_status(agent.agent_id, AgentStatus.HEALTHY)

    router = TaskRouter(registry)
    task = router.publish_task("Fix bug", ["python"], priority=5)
    registry.start_task(task.task_id)

    monitor.record_heartbeat(agent.agent_id, cpu_percent=95.0, memory_percent=91.0, consecutive_errors=4)
    monitor.evaluate()

    refreshed = registry.get_agent(agent.agent_id)
    retried_task = registry.get_task(task.task_id)

    assert refreshed is not None
    assert refreshed.status == AgentStatus.UNHEALTHY
    assert retried_task is not None
    assert retried_task.status == TaskStatus.REQUEUED
    assert retried_task.assigned_agent_id is None


def test_monitor_marks_agent_degraded_after_heartbeat_timeout(tmp_path):
    from openclaw_smart_agent.monitor import HealthMonitor, MonitorThresholds
    from openclaw_smart_agent.recovery import RecoveryManager
    from openclaw_smart_agent.registry import AgentRegistry
    from openclaw_smart_agent.store import StateStore

    store = StateStore(tmp_path / "smart-agent.db")
    registry = AgentRegistry(store)
    recovery = RecoveryManager(registry)
    monitor = HealthMonitor(
        registry,
        recovery,
        thresholds=MonitorThresholds(heartbeat_timeout_sec=10),
    )

    agent = registry.register(
        AgentProfile(
            identity="数据分析",
            role="data-analyst",
            skills=["analysis"],
            tools=["shell"],
            system_prompt="Data",
            resource_weight=0.6,
        )
    )
    registry.update_status(agent.agent_id, AgentStatus.HEALTHY)

    stale_time = datetime.now(UTC) - timedelta(seconds=30)
    monitor.record_heartbeat(
        agent.agent_id,
        cpu_percent=20.0,
        memory_percent=22.0,
        consecutive_errors=0,
        received_at=stale_time,
    )
    monitor.evaluate(now=datetime.now(UTC))

    refreshed = registry.get_agent(agent.agent_id)

    assert refreshed is not None
    assert refreshed.status == AgentStatus.DEGRADED
