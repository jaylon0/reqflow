"""Tests for BLOCKED/TIMEOUT response detection in Engine."""

import asyncio
import shutil

from unittest.mock import patch, MagicMock

from reqflow.core.engine import Engine, StepResult
from reqflow.core.runtime_config import RuntimeConfig
from reqflow.core.adapters.base import ModelResponse, TokenUsage


def _make_engine(tmp_dir="/tmp/test-blocked"):
    config = RuntimeConfig(name="manual", display_name="Manual")
    return Engine(config=config, run_dir=tmp_dir)


def test_step_result_has_blocked_status():
    """StepResult should accept 'blocked' status without error."""
    result = StepResult(name="test", status="blocked", error="content blocked")
    assert result.status == "blocked"
    assert result.error == "content blocked"
    shutil.rmtree("/tmp/test-blocked", ignore_errors=True)


def test_engine_detects_blocked_response():
    """When adapter returns [BLOCKED] in content, engine should report blocked status."""
    engine = _make_engine("/tmp/test-engine-blocked")

    blocked_response = ModelResponse(
        content="[BLOCKED] Cannot proceed due to policy violation.",
        tokens=TokenUsage(input_tokens=10, output_tokens=20),
    )

    async def _run():
        with patch.object(engine, "select_adapter") as mock_select:
            mock_adapter = MagicMock()
            mock_adapter.call.return_value = blocked_response
            mock_adapter.name = "mock"
            mock_select.return_value = mock_adapter

            result = await engine.run_workflow(
                [{"name": "step1", "prompt": "do something"}],
                requirement="test requirement",
            )
            return result

    result = asyncio.run(_run())
    assert result["status"] == "blocked"
    assert result["blocked_at"] == "step1"
    assert result["steps"][0]["status"] == "blocked"
    shutil.rmtree("/tmp/test-engine-blocked", ignore_errors=True)


def test_engine_detects_timeout_response():
    """When adapter returns [TIMEOUT] in content, engine should report timeout status."""
    engine = _make_engine("/tmp/test-engine-timeout")

    timeout_response = ModelResponse(
        content="[TIMEOUT] Request timed out after 30s.",
        tokens=TokenUsage(input_tokens=5, output_tokens=10),
    )

    async def _run():
        with patch.object(engine, "select_adapter") as mock_select:
            mock_adapter = MagicMock()
            mock_adapter.call.return_value = timeout_response
            mock_adapter.name = "mock"
            mock_select.return_value = mock_adapter

            result = await engine.run_workflow(
                [{"name": "step1", "prompt": "do something"}],
                requirement="test requirement",
            )
            return result

    result = asyncio.run(_run())
    assert result["status"] == "timeout"
    assert result["timeout_at"] == "step1"
    assert result["steps"][0]["status"] == "timeout"
    shutil.rmtree("/tmp/test-engine-timeout", ignore_errors=True)


def test_engine_detects_blocked_from_raw_status():
    """When response.raw has status='blocked', engine should detect it."""
    engine = _make_engine("/tmp/test-engine-raw-blocked")

    blocked_response = ModelResponse(
        content="Operation blocked by system.",
        tokens=TokenUsage(input_tokens=5, output_tokens=10),
        raw={"status": "blocked"},
    )

    async def _run():
        with patch.object(engine, "select_adapter") as mock_select:
            mock_adapter = MagicMock()
            mock_adapter.call.return_value = blocked_response
            mock_adapter.name = "mock"
            mock_select.return_value = mock_adapter

            result = await engine.run_workflow(
                [{"name": "step1", "prompt": "do something"}],
                requirement="test requirement",
            )
            return result

    result = asyncio.run(_run())
    assert result["status"] == "blocked"
    shutil.rmtree("/tmp/test-engine-raw-blocked", ignore_errors=True)


def test_engine_normal_response_stays_success():
    """Normal responses without BLOCKED/TIMEOUT should still report success."""
    engine = _make_engine("/tmp/test-engine-normal")

    normal_response = ModelResponse(
        content="Everything completed successfully.",
        tokens=TokenUsage(input_tokens=10, output_tokens=20),
    )

    async def _run():
        with patch.object(engine, "select_adapter") as mock_select:
            mock_adapter = MagicMock()
            mock_adapter.call.return_value = normal_response
            mock_adapter.name = "mock"
            mock_select.return_value = mock_adapter

            result = await engine.run_workflow(
                [{"name": "step1", "prompt": "do something"}],
                requirement="test requirement",
            )
            return result

    result = asyncio.run(_run())
    assert result["status"] == "completed"
    assert result["steps"][0]["status"] == "success"
    shutil.rmtree("/tmp/test-engine-normal", ignore_errors=True)
