import os
from reqflow.core.registry import RuntimeRegistry


def test_runtime_readiness_missing_api_key():
    """Runtime with missing API key should fail readiness check."""
    registry = RuntimeRegistry()
    old_key = os.environ.pop("OPENAI_API_KEY", None)
    try:
        ready, reason = registry.check_readiness("gpt")
        assert ready is False
        assert "API key" in reason or "api_key" in reason.lower() or "未配置" in reason
    finally:
        if old_key:
            os.environ["OPENAI_API_KEY"] = old_key


def test_runtime_readiness_with_api_key():
    """Runtime with API key set should pass readiness check."""
    registry = RuntimeRegistry()
    old_key = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "sk-test-key"
    try:
        ready, reason = registry.check_readiness("gpt")
        assert ready is True
    finally:
        if old_key:
            os.environ["OPENAI_API_KEY"] = old_key
        else:
            os.environ.pop("OPENAI_API_KEY", None)


def test_runtime_readiness_manual_always_ready():
    """Manual runtime should always be ready."""
    registry = RuntimeRegistry()
    ready, reason = registry.check_readiness("manual")
    assert ready is True


def test_default_runtime_prefers_host_over_api():
    """Default runtime detection should prefer host over external API runtimes."""
    registry = RuntimeRegistry()
    saved_keys = {}
    for provider in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "DEEPSEEK_API_KEY"):
        saved_keys[provider] = os.environ.pop(provider, None)
    try:
        from reqflow.runner.mcp_server import _detect_runtime
        config = _detect_runtime(registry)
        assert config is not None
        assert config.name not in ("claude", "gpt", "gemini", "deepseek"), \
            f"Default runtime should not be external API without key, got {config.name}"
    finally:
        for k, v in saved_keys.items():
            if v is not None:
                os.environ[k] = v
