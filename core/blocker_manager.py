"""ReqFlow Blocker Manager — 三级 BLOCKER 管理器。

P0 blocking: 必须人工决策，不能继续
P1 marked: 已解决/不影响继续，记录但不阻塞
P2 noted: 仅记录，后续处理
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class BlockerLevel(Enum):
    P0 = "blocking"
    P1 = "marked"
    P2 = "noted"


@dataclass
class Blocker:
    id: str
    level: BlockerLevel
    question: str
    answer: str = ""
    status: str = "open"  # open | resolved | not_applicable
    stage: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class BlockerGateResult:
    passed: bool
    open_p0: list[Blocker] = field(default_factory=list)
    summary: str = ""


class BlockerManager:
    """三级 BLOCKER 管理器。核心规则：P0 全部关闭才能进入下一阶段。"""

    def __init__(self):
        self._blockers: list[Blocker] = []
        self._counter = 0

    def add(self, level: BlockerLevel, question: str, stage: str = "") -> Blocker:
        self._counter += 1
        blocker = Blocker(id=f"b-{self._counter:03d}", level=level, question=question, stage=stage)
        self._blockers.append(blocker)
        logger.info("添加 BLOCKER [%s]: %s", level.value, question)
        return blocker

    def resolve(self, blocker_id: str, answer: str, status: str = "resolved") -> bool:
        for b in self._blockers:
            if b.id == blocker_id:
                b.answer = answer
                b.status = status
                return True
        return False

    def check_gate(self, stage: str = "") -> BlockerGateResult:
        open_p0 = [b for b in self._blockers if b.level == BlockerLevel.P0 and b.status == "open"]
        if stage:
            open_p0 = [b for b in open_p0 if b.stage == stage or not b.stage]
        passed = len(open_p0) == 0
        summary = "P0 BLOCKER 全部关闭，门禁通过" if passed else f"P0 BLOCKER 未全部关闭，{len(open_p0)} 项阻塞"
        return BlockerGateResult(passed=passed, open_p0=open_p0, summary=summary)

    def get_open_p0(self) -> list[Blocker]:
        return [b for b in self._blockers if b.level == BlockerLevel.P0 and b.status == "open"]

    def get_all(self) -> list[Blocker]:
        return list(self._blockers)

    def export_report(self) -> str:
        if not self._blockers:
            return "无 BLOCKER"
        lines = ["# BLOCKER 清单", ""]
        for level in BlockerLevel:
            blockers = [b for b in self._blockers if b.level == level]
            if not blockers:
                continue
            lines.append(f"## {level.value.upper()}")
            for b in blockers:
                icon = {"open": "[ ]", "resolved": "[x]", "not_applicable": "[-]"}.get(b.status, "[?]")
                lines.append(f"- {icon} [{b.id}] {b.question}")
                if b.answer:
                    lines.append(f"  回答: {b.answer}")
            lines.append("")
        return "\n".join(lines)

    def to_list(self) -> list[dict[str, Any]]:
        return [{"id": b.id, "level": b.level.value, "question": b.question, "answer": b.answer,
                 "status": b.status, "stage": b.stage, "timestamp": b.timestamp} for b in self._blockers]

    def load_from_list(self, data: list[dict[str, Any]]) -> None:
        for item in data:
            self._blockers.append(Blocker(id=item["id"], level=BlockerLevel(item["level"]),
                question=item["question"], answer=item.get("answer", ""), status=item.get("status", "open"),
                stage=item.get("stage", ""), timestamp=item.get("timestamp", "")))
