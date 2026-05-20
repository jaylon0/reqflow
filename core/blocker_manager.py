"""Blocker Manager — 管理运行过程中的阻塞项。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class BlockerLevel(Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


class BlockerStatus(Enum):
    OPEN = "open"
    RESOLVED = "resolved"


@dataclass
class Blocker:
    id: str
    level: BlockerLevel
    question: str
    stage: str
    status: BlockerStatus = BlockerStatus.OPEN
    answer: str = ""
    created_at: str = ""
    resolved_at: str = ""


class BlockerManager:
    """管理 BLOCKER 的增删改查。"""

    def __init__(self):
        self.blockers: list[Blocker] = []
        self._counter: int = 0

    def add(self, level: BlockerLevel, question: str, stage: str) -> Blocker:
        """添加一个 BLOCKER，返回带唯一 ID 的 Blocker 对象。"""
        self._counter += 1
        blocker = Blocker(
            id=f"b-{self._counter:03d}",
            level=level,
            question=question,
            stage=stage,
            created_at=datetime.now().isoformat(),
        )
        self.blockers.append(blocker)
        return blocker

    def resolve(self, blocker_id: str, answer: str) -> bool:
        """解决一个 BLOCKER。返回 True 如果找到并解决。"""
        for b in self.blockers:
            if b.id == blocker_id:
                if b.status == BlockerStatus.RESOLVED:
                    raise ValueError(f"BLOCKER {blocker_id} 已经解决")
                b.status = BlockerStatus.RESOLVED
                b.answer = answer
                b.resolved_at = datetime.now().isoformat()
                return True
        return False

    def get_open(self, level: BlockerLevel | None = None) -> list[Blocker]:
        """获取所有未解决的 BLOCKER。"""
        return [
            b for b in self.blockers
            if b.status == BlockerStatus.OPEN and (level is None or b.level == level)
        ]

    def has_p0_open(self) -> bool:
        """是否有未解决的 P0 BLOCKER。"""
        return any(
            b.level == BlockerLevel.P0 and b.status == BlockerStatus.OPEN
            for b in self.blockers
        )

    def load_from_list(self, items: list[dict[str, Any]]) -> None:
        """从 state.json 中的列表加载 BLOCKER。"""
        self.blockers = []
        self._counter = 0
        for item in items:
            blocker = Blocker(
                id=item.get("id", ""),
                level=BlockerLevel(item.get("level", "P0")),
                question=item.get("question", ""),
                stage=item.get("stage", ""),
                status=BlockerStatus(item.get("status", "open")),
                answer=item.get("answer", ""),
                created_at=item.get("created_at", ""),
                resolved_at=item.get("resolved_at", ""),
            )
            self.blockers.append(blocker)
            # 恢复计数器
            try:
                num = int(blocker.id.split("-")[-1])
                self._counter = max(self._counter, num)
            except (ValueError, IndexError):
                pass

    def to_list(self) -> list[dict[str, Any]]:
        """序列化为可存入 state.json 的列表。"""
        return [
            {
                "id": b.id,
                "level": b.level.value,
                "question": b.question,
                "stage": b.stage,
                "status": b.status.value,
                "answer": b.answer,
                "created_at": b.created_at,
                "resolved_at": b.resolved_at,
            }
            for b in self.blockers
        ]
