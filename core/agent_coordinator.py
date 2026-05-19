"""Agent Coordinator - dispatches agents based on workflow coordination rules.

Reads agent_coordination config (dispatch rules, repair loop, output contracts)
from workflow YAML Stage 7 and dispatches the appropriate agents.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable


@dataclass
class DispatchRule:
    """A single dispatch rule mapping work item type to agent."""
    type: str  # dev | verify | review
    agent: str  # agent name (e.g. dev-agent)
    parallel_with: str | None = None  # agent type to run in parallel with
    model_selection: dict[str, str] | None = None


@dataclass
class AgentResult:
    """Result from an agent dispatch."""
    agent: str
    status: str  # success | failure | error
    output: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


# Type alias for the dispatch function
DispatchFunc = Callable[[str, str, dict[str, Any]], Awaitable[dict[str, Any]]]


class AgentCoordinator:
    """Dispatches agents based on workflow coordination rules.

    The coordinator knows WHO to dispatch but not HOW — the actual dispatch
    is injected via set_dispatch_func().
    """

    def __init__(self, config: dict[str, Any]):
        self._config = config
        self._dispatch_rules = self._parse_dispatch_rules(config.get("dispatch", []))
        self._repair_config = config.get("repair", {})
        self._output_contracts = config.get("output_contracts", {})
        self._dispatch_func: DispatchFunc | None = None

    # --- Properties ---

    @property
    def dispatch_rules(self) -> list[DispatchRule]:
        """Parsed dispatch rules."""
        return self._dispatch_rules

    @property
    def max_repair_rounds(self) -> int:
        """Maximum repair loop rounds from config."""
        return self._repair_config.get("max_rounds", 3)

    @property
    def repair_strategy(self) -> str:
        """Repair strategy name from config."""
        return self._repair_config.get("strategy", "resume_dev_agent")

    @property
    def output_contracts(self) -> dict[str, str]:
        """Output contracts keyed by agent type."""
        return self._output_contracts

    # --- Setup ---

    def set_dispatch_func(self, func: DispatchFunc) -> None:
        """Set the async callable that actually dispatches an agent.

        The callable signature: (agent_name, prompt, context) -> dict
        """
        self._dispatch_func = func

    # --- Dispatch ---

    async def execute_work_item(
        self, work_item: dict[str, Any], context: dict[str, Any]
    ) -> AgentResult:
        """Dispatch the right agent based on work_item type.

        Args:
            work_item: Work item dict with at least 'type' and 'name' keys.
            context: Execution context passed to the agent.

        Returns:
            AgentResult with the agent's output.
        """
        if self._dispatch_func is None:
            return AgentResult(
                agent="none",
                status="error",
                output="No dispatch function set. Call set_dispatch_func() first.",
            )

        item_type = work_item.get("type", "dev")
        rule = self._find_rule(item_type)
        if rule is None:
            return AgentResult(
                agent="none",
                status="error",
                output=f"No dispatch rule found for type '{item_type}'.",
            )

        prompt = self._build_prompt(work_item, context)
        result = await self._dispatch_func(rule.agent, prompt, context)
        return AgentResult(
            agent=rule.agent,
            status=result.get("status", "success"),
            output=result.get("output", result.get("result", "")),
            metadata=result,
        )

    async def run_verification(
        self,
        work_item: dict[str, Any],
        dev_result: AgentResult,
        context: dict[str, Any],
    ) -> tuple[AgentResult, AgentResult]:
        """Run verify + review agents (in parallel if configured).

        Args:
            work_item: The original work item.
            dev_result: Result from the dev agent.
            context: Execution context.

        Returns:
            Tuple of (verify_result, review_result).
        """
        if self._dispatch_func is None:
            error = AgentResult(agent="none", status="error", output="No dispatch function set.")
            return error, error

        verify_rule = self._find_rule("verify")
        review_rule = self._find_rule("review")

        if verify_rule is None or review_rule is None:
            error = AgentResult(agent="none", status="error", output="Missing verify or review dispatch rule.")
            return error, error

        verify_prompt = self._build_verify_prompt(work_item, dev_result, context)
        review_prompt = self._build_review_prompt(work_item, dev_result, context)

        # Check if verify and review should run in parallel
        should_parallel = (
            verify_rule.parallel_with == "review"
            or review_rule.parallel_with == "verify"
        )

        if should_parallel:
            verify_task = self._dispatch_func(verify_rule.agent, verify_prompt, context)
            review_task = self._dispatch_func(review_rule.agent, review_prompt, context)
            verify_raw, review_raw = await asyncio.gather(verify_task, review_task)
        else:
            verify_raw = await self._dispatch_func(verify_rule.agent, verify_prompt, context)
            review_raw = await self._dispatch_func(review_rule.agent, review_prompt, context)

        verify_result = AgentResult(
            agent=verify_rule.agent,
            status=verify_raw.get("status", "success"),
            output=verify_raw.get("output", verify_raw.get("result", "")),
            metadata=verify_raw,
        )
        review_result = AgentResult(
            agent=review_rule.agent,
            status=review_raw.get("status", "success"),
            output=review_raw.get("output", review_raw.get("result", "")),
            metadata=review_raw,
        )

        return verify_result, review_result

    async def execute_with_repair(
        self,
        work_item: dict[str, Any],
        context: dict[str, Any],
    ) -> AgentResult:
        """Run dev -> verify loop up to max_repair_rounds.

        On verification failure, feeds failure context back to the dev agent
        for another attempt.

        Args:
            work_item: Work item dict.
            context: Execution context.

        Returns:
            Final AgentResult (dev result from last successful attempt, or
            the last failed result if all rounds exhausted).
        """
        last_dev_result: AgentResult | None = None
        failure_context: str = ""

        for round_num in range(self.max_repair_rounds):
            # Build context with failure info from previous round
            round_context = {**context}
            if failure_context:
                round_context["previous_failure"] = failure_context
                round_context["repair_round"] = round_num

            # Step 1: Dispatch dev agent
            dev_result = await self.execute_work_item(work_item, round_context)
            last_dev_result = dev_result

            if dev_result.status in ("error", "failure"):
                failure_context = dev_result.output
                continue

            # Step 2: Run verification (verify + review)
            verify_result, review_result = await self.run_verification(
                work_item, dev_result, round_context
            )

            # Check if verification passed
            verify_passed = verify_result.status == "success"
            review_passed = review_result.status == "success"

            if verify_passed and review_passed:
                # All good — attach verification metadata
                dev_result.metadata["verify_result"] = verify_result
                dev_result.metadata["review_result"] = review_result
                return dev_result

            # Build failure context for next round
            failure_parts = []
            if not verify_passed:
                failure_parts.append(f"Verification failed: {verify_result.output}")
            if not review_passed:
                failure_parts.append(f"Review failed: {review_result.output}")
            failure_context = "; ".join(failure_parts)

        # All rounds exhausted
        if last_dev_result is not None:
            last_dev_result.status = "failure"
            last_dev_result.metadata["repair_exhausted"] = True
            return last_dev_result

        return AgentResult(
            agent="none",
            status="failure",
            output="Repair loop produced no result.",
        )

    # --- Private helpers ---

    def _parse_dispatch_rules(self, raw_rules: list[dict[str, Any]]) -> list[DispatchRule]:
        """Parse raw dispatch config into DispatchRule objects."""
        rules = []
        for rule in raw_rules:
            rules.append(DispatchRule(
                type=rule.get("type", ""),
                agent=rule.get("agent", ""),
                parallel_with=rule.get("parallel_with"),
                model_selection=rule.get("model_selection"),
            ))
        return rules

    def _find_rule(self, rule_type: str) -> DispatchRule | None:
        """Find a dispatch rule by type."""
        for rule in self._dispatch_rules:
            if rule.type == rule_type:
                return rule
        return None

    def _build_prompt(
        self, work_item: dict[str, Any], context: dict[str, Any]
    ) -> str:
        """Build the prompt for a dev agent dispatch."""
        parts = [f"Work item: {work_item.get('name', 'unnamed')}"]
        if "description" in work_item:
            parts.append(f"Description: {work_item['description']}")
        if "spec" in work_item:
            parts.append(f"Spec: {work_item['spec']}")
        if "context_pack" in context:
            parts.append(f"Context: {context['context_pack']}")
        if "previous_failure" in context:
            parts.append(f"Previous attempt failed: {context['previous_failure']}")
            parts.append("Please fix the issues and try again.")
        return "\n".join(parts)

    def _build_verify_prompt(
        self,
        work_item: dict[str, Any],
        dev_result: AgentResult,
        context: dict[str, Any],
    ) -> str:
        """Build the prompt for a verify agent dispatch."""
        parts = [
            f"Verify work item: {work_item.get('name', 'unnamed')}",
            f"Dev agent output:\n{dev_result.output}",
        ]
        contract = self._output_contracts.get("verify", "")
        if contract:
            parts.append(f"Expected output format:\n{contract}")
        return "\n".join(parts)

    def _build_review_prompt(
        self,
        work_item: dict[str, Any],
        dev_result: AgentResult,
        context: dict[str, Any],
    ) -> str:
        """Build the prompt for a review agent dispatch."""
        parts = [
            f"Review work item: {work_item.get('name', 'unnamed')}",
            f"Dev agent output:\n{dev_result.output}",
        ]
        contract = self._output_contracts.get("review", "")
        if contract:
            parts.append(f"Expected output format:\n{contract}")
        return "\n".join(parts)
