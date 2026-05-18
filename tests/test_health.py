import os
import asyncio
from reqflow.runner.mcp_server import _handle_health


def test_health_returns_system_and_runtime_info():
    """Health check should return system health AND runtime readiness."""
    result = asyncio.run(_handle_health({}))
    text = result[0].text
    assert "system" in text.lower() or "系统" in text
    assert "runtime" in text.lower()


def test_health_reports_unavailable_runtime():
    """Health check should report which runtimes are NOT ready."""
    old_key = os.environ.pop("OPENAI_API_KEY", None)
    try:
        result = asyncio.run(_handle_health({}))
        text = result[0].text
        assert "gpt" in text.lower()
    finally:
        if old_key:
            os.environ["OPENAI_API_KEY"] = old_key
