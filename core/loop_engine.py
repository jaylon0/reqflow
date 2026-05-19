"""Loop engine - state machine runner for iterative workflows."""

from __future__ import annotations

import inspect

from typing import Any, Callable


class LoopEngine:
    """State machine runner that iterates through a sequence of states.

    Each state has a registered handler. The engine runs all states in order,
    repeating up to max_iterations. Risk gates are checked before each state
    to decide whether to halt early.
    """

    def __init__(self, config: dict[str, Any]):
        self._config = config
        self._state_machine_str: str = config.get("state_machine", "")
        self._max_iterations: int = config.get("max_iterations", 3)
        self._risk_gates: list[str] = config.get("risk_gates", [])
        self._handlers: dict[str, Callable] = {}

        self._states: list[str] = self._parse_state_machine(self._state_machine_str)

    @staticmethod
    def _parse_state_machine(state_machine_str: str) -> list[str]:
        """Parse a state machine string like 'a -> b -> c' into a list of names."""
        if not state_machine_str:
            return []
        return [s.strip() for s in state_machine_str.split("->") if s.strip()]

    @property
    def states(self) -> list[str]:
        """Return the parsed list of state names."""
        return self._states

    @property
    def max_iterations(self) -> int:
        """Return the maximum number of loop iterations."""
        return self._max_iterations

    def register_handler(self, state: str, handler: Callable) -> None:
        """Register a handler function for a state.

        Handler signature: (context: dict) -> dict
        Can be sync or async.
        """
        self._handlers[state] = handler

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute the state machine loop.

        Iterates up to max_iterations. Each iteration runs all states in order.
        Risk gates are checked before each state. If the 'decide' state returns
        {"action": "stop"}, the loop ends. If 'verify' returns {"status": "pass"},
        the loop ends (fix is verified).

        Returns:
            Final context dict with an added "_loop_status" key.
        """
        for iteration in range(self._max_iterations):
            context["_loop_iteration"] = iteration

            gate = self._check_risk_gates(context)
            if gate is not None:
                context["_loop_status"] = "risk_gate_triggered"
                context["_risk_gate"] = gate
                return context

            for state_name in self._states:
                gate = self._check_risk_gates(context)
                if gate is not None:
                    context["_loop_status"] = "risk_gate_triggered"
                    context["_risk_gate"] = gate
                    return context

                handler = self._handlers.get(state_name)
                if handler is None:
                    continue

                if inspect.iscoroutinefunction(handler):
                    result = await handler(context)
                else:
                    result = handler(context)

                if not isinstance(result, dict):
                    continue

                context.update(result)

                # verify -> pass means fix is verified, stop the loop
                if state_name == "verify" and result.get("status") == "pass":
                    context["_loop_status"] = "verified"
                    return context

                # decide -> stop ends the entire loop
                if state_name == "decide" and result.get("action") == "stop":
                    context["_loop_status"] = "stopped"
                    return context

        context["_loop_status"] = "max_iterations"
        return context

    def _check_risk_gates(self, context: dict[str, Any]) -> str | None:
        """Check if any risk gate is triggered.

        Returns the gate name if triggered, None otherwise.

        Built-in gates:
        - "max retry count reached" — triggers when iteration >= max_iterations - 1
        - "same fingerprint appears twice" — triggers when context has
          _seen_fingerprints with duplicates
        """
        iteration = context.get("_loop_iteration", 0)

        for gate in self._risk_gates:
            gate_lower = gate.lower()
            if gate_lower == "max retry count reached":
                if iteration >= self._max_iterations - 1:
                    return gate
            elif gate_lower == "same fingerprint appears twice":
                seen = context.get("_seen_fingerprints", [])
                if len(seen) != len(set(seen)):
                    return gate
            # Other gates can be extended via subclass or config

        return None
