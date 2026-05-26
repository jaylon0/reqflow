"""StageExecutor -- executes a single workflow stage."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Awaitable, Callable

from .models import (
    AgentReport,
    AgentRole,
    Risk,
    RunState,
    Stage,
    StageAnalysis,
    StageOutput,
)

logger = logging.getLogger(__name__)


class StageExecutor:
    """Execute a single workflow stage.

    Dispatches agent(s), collects structured outputs, and assembles
    a StageOutput.
    """

    def __init__(self, agent_handler: Callable[[str], Awaitable[str]]):
        """
        Args:
            agent_handler: Async function that receives a prompt string
                          and returns a JSON string from the agent.
        """
        self.agent_handler = agent_handler

    async def execute(
        self, stage: Stage, prompt: str, state: RunState
    ) -> StageOutput:
        """Execute a stage."""
        if stage.agents:
            agent_outputs = await self._dispatch_agents(stage.agents, prompt)
        else:
            agent_outputs = [await self._dispatch_single(prompt)]

        return self._collect_output(stage, agent_outputs)

    async def execute_with_repair(
        self, stage: Stage, repair_prompt: str
    ) -> StageOutput:
        """Execute in repair mode (lighter state)."""
        state = RunState(run_id="repair", requirement="", routing_level="L3")
        return await self.execute(stage, repair_prompt, state)

    # --- Internal dispatch ---

    async def _dispatch_agents(
        self, agents: list[AgentRole], prompt: str
    ) -> list[AgentReport]:
        """Dispatch multiple agents in parallel."""
        tasks = [self._dispatch_one(agent, prompt) for agent in agents]
        return await asyncio.gather(*tasks)

    async def _dispatch_one(self, agent: AgentRole, prompt: str) -> AgentReport:
        """Dispatch a single agent."""
        agent_prompt = f"""
{prompt}

## 你的角色
{agent.role}: {agent.task}

## 输出格式（必须严格遵循 JSON）
```json
{{
  "agent_role": "{agent.role}",
  "task": "{agent.task}",
  "conclusion": "你的结论（至少 50 字）",
  "confidence": 0.0-1.0,
  "findings": ["发现1", "发现2"],
  "recommendations": ["建议1", "建议2"],
  "risks": [{{"level": "low|medium|high", "description": "风险描述"}}],
  "skills_requested": []
}}
```
"""
        raw = await self.agent_handler(agent_prompt)
        return self._parse_report(raw, agent)

    async def _dispatch_single(self, prompt: str) -> AgentReport:
        """Single agent execution."""
        raw = await self.agent_handler(prompt)
        return self._parse_report(raw, AgentRole(role="agent", task="执行"))

    # --- Parsing ---

    def _parse_report(self, raw: str, agent: AgentRole) -> AgentReport:
        """Parse agent JSON output into an AgentReport."""
        try:
            json_str = self._extract_json(raw)
            data = json.loads(json_str)
            return AgentReport(
                role=data.get("agent_role", data.get("role", agent.role)),
                task=data.get("task", agent.task),
                conclusion=data.get("conclusion", ""),
                confidence=float(data.get("confidence", 0.5)),
                findings=data.get("findings", []),
                recommendations=data.get("recommendations", []),
                risks=[Risk(**r) for r in data.get("risks", [])],
                skills_requested=data.get("skills_requested", []),
            )
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            logger.warning("Failed to parse agent output: %s", e)
            # Fallback: treat raw output as conclusion
            return AgentReport(
                role=agent.role,
                task=agent.task,
                conclusion=raw[:500] if raw else "无输出",
                confidence=0.3,
            )

    @staticmethod
    def _extract_json(text: str) -> str:
        """Extract a JSON block from text."""
        # Try ```json ... ``` block
        match = re.search(r"```json\s*\n(.*?)\n```", text, re.DOTALL)
        if match:
            return match.group(1)

        # Try bare { ... } block
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return match.group(0)

        return text

    # --- Output collection ---

    def _collect_output(
        self, stage: Stage, reports: list[AgentReport]
    ) -> StageOutput:
        """Assemble StageOutput from agent reports."""
        all_findings: list[str] = []
        all_risks: list[Risk] = []
        all_skills_requested: list[str] = []

        for r in reports:
            all_findings.extend(r.findings)
            all_risks.extend(r.risks)
            all_skills_requested.extend(r.skills_requested)

        # Build combined summary
        combined_summary = "\n\n".join(
            f"### {r.role}\n{r.conclusion}" for r in reports
        )

        analysis = StageAnalysis(
            summary=combined_summary,
            findings=all_findings,
            next_steps=[
                r.recommendations[0]
                for r in reports
                if r.recommendations
            ],
        )

        return StageOutput(
            stage_id=stage.id,
            status="completed",
            analysis=analysis,
            agent_reports=reports,
            risks=all_risks,
            skills_used=list(stage.required_skills),
            skills_requested=all_skills_requested,
        )
