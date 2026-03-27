from pathlib import Path


def _write_template(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_identity_enhancer_uses_keyword_template_match(tmp_path):
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    _write_template(
        template_dir / "python-developer.yaml",
        """
role: python-developer
keywords:
  - python
  - Python开发
skills:
  - python
  - testing
tools:
  - shell
system_prompt: You are a Python implementation specialist.
resource_weight: 0.8
""".strip(),
    )

    from openclaw_smart_agent.identity import IdentityEnhancer

    enhancer = IdentityEnhancer(template_dir=template_dir)
    profile = enhancer.enhance("Senior Python开发")

    assert profile.role == "python-developer"
    assert "python" in profile.skills
    assert profile.tools == ["shell"]
    assert profile.system_prompt == "You are a Python implementation specialist."
    assert profile.resource_weight == 0.8


def test_identity_enhancer_falls_back_to_generic_profile(tmp_path):
    template_dir = tmp_path / "templates"
    template_dir.mkdir()

    from openclaw_smart_agent.identity import IdentityEnhancer

    enhancer = IdentityEnhancer(template_dir=template_dir)
    profile = enhancer.enhance("未知角色")

    assert profile.role == "generalist"
    assert profile.skills == ["general"]
    assert profile.tools == ["shell"]
