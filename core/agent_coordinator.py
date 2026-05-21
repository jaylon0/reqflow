"""Agent Coordinator — 多 Agent 头脑风暴协调器。"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class BrainstormMode(Enum):
    ROUND_ROBIN = "round-robin"
    PANEL_OF_EXPERTS = "panel-of-experts"
    ADVERSARIAL_DEBATE = "adversarial-debate"
    CRITIQUE_REFINE = "critique-refine"
    TREE_OF_THOUGHT = "tree-of-thought"


@dataclass
class Round:
    """一轮讨论。"""
    round_number: int
    contributions: list[dict[str, Any]]


@dataclass
class BrainstormResult:
    """头脑风暴结果。"""
    mode: BrainstormMode
    rounds: list[Round]
    consensus: str = ""
    summary: str = ""
    fallback: bool = False
    unresolved: list[str] = field(default_factory=list)


class AgentCoordinator:
    """多 Agent 协作协调器。"""

    def brainstorm(
        self,
        mode: BrainstormMode,
        agents: list[str],
        topic: str,
        context: str,
        max_rounds: int = 3,
        consensus_method: str = "majority",
    ) -> BrainstormResult:
        """执行头脑风暴。"""
        rounds = []
        fallback = False

        for round_num in range(1, max_rounds + 1):
            contributions = []
            for agent in agents:
                contribution = self._get_agent_contribution(
                    agent=agent,
                    mode=mode,
                    topic=topic,
                    context=context,
                    round_number=round_num,
                    previous_rounds=rounds,
                )
                if contribution is None:
                    fallback = True
                    continue
                contributions.append(contribution)

            if not contributions:
                fallback = True
                break

            rounds.append(Round(
                round_number=round_num,
                contributions=contributions,
            ))

            # Check consensus
            votes = [c.get("stance", "neutral") for c in contributions]
            if self._has_consensus(votes, consensus_method):
                break

        return BrainstormResult(
            mode=mode,
            rounds=rounds,
            consensus=self._extract_consensus(rounds),
            summary=self._generate_summary(rounds, topic),
            fallback=fallback,
        )

    def detect_consensus(
        self,
        opinions: list[dict[str, Any]],
        method: str = "majority",
    ) -> dict[str, Any]:
        """检测共识。"""
        votes = [o["vote"] for o in opinions]
        return self._analyze_votes(votes, method)

    def _get_agent_contribution(
        self,
        agent: str,
        mode: BrainstormMode,
        topic: str,
        context: str,
        round_number: int,
        previous_rounds: list[Round],
    ) -> dict[str, Any] | None:
        """获取 agent 贡献。实际实现中会调用 agent。"""
        # Stub: return a placeholder contribution
        return {
            "agent": agent,
            "round": round_number,
            "opinion": f"{agent} 对 {topic} 的观点 (第{round_number}轮)",
            "stance": "agree",
            "reasoning": f"基于 {context} 的分析",
        }

    def _has_consensus(self, votes: list[str], method: str) -> bool:
        """判断是否达成共识。"""
        if not votes:
            return False
        if method == "majority":
            agree_count = sum(1 for v in votes if v == "agree")
            return agree_count > len(votes) / 2
        if method == "unanimous":
            return all(v == "agree" for v in votes)
        return False

    def _extract_consensus(self, rounds: list[Round]) -> str:
        """从讨论轮次中提取共识。"""
        if not rounds:
            return ""
        last_round = rounds[-1]
        opinions = [c.get("opinion", "") for c in last_round.contributions]
        return "; ".join(opinions[:3])

    def _generate_summary(self, rounds: list[Round], topic: str) -> str:
        """生成讨论摘要。"""
        if not rounds:
            return f"{topic}: 无讨论结果"
        total_contributions = sum(len(r.contributions) for r in rounds)
        return f"{topic}: {len(rounds)} 轮讨论, {total_contributions} 个贡献"

    def _analyze_votes(self, votes: list[str], method: str) -> dict[str, Any]:
        """分析投票结果。"""
        if not votes:
            return {"consensus": "none", "ratio": 0.0}
        agree_count = sum(1 for v in votes if v == "agree")
        ratio = agree_count / len(votes)
        if method == "majority":
            consensus = "agree" if ratio > 0.5 else "disagree"
        elif method == "unanimous":
            consensus = "agree" if ratio == 1.0 else "disagree"
        else:
            consensus = "agree" if ratio > 0.5 else "disagree"
        return {"consensus": consensus, "ratio": ratio}
