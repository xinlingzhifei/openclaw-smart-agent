def test_runtime_config_loads_and_dumps_identity_llm_settings(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
identity:
  fallback_strategy: openclaw_llm
  openclaw_gateway_url: http://127.0.0.1:18789
  gateway_bearer_token: test-token
  session_key: workers
  thinking: medium
  provider: openai-codex
  model: gpt-5.4
  auth_profile_id: main
  timeout_ms: 45000
  max_tokens: 900
""".strip(),
        encoding="utf-8",
    )

    from openclaw_smart_agent.config import dump_runtime_config, load_runtime_config

    config = load_runtime_config(config_path)

    assert config.identity.fallback_strategy == "openclaw_llm"
    assert config.identity.openclaw_gateway_url == "http://127.0.0.1:18789"
    assert config.identity.gateway_bearer_token == "test-token"
    assert config.identity.session_key == "workers"
    assert config.identity.thinking == "medium"
    assert config.identity.provider == "openai-codex"
    assert config.identity.model == "gpt-5.4"
    assert config.identity.auth_profile_id == "main"
    assert config.identity.timeout_ms == 45000
    assert config.identity.max_tokens == 900

    dumped = dump_runtime_config(config)

    assert "identity:" in dumped
    assert "fallback_strategy: openclaw_llm" in dumped
    assert "openclaw_gateway_url: http://127.0.0.1:18789" in dumped
