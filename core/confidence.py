"""Confidence System V7 — 6维×5档置信度评估与自动路由。"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    VERY_HIGH = "very_high"  # 0.9-1.0
    HIGH = "high"            # 0.75-0.9
    MEDIUM = "medium"        # 0.5-0.75
    LOW = "low"              # 0.3-0.5
    VERY_LOW = "very_low"    # 0-0.3


@dataclass
class DimensionScore:
    """单维度评分。"""
    name: str
    score: float  # 0-1
    weight: float = 0.2
    evidence: str = ""  # 证据说明


@dataclass
class AgentConfidence:
    """单个 Agent 的置信度评估。"""
    agent_name: str
    score: float  # 0-1
    reasoning: str = ""  # 置信度理由


@dataclass
class ConfidenceResult:
    """置信度评估结果。"""
    level: ConfidenceLevel
    score: float
    action: str  # proceed | pause | retry | escalate | auto_proceed
    reasons: list[str]
    dimensions: list[DimensionScore] = field(default_factory=list)
    agent_confidences: list[AgentConfidence] = field(default_factory=list)
    consensus_degree: float = 0.0  # 共识度 0-1


# 置信度提取 prompt 模板（基于 Anthropic P(True) 研究）
CONFIDENCE_PROMPT = """Rate your confidence in this analysis from 0-100%.
Consider:
- Is the information well-established in the codebase?
- Did you have sufficient context to make this judgment?
- Are there edge cases you couldn't verify?
Provide your reasoning for the confidence score.
Format: confidence=<0-100>, reasoning=<your reasoning>"""


class ConfidenceAssessor:
    """置信度评估器 V7 — 6维×5档。"""

    # 6 维度默认权重
    DEFAULT_WEIGHTS = {
        "completeness": 0.17,    # 完整性
        "consistency": 0.15,     # 一致性
        "accuracy": 0.18,        # 准确性
        "testability": 0.15,     # 可测试性
        "risk_coverage": 0.15,   # 风险覆盖
        "spec_compliance": 0.20, # Spec合规
    }

    # 5 档阈值
    THRESHOLDS = {
        ConfidenceLevel.VERY_HIGH: 0.9,
        ConfidenceLevel.HIGH: 0.75,
        ConfidenceLevel.MEDIUM: 0.5,
        ConfidenceLevel.LOW: 0.3,
    }

    def assess(
        self,
        completeness: float = 0.0,
        consistency: float = 0.0,
        accuracy: float = 0.0,
        testability: float = 0.0,
        risk_coverage: float = 0.0,
        spec_compliance: float = 0.0,
        retry_count: int = 0,
        max_retries: int = 2,
        agent_confidences: list[AgentConfidence] | None = None,
    ) -> ConfidenceResult:
        """评估置信度（6维×5档）。"""
        dimensions = [
            DimensionScore("完整性", completeness, self.DEFAULT_WEIGHTS["completeness"]),
            DimensionScore("一致性", consistency, self.DEFAULT_WEIGHTS["consistency"]),
            DimensionScore("准确性", accuracy, self.DEFAULT_WEIGHTS["accuracy"]),
            DimensionScore("可测试性", testability, self.DEFAULT_WEIGHTS["testability"]),
            DimensionScore("风险覆盖", risk_coverage, self.DEFAULT_WEIGHTS["risk_coverage"]),
            DimensionScore("Spec合规", spec_compliance, self.DEFAULT_WEIGHTS["spec_compliance"]),
        ]

        # 加权平均
        score = sum(d.score * d.weight for d in dimensions)

        # 共识度修正
        consensus_degree = self._calc_consensus(agent_confidences or [])
        if consensus_degree >= 0.9 and agent_confidences and len(agent_confidences) >= 2:
            # 全员一致，自动提升一档
            score = min(1.0, score + 0.05)

        # 分级
        level = self._classify(score)
        action = self._determine_action(level, retry_count, max_retries)

        # 生成原因
        reasons = []
        for d in dimensions:
            if d.score < 0.8:
                reasons.append(f"{d.name}不足: {d.score:.0%}")
        if consensus_degree < 0.7:
            reasons.append(f"共识度低: {consensus_degree:.0%}")

        return ConfidenceResult(
            level=level,
            score=score,
            action=action,
            reasons=reasons,
            dimensions=dimensions,
            agent_confidences=agent_confidences or [],
            consensus_degree=consensus_degree,
        )

    def assess_from_dict(self, data: dict) -> ConfidenceResult:
        """从字典评估置信度。"""
        return self.assess(
            completeness=data.get("completeness", 0.0),
            consistency=data.get("consistency", 0.0),
            accuracy=data.get("accuracy", 0.0),
            testability=data.get("testability", 0.0),
            risk_coverage=data.get("risk_coverage", 0.0),
            spec_compliance=data.get("spec_compliance", 0.0),
            retry_count=data.get("retry_count", 0),
            agent_confidences=data.get("agent_confidences"),
        )

    def _classify(self, score: float) -> ConfidenceLevel:
        """5 档分级。"""
        if score >= self.THRESHOLDS[ConfidenceLevel.VERY_HIGH]:
            return ConfidenceLevel.VERY_HIGH
        elif score >= self.THRESHOLDS[ConfidenceLevel.HIGH]:
            return ConfidenceLevel.HIGH
        elif score >= self.THRESHOLDS[ConfidenceLevel.MEDIUM]:
            return ConfidenceLevel.MEDIUM
        elif score >= self.THRESHOLDS[ConfidenceLevel.LOW]:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def _determine_action(
        self, level: ConfidenceLevel, retry_count: int, max_retries: int
    ) -> str:
        """根据级别确定动作。"""
        actions = {
            ConfidenceLevel.VERY_HIGH: "auto_proceed",
            ConfidenceLevel.HIGH: "proceed",
            ConfidenceLevel.MEDIUM: "pause",
            ConfidenceLevel.LOW: "retry" if retry_count < max_retries else "escalate",
            ConfidenceLevel.VERY_LOW: "escalate",
        }
        return actions[level]

    def _calc_consensus(self, agent_confidences: list[AgentConfidence]) -> float:
        """计算共识度 = 1 - (标准差 / 最大可能标准差)。"""
        if len(agent_confidences) < 2:
            return 1.0
        scores = [ac.score for ac in agent_confidences]
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std = variance ** 0.5
        # 最大可能标准差（一半 0 一半 1）
        max_std = 0.5
        return max(0.0, 1.0 - (std / max_std))

    @staticmethod
    def get_action_label(action: str) -> str:
        """获取动作的中文标签。"""
        labels = {
            "auto_proceed": "自动进入下一阶段",
            "proceed": "进入下一阶段",
            "pause": "暂停，列出不确定点",
            "retry": "自动重试",
            "escalate": "升级到用户",
        }
        return labels.get(action, action)

    @staticmethod
    def get_level_label(level: ConfidenceLevel) -> str:
        """获取级别的中文标签。"""
        labels = {
            ConfidenceLevel.VERY_HIGH: "VERY_HIGH (极高)",
            ConfidenceLevel.HIGH: "HIGH (高)",
            ConfidenceLevel.MEDIUM: "MEDIUM (中)",
            ConfidenceLevel.LOW: "LOW (低)",
            ConfidenceLevel.VERY_LOW: "VERY_LOW (极低)",
        }
        return labels.get(level, level.value)
