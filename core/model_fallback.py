"""ModelFallback -- provides fallback model support with circuit breaker protection.

Tries primary model first, falls back to alternative models on failure.
Each model is protected by its own CircuitBreaker.
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from .circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class ModelFallback:
    """Execute prompts with automatic model fallback.

    Args:
        models: List of model identifiers (first is primary).
        handler: Async function that takes (model, prompt, **kwargs) and returns response.
        failure_threshold: Circuit breaker failure threshold per model.
        reset_timeout: Circuit breaker reset timeout in seconds.
    """

    def __init__(
        self,
        models: list[str],
        handler: Callable[[str, str], Awaitable[str]],
        failure_threshold: int = 3,
        reset_timeout: float = 60.0,
    ):
        if not models:
            raise ValueError("At least one model must be specified")

        self.models = models
        self.handler = handler
        self._breakers: dict[str, CircuitBreaker] = {
            model: CircuitBreaker(
                failure_threshold=failure_threshold,
                reset_timeout=reset_timeout,
            )
            for model in models
        }

    async def execute(self, prompt: str, **kwargs: Any) -> str:
        """Execute a prompt with automatic fallback.

        Tries each model in order. If a model's circuit breaker is open
        or the call fails, tries the next model.

        Args:
            prompt: The prompt to execute.
            **kwargs: Additional keyword arguments passed to the handler.

        Returns:
            The response from the first successful model.

        Raises:
            RuntimeError: If all models fail.
        """
        errors: list[str] = []

        for model in self.models:
            breaker = self._breakers[model]

            if not breaker.allow_request():
                logger.warning("Circuit breaker open for model %s, skipping", model)
                errors.append(f"{model}: circuit_breaker_open")
                continue

            try:
                logger.info("Trying model: %s", model)
                result = await self.handler(model, prompt)
                breaker.record_success()
                return result
            except Exception as e:
                logger.warning("Model %s failed: %s", model, e)
                breaker.record_failure()
                errors.append(f"{model}: {str(e)}")

        raise RuntimeError(f"All models failed:\n" + "\n".join(f"  - {e}" for e in errors))

    def get_status(self) -> dict[str, str]:
        """Get the status of all circuit breakers.

        Returns:
            Dict mapping model name to circuit breaker state.
        """
        return {model: breaker.state for model, breaker in self._breakers.items()}

    def reset(self, model: str | None = None) -> None:
        """Reset circuit breaker(s).

        Args:
            model: Specific model to reset, or None to reset all.
        """
        if model:
            if model in self._breakers:
                self._breakers[model].reset()
        else:
            for breaker in self._breakers.values():
                breaker.reset()
