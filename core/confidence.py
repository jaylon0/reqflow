"""Confidence System — 置信度评估与自动路由。"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    HIGH = "high"      # 0.8-1.0
    MEDIUM = "medium"  # 0.5-0.8
    LOW = "low"        # 0-0.5


@dataclass
class ConfidenceResult:
    """置信度评估结果。"""
    level: ConfidenceLevel
    score: float
    action: str  # proceed | pause | retry | escalate
    reasons: list[str]


class ConfidenceAssessor:
    """置信度评估器。"""

    def assess(
        self,
        completeness: float,
        consistency: float,
        accuracy: float,
        retry_count: int = 0,
        max_retries: int = 2,
    ) -> ConfidenceResult:
        score = (completeness * 0.4 + consistency * 0.3 + accuracy * 0.3)
        reasons = []

        if completeness < 0.8:
            reasons.append(f"完整性不足: {completeness:.0%}")
        if consistency < 0.8:
            reasons.append(f"一致性不足: {consistency:.0%}")
        if accuracy < 0.8:
            reasons.append(f"准确性不足: {accuracy:.0%}")

        if score >= 0.8:
            level = ConfidenceLevel.HIGH
            action = "proceed"
        elif score >= 0.5:
            level = ConfidenceLevel.MEDIUM
            action = "pause"
        else:
            level = ConfidenceLevel.LOW
            if retry_count >= max_retries:
                action = "escalate"
            else:
                action = "retry"

        return ConfidenceResult(
            level=level,
            score=score,
            action=action,
            reasons=reasons,
        )
