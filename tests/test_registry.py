from reqflow.core.registry import RuntimeRegistry


def test_registry_loads_gpt_api_config():
    registry = RuntimeRegistry()
    config = registry.get("gpt")
    assert config.api_base == "https://api.openai.com/v1"
    assert config.model == "gpt-4o"
    assert config.env_key == "OPENAI_API_KEY"


def test_registry_loads_deepseek_api_config():
    registry = RuntimeRegistry()
    config = registry.get("deepseek")
    assert config.api_base == "https://api.deepseek.com/v1"
    assert config.model == "deepseek-chat"
    assert config.env_key == "DEEPSEEK_API_KEY"


def test_registry_loads_gemini_api_config():
    registry = RuntimeRegistry()
    config = registry.get("gemini")
    assert config.api_base == "https://generativelanguage.googleapis.com/v1beta"
    assert config.model == "gemini-2.0-flash"
    assert config.env_key == "GEMINI_API_KEY"


def test_registry_manual_has_empty_api_fields():
    registry = RuntimeRegistry()
    config = registry.get("manual")
    assert config.api_key == ""
    assert config.api_base == ""
    assert config.model == ""
    assert config.env_key == ""
