from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ci_workflow_and_readme_badge_exist():
    workflow_path = ROOT / ".github" / "workflows" / "ci.yml"
    readme_path = ROOT / "README.md"

    assert workflow_path.exists()

    workflow_text = workflow_path.read_text(encoding="utf-8")
    assert "push:" in workflow_text
    assert "pull_request:" in workflow_text
    assert "FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true" in workflow_text
    assert "actions/checkout@v6" in workflow_text
    assert "actions/setup-python@v6" in workflow_text
    assert "actions/setup-node@v6" in workflow_text
    assert "python -m pytest tests -q" in workflow_text
    assert "npm ci" in workflow_text
    assert "npm run check" in workflow_text

    readme_text = readme_path.read_text(encoding="utf-8")
    assert "actions/workflows/ci.yml/badge.svg?branch=main" in readme_text
    assert "/actions/workflows/ci.yml" in readme_text


def test_plugin_exposes_heartbeat_tool():
    plugin_entry_path = ROOT / "plugin" / "src" / "index.ts"
    plugin_text = plugin_entry_path.read_text(encoding="utf-8")

    assert "smart_agent_heartbeat" in plugin_text
    assert "/api/v1/agents/heartbeat" in plugin_text


def test_plugin_registers_runtime_autostart_service_and_schema():
    plugin_entry_text = (ROOT / "plugin" / "src" / "index.ts").read_text(encoding="utf-8")
    plugin_manifest_text = (ROOT / "plugin" / "openclaw.plugin.json").read_text(encoding="utf-8")

    assert "api.registerService" in plugin_entry_text
    assert "runtime-autostart" in plugin_entry_text
    assert "resolveRuntimeAutostartOptions" in plugin_entry_text
    assert "autoStartRuntime" in plugin_manifest_text
    assert "runtimeConfigPath" in plugin_manifest_text


def test_readme_links_integration_and_heartbeat_flow():
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
    integration_guide_path = ROOT / "docs" / "openclaw-integration.md"

    assert integration_guide_path.exists()
    assert "docs/openclaw-integration.md" in readme_text
    assert "smart_agent_heartbeat" in readme_text
    assert "auto-start the runtime" in readme_text


def test_template_guide_is_referenced_by_readme_and_skill():
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
    skill_text = (ROOT / "skills" / "openclaw-smart-agent" / "SKILL.md").read_text(encoding="utf-8")
    template_guide_path = ROOT / "docs" / "template-guide.md"

    assert template_guide_path.exists()
    assert "docs/template-guide.md" in readme_text
    assert "template" in skill_text.casefold()


def test_runtime_verification_script_is_documented():
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
    integration_text = (ROOT / "docs" / "openclaw-integration.md").read_text(encoding="utf-8")
    verification_script_path = ROOT / "scripts" / "verify_runtime.py"

    assert verification_script_path.exists()
    assert "verify_runtime.py" in readme_text
    assert "verify_runtime.py" in integration_text
    assert "auto-start" in integration_text


def test_docs_explain_openclaw_llm_identity_fallback():
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
    integration_text = (ROOT / "docs" / "openclaw-integration.md").read_text(encoding="utf-8")
    skill_text = (ROOT / "skills" / "openclaw-smart-agent" / "SKILL.md").read_text(encoding="utf-8")
    api_text = (ROOT / "skills" / "openclaw-smart-agent" / "references" / "api.md").read_text(encoding="utf-8")
    config_text = (ROOT / "config" / "config.example.yaml").read_text(encoding="utf-8")

    assert "llm-task" in readme_text
    assert "openclaw_llm" in readme_text
    assert "llm-task" in integration_text
    assert "identity" in skill_text.casefold()
    assert "fallback_strategy" in config_text
    assert "openclaw_llm" in api_text
