"""Tests for CircuitBreaker and ModelFallback."""

from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from core.circuit_breaker import CircuitBreaker
from core.model_fallback import ModelFallback


# ---------------------------------------------------------------------------
# CircuitBreaker tests
# ---------------------------------------------------------------------------


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""

    def test_initial_state_is_closed(self):
        cb = CircuitBreaker()
        assert cb.state == "closed"

    def test_closed_allows_requests(self):
        cb = CircuitBreaker()
        assert cb.allow_request() is True

    def test_single_failure_stays_closed(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        assert cb.state == "closed"
        assert cb.allow_request() is True

    def test_opens_after_threshold_failures(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "open"
        assert cb.allow_request() is False

    def test_half_open_after_timeout(self):
        import time
        cb = CircuitBreaker(failure_threshold=2, reset_timeout=0.1)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "open"

        # Wait for timeout
        time.sleep(0.15)
        assert cb.state == "half-open"
        assert cb.allow_request() is True  # Allows one test request

    def test_half_open_success_closes(self):
        import time
        cb = CircuitBreaker(failure_threshold=2, reset_timeout=0.1)
        cb.record_failure()
        cb.record_failure()
        time.sleep(0.15)
        assert cb.state == "half-open"

        cb.record_success()
        assert cb.state == "closed"

    def test_half_open_failure_reopens(self):
        import time
        cb = CircuitBreaker(failure_threshold=2, reset_timeout=0.1)
        cb.record_failure()
        cb.record_failure()
        time.sleep(0.15)
        assert cb.state == "half-open"

        cb.record_failure()
        assert cb.state == "open"

    def test_success_resets_failure_count(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        # Should have reset
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "closed"  # Only 2 failures after reset

    def test_manual_reset(self):
        cb = CircuitBreaker(failure_threshold=2)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "open"

        cb.reset()
        assert cb.state == "closed"
        assert cb.allow_request() is True


# ---------------------------------------------------------------------------
# ModelFallback tests
# ---------------------------------------------------------------------------


class TestModelFallback:
    """Tests for ModelFallback."""

    @pytest.mark.asyncio
    async def test_primary_model_success(self):
        """Should use primary model when it succeeds."""
        handler = AsyncMock(return_value="success from primary")
        fallback = ModelFallback(
            models=["primary", "secondary"],
            handler=handler,
        )

        result = await fallback.execute("test prompt")
        assert result == "success from primary"
        handler.assert_called_once_with("primary", "test prompt")

    @pytest.mark.asyncio
    async def test_fallback_on_primary_failure(self):
        """Should fall back to secondary when primary fails."""
        handler = AsyncMock(side_effect=[
            Exception("Primary failed"),
            "success from secondary",
        ])
        fallback = ModelFallback(
            models=["primary", "secondary"],
            handler=handler,
        )

        result = await fallback.execute("test prompt")
        assert result == "success from secondary"
        assert handler.call_count == 2

    @pytest.mark.asyncio
    async def test_all_models_fail_raises(self):
        """Should raise RuntimeError when all models fail."""
        handler = AsyncMock(side_effect=Exception("Model failed"))
        fallback = ModelFallback(
            models=["model-a", "model-b"],
            handler=handler,
        )

        with pytest.raises(RuntimeError, match="All models failed"):
            await fallback.execute("test prompt")

    @pytest.mark.asyncio
    async def test_skips_open_circuit_breaker(self):
        """Should skip models with open circuit breakers."""
        call_count = 0

        async def handler(model, prompt):
            nonlocal call_count
            call_count += 1
            if model == "primary":
                raise Exception("Primary down")
            return f"success from {model}"

        fallback = ModelFallback(
            models=["primary", "secondary"],
            handler=handler,
            failure_threshold=1,
        )

        # First call: primary fails, secondary succeeds
        result = await fallback.execute("test")
        assert result == "success from secondary"

        # Second call: primary circuit should be open
        call_count_before = call_count
        result = await fallback.execute("test")
        # Primary should be skipped (circuit open)
        assert result == "success from secondary"

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Should return status of all circuit breakers."""
        handler = AsyncMock(return_value="ok")
        fallback = ModelFallback(
            models=["model-a", "model-b"],
            handler=handler,
        )

        status = fallback.get_status()
        assert "model-a" in status
        assert "model-b" in status
        assert all(s == "closed" for s in status.values())

    @pytest.mark.asyncio
    async def test_reset_specific_model(self):
        """Should reset circuit breaker for specific model."""
        handler = AsyncMock(side_effect=Exception("fail"))
        fallback = ModelFallback(
            models=["model-a"],
            handler=handler,
            failure_threshold=1,
        )

        # Trigger circuit open
        try:
            await fallback.execute("test")
        except RuntimeError:
            pass

        assert fallback.get_status()["model-a"] == "open"
        fallback.reset("model-a")
        assert fallback.get_status()["model-a"] == "closed"

    @pytest.mark.asyncio
    async def test_reset_all_models(self):
        """Should reset all circuit breakers."""
        handler = AsyncMock(side_effect=Exception("fail"))
        fallback = ModelFallback(
            models=["model-a", "model-b"],
            handler=handler,
            failure_threshold=1,
        )

        # Open both circuits
        try:
            await fallback.execute("test")
        except RuntimeError:
            pass

        fallback.reset()
        assert all(s == "closed" for s in fallback.get_status().values())
