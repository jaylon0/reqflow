from unittest.mock import patch
from reqflow.core.adapters.manual import ManualAdapter


def test_manual_eof_returns_blocked_content():
    """Manual adapter on EOF should indicate blocked, not empty success."""
    adapter = ManualAdapter()

    with patch("builtins.input", side_effect=EOFError):
        response = adapter.call(prompt="test task")

    assert response.content != ""
    assert "blocked" in response.content.lower() or "eof" in response.content.lower() or "无法" in response.content


def test_manual_execute_tool_eof_returns_failed():
    """Manual adapter execute_tool on EOF should return failure, not success."""
    adapter = ManualAdapter()

    with patch("builtins.input", side_effect=EOFError):
        result = adapter.execute_tool(tool_name="bash", args={"command": "echo hi"})

    assert result.success is False
    assert "blocked" in result.error.lower() or "无法" in result.error
