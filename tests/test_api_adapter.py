"""Tests for APIAdapter.from_config classmethod."""

import json
from unittest.mock import patch, MagicMock

from reqflow.core.adapters.api import APIAdapter
from reqflow.core.runtime_config import RuntimeConfig


def test_api_adapter_from_config():
    config = RuntimeConfig(
        name="gpt", display_name="GPT-4o",
        api_key="sk-test",
        api_base="https://api.openai.com/v1",
        model="gpt-4o",
    )
    adapter = APIAdapter.from_config(config)
    assert adapter.api_key == "sk-test"
    assert adapter.base_url == "https://api.openai.com/v1"
    assert adapter.model == "gpt-4o"
    assert adapter.name == "api_gpt"


def test_api_adapter_reads_env_key():
    config = RuntimeConfig(
        name="gpt", display_name="GPT-4o",
        env_key="OPENAI_API_KEY",
        api_base="https://api.openai.com/v1",
        model="gpt-4o",
    )
    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-env-test"}):
        adapter = APIAdapter.from_config(config)
        assert adapter.api_key == "sk-env-test"


def test_api_adapter_env_key_fallback_when_no_api_key():
    config = RuntimeConfig(
        name="deepseek", display_name="DeepSeek",
        env_key="DEEPSEEK_API_KEY",
        api_base="https://api.deepseek.com/v1",
        model="deepseek-chat",
    )
    with patch.dict("os.environ", {"DEEPSEEK_API_KEY": "sk-ds"}):
        adapter = APIAdapter.from_config(config)
        assert adapter.api_key == "sk-ds"
        assert adapter.provider == "deepseek"


def test_api_adapter_call_with_mock():
    config = RuntimeConfig(
        name="gpt", display_name="GPT-4o",
        api_key="sk-test",
        api_base="https://api.openai.com/v1",
        model="gpt-4o",
    )
    adapter = APIAdapter.from_config(config)

    mock_response = {
        "choices": [{"message": {"content": "Hello!", "tool_calls": []}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(mock_response).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp
        result = adapter.call(prompt="Say hello")
        assert result.content == "Hello!"
        assert result.tokens.input_tokens == 10


def test_api_adapter_supports_capability():
    config = RuntimeConfig(name="gpt", display_name="GPT-4o", api_key="sk-test")
    adapter = APIAdapter.from_config(config)
    assert adapter.supports_capability("bash") is True
    assert adapter.supports_capability("agent_tools") is False
