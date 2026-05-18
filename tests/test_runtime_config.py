from reqflow.core.runtime_config import RuntimeConfig

def test_runtime_config_has_api_fields():
    config = RuntimeConfig(
        name="gpt",
        display_name="GPT-4o",
        api_key="sk-test",
        api_base="https://api.openai.com/v1",
        model="gpt-4o",
        env_key="OPENAI_API_KEY",
    )
    assert config.api_key == "sk-test"
    assert config.api_base == "https://api.openai.com/v1"
    assert config.model == "gpt-4o"
    assert config.env_key == "OPENAI_API_KEY"

def test_runtime_config_defaults():
    config = RuntimeConfig(name="manual", display_name="Manual")
    assert config.api_key == ""
    assert config.api_base == ""
    assert config.model == ""
    assert config.env_key == ""
