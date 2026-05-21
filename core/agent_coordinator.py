"""Agent Coordinator — V7 多 Agent 头脑风暴协调器，含辩论和角色互换。"""

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
    STRUCTURED_DEBATE = "structured-debate"  # V7 新增


class DebateRole(Enum):
    """辩论角色。"""
    PROPONENT = "proponent"   # 正方
    OPPONENT = "opponent"     # 反方
    MODERATOR = "moderator"   # 主持人
    OBSERVER = "observer"     # 观察员


@dataclass
class DebateArgument:
    """辩论论点。"""
    agent: str
    role: DebateRole
    position: str  # 立场
    arguments: list[str]  # 论据
    evidence: str = ""  # 证据
    confidence: float = 0.0


@dataclass
class Round:
    """一轮讨论。"""
    round_number: int
    contributions: list[dict[str, Any]]
    debate_arguments: list[DebateArgument] = field(default_factory=list)  # V7 辩论论点


@dataclass
class RoleSwap:
    """角色互换记录。"""
    agent: str
    from_role: str
    to_role: str
    reason: str
    round_number: int


@dataclass
class BrainstormResult:
    """头脑风暴结果。"""
    mode: BrainstormMode
    rounds: list[Round]
    consensus: str = ""
    summary: str = ""
    fallback: bool = False
    unresolved: list[str] = field(default_factory=list)
    role_swaps: list[RoleSwap] = field(default_factory=list)  # V7 角色互换记录
    debate_score: float = 0.0  # V7 辩论质量分 0-1


