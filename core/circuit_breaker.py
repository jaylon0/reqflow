"""CircuitBreaker -- implements the circuit breaker pattern for fault tolerance.

States:
- closed: Normal operation, requests pass through.
- open: Failure threshold exceeded, requests are blocked.
- half-open: Testing if service has recovered.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class CircuitBreaker:
    """Circuit breaker for fault tolerance.

    Args:
        failure_threshold: Number of consecutive failures before opening.
        reset_timeout: Seconds to wait before transitioning from open to half-open.
    """

    failure_threshold: int = 3
    reset_timeout: float = 60.0

    _state: str = field(default="closed", init=False)
    _failure_count: int = field(default=0, init=False)
    _last_failure_time: float = field(default=0.0, init=False)
    _success_count: int = field(default=0, init=False)

    @property
    def state(self) -> str:
        """Get current circuit breaker state."""
        # Auto-transition from open to half-open after timeout
        if self._state == "open":
            elapsed = time.time() - self._last_failure_time
            if elapsed >= self.reset_timeout:
                self._state = "half-open"
        return self._state

    def allow_request(self) -> bool:
        """Check if a request should be allowed.

        Returns:
            True if the request should proceed, False if blocked.
        """
        current_state = self.state

        if current_state == "closed":
            return True
        elif current_state == "half-open":
            # Allow one test request
            return True
        else:  # open
            return False

    def record_success(self) -> None:
        """Record a successful request."""
        if self._state == "half-open":
            # Success in half-open -> close the circuit
            self._state = "closed"
            self._failure_count = 0
            self._success_count = 0
        elif self._state == "closed":
            # Reset failure count on success
            self._failure_count = 0
            self._success_count += 1

    def record_failure(self) -> None:
        """Record a failed request."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == "half-open":
            # Failure in half-open -> reopen
            self._state = "open"
        elif self._state == "closed":
            if self._failure_count >= self.failure_threshold:
                self._state = "open"

    def reset(self) -> None:
        """Manually reset the circuit breaker to closed state."""
        self._state = "closed"
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
