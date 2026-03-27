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


def test_identity_enhancer_does_not_override_template_match_with_llm(tmp_path):
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
tools:
  - shell
system_prompt: You are a Python implementation specialist.
resource_weight: 0.8
""".strip(),
    )

    from openclaw_smart_agent.identity import IdentityEnhancer
    from openclaw_smart_agent.models import AgentProfile

    llm_calls: list[str] = []

    def fake_llm(identity: str, profile: AgentProfile) -> AgentProfile:
        llm_calls.append(identity)
        return AgentProfile(
            identity=identity,
            role="llm-generated-role",
            skills=["qa"],
            tools=["shell"],
            system_prompt="LLM generated profile",
            resource_weight=0.6,
        )

    enhancer = IdentityEnhancer(
        template_dir=template_dir,
        ai_enhancement_enabled=True,
        llm_enhancer=fake_llm,
    )
    profile = enhancer.enhance("Python开发")

    assert profile.role == "python-developer"
    assert llm_calls == []


def test_identity_enhancer_uses_llm_for_unmatched_identity(tmp_path):
    template_dir = tmp_path / "templates"
    template_dir.mkdir()

    from openclaw_smart_agent.identity import IdentityEnhancer
    from openclaw_smart_agent.models import AgentProfile

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

    enhancer = IdentityEnhancer(
        template_dir=template_dir,
        ai_enhancement_enabled=True,
        llm_enhancer=fake_llm,
    )
    profile = enhancer.enhance("测试工程师")

    assert profile.role == "test-engineer"
    assert profile.skills == ["testing", "qa"]
    assert profile.system_prompt == "You are a testing specialist."


def test_identity_enhancer_uses_defaults_when_llm_fallback_fails(tmp_path):
    template_dir = tmp_path / "templates"
    template_dir.mkdir()

    from openclaw_smart_agent.identity import IdentityEnhancer
    from openclaw_smart_agent.models import AgentProfile

    def fake_llm(_identity: str, _profile: AgentProfile) -> AgentProfile:
        raise RuntimeError("gateway unavailable")

    enhancer = IdentityEnhancer(
        template_dir=template_dir,
        ai_enhancement_enabled=True,
        llm_enhancer=fake_llm,
    )
    profile = enhancer.enhance("未知角色")

    assert profile.role == "generalist"
    assert profile.skills == ["general"]
    assert profile.tools == ["shell"]
