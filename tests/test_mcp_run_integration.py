import os
import asyncio
from reqflow.runner.mcp_server import _handle_run


def test_mcp_run_fails_fast_on_missing_api_key():
    """MCP reqflow_run should fail fast when API key is missing."""
    old_key = os.environ.pop("OPENAI_API_KEY", None)
    try:
        result = asyncio.run(_handle_run({"requirement": "test", "runtime": "gpt"}))
        text = result[0].text
        assert "错误" in text or "error" in text.lower() or "未配置" in text
        assert "401" not in text
    finally:
        if old_key:
            os.environ["OPENAI_API_KEY"] = old_key


def test_mcp_run_default_uses_host():
    """MCP reqflow_run without runtime should prefer host."""
    result = asyncio.run(_handle_run({"requirement": "test"}))
    text = result[0].text
    assert "gpt" not in text.lower() or "host" in text.lower() or "manual" in text.lower()
