"""AgentLifecycleManager -- agent execution with triple limits."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from .models import AgentReport, AgentRole

logger = logging.getLogger(__name__)


@dataclass
class AgentLimits:
    """Agent execution limits."""
    max_iterations: int = 20
    max_execution_time: int = 300  # seconds
    max_retry_limit: int = 2


class MaxIterationsExceeded(Exception):
    """Raised when agent exceeds max iterations."""

    def __init__(self, iterations: int):
        self.iterations = iterations
        super().__init__(f"Max iterations exceeded: {iterations}")


class AgentLifecycleManager:
    """Manages agent execution with triple limits.

    Each agent execution is bounded by:
    - Max iterations (agent internal loops)
    - Max execution time (timeout)
    - Max retry count (on failure)
    """

    def __init__(self, agent_handler: Callable[[str], Awaitable[str]]):
        self.agent_handler = agent_handler

    async def execute_with_limits(
        self,
        agent: AgentRole,
        prompt: str,
        limits: AgentLimits | None = None,
    ) -> AgentReport:
        """Execute an agent with triple limits."""
        if limits is None:
            limits = AgentLimits()

        attempts = 0
        last_error: Exception | None = None

        while attempts <= limits.max_retry_limit:
            attempts += 1

            try:
                # Execute with timeout
                report = await asyncio.wait_for(
                    self._execute_agent(agent, prompt),
                    timeout=limits.max_execution_time,
                )

                # Check iteration count
                if report.iterations > limits.max_iterations:
                    raise MaxIterationsExceeded(report.iterations)

                return report

            except asyncio.TimeoutError:
                logger.warning(
                    "Agent %s timed out (%ds)",
                    agent.role, limits.max_execution_time,
                )
                last_error = TimeoutError(
                    f"Agent {agent.role} timed out after {limits.max_execution_time}s"
                )
                if attempts > limits.max_retry_limit:
                    return self._build_timeout_report(agent, limits)

            except MaxIterationsExceeded as e:
                logger.warning(
                    "Agent %s exceeded max iterations (%d)",
                    agent.role, e.iterations,
                )
                last_error = e
                if attempts > limits.max_retry_limit:
                    return self._build_iteration_report(agent, limits)

            except Exception as e:
                logger.error("Agent %s execution failed: %s", agent.role, e)
                last_error = e
                if attempts > limits.max_retry_limit:
                    return self._build_exhausted_report(agent, attempts, last_error)

        return self._build_exhausted_report(agent, attempts, last_error)

    async def _execute_agent(self, agent: AgentRole, prompt: str) -> AgentReport:
        """Execute a single agent and parse the result."""
        raw = await self.agent_handler(prompt)
        return self._parse_report(raw, agent)

    @staticmethod
    def _parse_report(raw: str, agent: AgentRole) -> AgentReport:
        """Parse agent output into an AgentReport."""
        import json
        import re

        try:
            # Extract JSON
            match = re.search(r"```json\s*\n(.*?)\n```", raw, re.DOTALL)
            json_str = match.group(1) if match else raw
            match = re.search(r"\{.*\}", json_str, re.DOTALL)
            json_str = match.group(0) if match else json_str

            data = json.loads(json_str)
            return AgentReport(
                role=data.get("agent_role", data.get("role", agent.role)),
                task=data.get("task", agent.task),
                conclusion=data.get("conclusion", ""),
                confidence=float(data.get("confidence", 0.5)),
                findings=data.get("findings", []),
                recommendations=data.get("recommendations", []),
                iterations=data.get("iterations", 0),
            )
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return AgentReport(
                role=agent.role,
                task=agent.task,
                conclusion=raw[:500] if raw else "无输出",
                confidence=0.3,
            )

    @staticmethod
    def _build_timeout_report(agent: AgentRole, limits: AgentLimits) -> AgentReport:
        """Build a report for timeout."""
        return AgentReport(
            role=agent.role,
            task=agent.task,
            conclusion=f"Agent 执行超时（{limits.max_execution_time}s），已重试 {limits.max_retry_limit} 次",
            confidence=0.0,
        )

    @staticmethod
    def _build_iteration_report(agent: AgentRole, limits: AgentLimits) -> AgentReport:
        """Build a report for iteration exceeded."""
        return AgentReport(
            role=agent.role,
            task=agent.task,
            conclusion=f"Agent 超过最大迭代次数（{limits.max_iterations}），已重试 {limits.max_retry_limit} 次",
            confidence=0.0,
        )

    @staticmethod
    def _build_error_report(agent: AgentRole, error: Exception) -> AgentReport:
        """Build a report for execution error."""
        return AgentReport(
            role=agent.role,
            task=agent.task,
            conclusion=f"Agent 执行失败: {error}",
            confidence=0.0,
        )

    @staticmethod
    def _build_exhausted_report(
        agent: AgentRole, attempts: int, last_error: Exception | None
    ) -> AgentReport:
        """Build a report for exhausted retries."""
        return AgentReport(
            role=agent.role,
            task=agent.task,
            conclusion=f"Agent 重试耗尽（{attempts} 次），最后错误: {last_error}",
            confidence=0.0,
        )
