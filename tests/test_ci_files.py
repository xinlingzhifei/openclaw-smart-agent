from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ci_workflow_and_readme_badge_exist():
    workflow_path = ROOT / ".github" / "workflows" / "ci.yml"
    readme_path = ROOT / "README.md"

    assert workflow_path.exists()

    workflow_text = workflow_path.read_text(encoding="utf-8")
    assert "push:" in workflow_text
    assert "pull_request:" in workflow_text
    assert "python -m pytest tests -q" in workflow_text
    assert "npm ci" in workflow_text
    assert "npm run check" in workflow_text

    readme_text = readme_path.read_text(encoding="utf-8")
    assert "actions/workflows/ci.yml/badge.svg?branch=main" in readme_text
    assert "/actions/workflows/ci.yml" in readme_text