class AgentCoordinator:
    """V7 多 Agent 协作协调器 — 含辩论和角色互换。"""

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
        role_swaps: list[RoleSwap] = []

        # V7: structured-debate 模式使用辩论流程
        if mode == BrainstormMode.STRUCTURED_DEBATE:
            return self._structured_debate(agents, topic, context, max_rounds)

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
            role_swaps=role_swaps,
        )

    def _structured_debate(
        self,
        agents: list[str],
        topic: str,
        context: str,
        max_rounds: int,
    ) -> BrainstormResult:
        """V7 结构化辩论流程。"""
        rounds = []
        role_swaps: list[RoleSwap] = []
        debate_score = 0.0

        # 分配角色：前半正方，后半反方，第一个 agent 兼任主持人
        mid = max(1, len(agents) // 2)
        roles: dict[str, DebateRole] = {}
        for i, agent in enumerate(agents):
            if i == 0:
                roles[agent] = DebateRole.MODERATOR
            elif i <= mid:
                roles[agent] = DebateRole.PROPONENT
            else:
                roles[agent] = DebateRole.OPPONENT

        for round_num in range(1, max_rounds + 1):
            contributions = []
            debate_args: list[DebateArgument] = []

            for agent in agents:
                role = roles.get(agent, DebateRole.OBSERVER)
                contribution = self._get_debate_contribution(
                    agent=agent,
                    role=role,
                    topic=topic,
                    context=context,
                    round_number=round_num,
                    previous_rounds=rounds,
                )
                if contribution:
                    contributions.append(contribution)
                    debate_args.append(DebateArgument(
                        agent=agent,
                        role=role,
                        position=contribution.get("opinion", ""),
                        arguments=contribution.get("arguments", []),
                        evidence=contribution.get("evidence", ""),
                        confidence=contribution.get("confidence", 0.5),
                    ))

            if not contributions:
                break

            rounds.append(Round(
                round_number=round_num,
                contributions=contributions,
                debate_arguments=debate_args,
            ))

            # V7: 角色互换检测 — 如果反方论据更强，正反方互换
            if round_num < max_rounds:
                swap = self._check_role_swap(agents, roles, debate_args, round_num)
                if swap:
                    role_swaps.append(swap)
                    # 执行角色互换
                    roles[swap.agent] = DebateRole(swap.to_role)

        # 计算辩论质量分
        debate_score = self._calc_debate_score(rounds)

        return BrainstormResult(
            mode=BrainstormMode.STRUCTURED_DEBATE,
            rounds=rounds,
            consensus=self._extract_debate_consensus(rounds),
            summary=self._generate_summary(rounds, topic),
            role_swaps=role_swaps,
            debate_score=debate_score,
        )

    def _get_debate_contribution(
        self,
        agent: str,
        role: DebateRole,
        topic: str,
        context: str,
        round_number: int,
        previous_rounds: list[Round],
    ) -> dict[str, Any] | None:
        """获取辩论贡献。实际实现中会调用 agent。"""
        stance_map = {
            DebateRole.PROPONENT: "agree",
            DebateRole.OPPONENT: "disagree",
            DebateRole.MODERATOR: "neutral",
            DebateRole.OBSERVER: "neutral",
        }
        return {
            "agent": agent,
            "round": round_number,
            "role": role.value,
            "opinion": f"{agent}（{role.value}）对 {topic} 的观点 (第{round_number}轮)",
            "stance": stance_map.get(role, "neutral"),
            "arguments": [f"论据1 from {agent}", f"论据2 from {agent}"],
            "evidence": f"基于 {context} 的证据",
            "confidence": 0.7,
        }

    def _check_role_swap(
        self,
        agents: list[str],
        roles: dict[str, DebateRole],
        debate_args: list[DebateArgument],
        round_number: int,
    ) -> RoleSwap | None:
        """检测是否需要角色互换。"""
        proponent_confidence = sum(
            a.confidence for a in debate_args if a.role == DebateRole.PROPONENT
        )
        opponent_confidence = sum(
            a.confidence for a in debate_args if a.role == DebateRole.OPPONENT
        )

        # 如果反方论据置信度显著高于正方，触发角色互换
        if opponent_confidence > proponent_confidence * 1.3:
            # 找到最弱的正方 agent 进行互换
            proponents = [a for a in debate_args if a.role == DebateRole.PROPONENT]
            if proponents:
                weakest = min(proponents, key=lambda a: a.confidence)
                return RoleSwap(
                    agent=weakest.agent,
                    from_role=DebateRole.PROPONENT.value,
                    to_role=DebateRole.OPPONENT.value,
                    reason=f"反方论据更强 (confidence: {opponent_confidence:.2f} > {proponent_confidence:.2f})",
                    round_number=round_number,
                )
        return None

    def _calc_debate_score(self, rounds: list[Round]) -> float:
        """计算辩论质量分。"""
        if not rounds:
            return 0.0

        total_args = 0
        total_evidence = 0
        for r in rounds:
            for da in r.debate_arguments:
                total_args += len(da.arguments)
                if da.evidence:
                    total_evidence += 1

        # 基于论据数量和证据覆盖率
        arg_score = min(1.0, total_args / (len(rounds) * 4))  # 每轮期望 4 个论据
        evidence_score = total_evidence / max(1, sum(len(r.debate_arguments) for r in rounds))

        return (arg_score + evidence_score) / 2

    def _extract_debate_consensus(self, rounds: list[Round]) -> str:
        """从辩论中提取共识。"""
        if not rounds:
            return ""

        # 收集所有论据，取置信度最高的
        all_args: list[DebateArgument] = []
        for r in rounds:
            all_args.extend(r.debate_arguments)

        if not all_args:
            return ""

        # 按置信度排序
        all_args.sort(key=lambda a: a.confidence, reverse=True)
        top_args = all_args[:3]
        return "; ".join(f"{a.agent}({a.role.value}): {a.position}" for a in top_args)

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
        if method == "weighted_majority":
            # V7: 加权多数（简单实现，权重可扩展）
            agree_count = sum(1 for v in votes if v == "agree")
            return agree_count > len(votes) * 0.6
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
        elif method == "weighted_majority":
            consensus = "agree" if ratio > 0.6 else "disagree"
        else:
            consensus = "agree" if ratio > 0.5 else "disagree"
        return {"consensus": consensus, "ratio": ratio}
