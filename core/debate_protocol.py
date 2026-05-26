"""DebateProtocol -- orchestrates multi-round structured debates between agents.

Dispatches agents in parallel for each round, with independent analysis
in the first round and cross-commentary in subsequent rounds.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable

from .convergence_detector import ConvergenceDetector
from .models import (
    AgentRole,
    DebateOpinion,
    DebateResult,
    DebateRound,
)

logger = logging.getLogger(__name__)


class DebateProtocol:
    """Orchestrates multi-round structured debates.

    Args:
        agent_handler: Async function that receives a prompt and returns agent output.
        convergence_detector: Detector for convergence checking.
    """

    def __init__(
        self,
        agent_handler: Callable[[str], Awaitable[str]],
        convergence_detector: ConvergenceDetector | None = None,
    ):
        self.agent_handler = agent_handler
        self.detector = convergence_detector or ConvergenceDetector()

    async def run_debate(
        self,
        topic: str,
        agents: list[AgentRole],
        max_rounds: int = 5,
        convergence_threshold: float = 0.85,
    ) -> DebateResult:
        """Run a multi-round debate.

        Args:
            topic: The debate topic.
            agents: List of agent roles participating in the debate.
            max_rounds: Maximum number of debate rounds.
            convergence_threshold: Similarity threshold for convergence.

        Returns:
            DebateResult with all rounds and final consensus.
        """
        self.detector.max_rounds = max_rounds
        self.detector.similarity_threshold = convergence_threshold

        rounds: list[dict] = []
        debate_rounds: list[DebateRound] = []

        for round_num in range(1, max_rounds + 1):
            logger.info("Debate round %d/%d for topic: %s", round_num, max_rounds, topic)

            if round_num == 1:
                # First round: independent analysis
                opinions = await self._first_round(topic, agents)
            else:
                # Subsequent rounds: cross-commentary
                prev_opinions = rounds[-1].get("opinions", [])
                opinions = await self._cross_commentary_round(topic, agents, prev_opinions)

            # Build round data for convergence detection
            round_data = {
                "round_num": round_num,
                "opinions": [
                    {
                        "role": o.role,
                        "conclusion": o.conclusion,
                        "confidence": o.confidence,
                        "cross_commentary": o.cross_commentary,
                    }
                    for o in opinions
                ],
            }
            rounds.append(round_data)

            # Calculate convergence for this round
            conv_result = self.detector.check(rounds)
            convergence_score = conv_result["score"]

            # Store convergence in round_data for later retrieval
            round_data["convergence"] = convergence_score

            debate_round = DebateRound(
                round_num=round_num,
                opinions=opinions,
                convergence=convergence_score,
            )
            debate_rounds.append(debate_round)

            logger.info(
                "Round %d convergence: %.2f (%s)",
                round_num, convergence_score, conv_result["reason"],
            )

            if conv_result["converged"]:
                logger.info("Debate converged at round %d: %s", round_num, conv_result["reason"])
                break

        # Build final result
        final_score = rounds[-1].get("convergence", 0.0) if rounds else 0.0
        consensus = self._build_consensus(debate_rounds)
        dissenting = self._extract_dissents(debate_rounds)

        return DebateResult(
            topic=topic,
            rounds=debate_rounds,
            consensus=consensus,
            dissenting=dissenting,
            convergence_score=final_score,
        )

    async def _first_round(self, topic: str, agents: list[AgentRole]) -> list[DebateOpinion]:
        """First round: independent analysis from each agent."""
        prompts = []
        for agent in agents:
            prompt = f"""
## 辩论主题
{topic}

## 你的角色
{agent.role}: {agent.task}

## 要求
请独立分析以上主题，给出你的结论、推理过程和置信度。
不要参考其他人的观点，完全基于你自己的判断。

## 输出格式（JSON）
```json
{{
  "role": "{agent.role}",
  "conclusion": "你的结论（详细说明）",
  "confidence": 0.0-1.0,
  "reasoning": "你的推理过程"
}}
```
"""
            prompts.append(prompt)

        return await self._dispatch_parallel(agents, prompts)

    async def _cross_commentary_round(
        self,
        topic: str,
        agents: list[AgentRole],
        prev_opinions: list[dict],
    ) -> list[DebateOpinion]:
        """Subsequent rounds: each agent reviews others' conclusions."""
        # Format previous opinions for context
        others_text = "\n".join(
            f"- **{o.get('role', 'unknown')}**: {o.get('conclusion', 'N/A')}"
            for o in prev_opinions
        )

        prompts = []
        for agent in agents:
            prompt = f"""
## 辩论主题
{topic}

## 你的角色
{agent.role}: {agent.task}

## 其他参与者的上一轮结论
{others_text}

## 要求
1. 评论其他参与者的结论（指出你同意/不同意的部分及原因）
2. 基于他人的观点，更新或坚持你自己的结论
3. 给出你的置信度

## 输出格式（JSON）
```json
{{
  "role": "{agent.role}",
  "conclusion": "你的更新结论",
  "confidence": 0.0-1.0,
  "reasoning": "你的推理过程",
  "cross_commentary": "对其他人结论的评论"
}}
```
"""
            prompts.append(prompt)

        return await self._dispatch_parallel(agents, prompts)

    async def _dispatch_parallel(
        self, agents: list[AgentRole], prompts: list[str]
    ) -> list[DebateOpinion]:
        """Dispatch agents in parallel and collect opinions."""
        tasks = [self._get_opinion(agent, prompt) for agent, prompt in zip(agents, prompts)]
        return await asyncio.gather(*tasks)

    async def _get_opinion(self, agent: AgentRole, prompt: str) -> DebateOpinion:
        """Get a single agent's opinion."""
        import json
        import re

        raw = await self.agent_handler(prompt)

        try:
            # Extract JSON from response
            match = re.search(r"```json\s*\n(.*?)\n```", raw, re.DOTALL)
            if match:
                json_str = match.group(1)
            else:
                match = re.search(r"\{.*\}", raw, re.DOTALL)
                json_str = match.group(0) if match else raw

            data = json.loads(json_str)
            return DebateOpinion(
                role=data.get("role", agent.role),
                agent=agent.role,
                conclusion=data.get("conclusion", ""),
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", ""),
                cross_commentary=data.get("cross_commentary", ""),
            )
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            logger.warning("Failed to parse debate opinion: %s", e)
            return DebateOpinion(
                role=agent.role,
                agent=agent.role,
                conclusion=raw[:500] if raw else "无输出",
                confidence=0.3,
            )

    def _build_consensus(self, rounds: list[DebateRound]) -> str:
        """Build consensus text from the final round."""
        if not rounds:
            return "无辩论记录"

        final = rounds[-1]
        parts = [f"经过 {len(rounds)} 轮辩论，达成以下共识：\n"]

        for opinion in final.opinions:
            parts.append(f"**{opinion.role}**: {opinion.conclusion}\n")

        return "\n".join(parts)

    def _extract_dissents(self, rounds: list[DebateRound]) -> list[str]:
        """Extract dissenting opinions from the final round."""
        if not rounds:
            return []

        final = rounds[-1]
        dissents = []

        # Find agents with significantly lower confidence than average
        confidences = [o.confidence for o in final.opinions if o.confidence > 0]
        if not confidences:
            return []

        avg_confidence = sum(confidences) / len(confidences)

        for opinion in final.opinions:
            if opinion.confidence < avg_confidence * 0.7:
                dissents.append(f"{opinion.role}: {opinion.conclusion[:200]}")

        return dissents
