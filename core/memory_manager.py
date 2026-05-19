"""ReqFlow Memory Manager — 长期记忆管理器。

跨会话持久化 memory.md，记录关键决策、限制、命名规则、模式。
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    category: str     # decision | constraint | naming | pattern
    content: str
    stage: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class MemoryManager:
    """长期记忆管理器。"""

    def __init__(self, memory_path: str = "memory.md"):
        self.memory_path = memory_path
        self._entries: list[MemoryEntry] = []

    def save(self, category: str, content: str, stage: str = "") -> MemoryEntry:
        """保存一条记忆。"""
        entry = MemoryEntry(category=category, content=content, stage=stage)
        self._entries.append(entry)
        logger.info("保存记忆 [%s]: %s", category, content[:50])
        return entry

    def load(self) -> list[MemoryEntry]:
        """加载所有记忆。"""
        return list(self._entries)

    def get_by_category(self, category: str) -> list[MemoryEntry]:
        """按分类获取记忆。"""
        return [e for e in self._entries if e.category == category]

    def get_decisions(self) -> list[MemoryEntry]:
        return self.get_by_category("decision")

    def get_constraints(self) -> list[MemoryEntry]:
        return self.get_by_category("constraint")

    def get_naming_rules(self) -> list[MemoryEntry]:
        return self.get_by_category("naming")

    def get_patterns(self) -> list[MemoryEntry]:
        return self.get_by_category("pattern")

    def export_markdown(self) -> str:
        """导出为 memory.md 格式。"""
        if not self._entries:
            return "# 长期记忆\n\n（空）"

        lines = ["# 长期记忆", ""]

        categories = {
            "decision": "关键决策",
            "constraint": "特殊限制",
            "naming": "跨模块命名规则",
            "pattern": "模式记录",
        }

        for cat_key, cat_name in categories.items():
            entries = self.get_by_category(cat_key)
            if not entries:
                continue
            lines.append(f"## {cat_name}")
            for e in entries:
                stage_info = f"（阶段：{e.stage}）" if e.stage else ""
                lines.append(f"- {e.content} {stage_info}")
            lines.append("")

        return "\n".join(lines)

    def save_to_file(self, path: str | None = None) -> str:
        """保存到文件。"""
        output_path = path or self.memory_path
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        content = self.export_markdown()
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("记忆已保存到: %s", output_path)
        return output_path

    def load_from_file(self, path: str | None = None) -> None:
        """从文件加载。"""
        load_path = path or self.memory_path
        if not os.path.exists(load_path):
            return

        with open(load_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 简单解析 markdown
        current_category = ""
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("## "):
                name = line[3:].strip()
                cat_map = {"关键决策": "decision", "特殊限制": "constraint",
                           "跨模块命名规则": "naming", "模式记录": "pattern"}
                current_category = cat_map.get(name, "")
            elif line.startswith("- ") and current_category:
                entry_content = line[2:].strip()
                self.save(current_category, entry_content)

    def to_list(self) -> list[dict[str, Any]]:
        """导出为字典列表。"""
        return [{"category": e.category, "content": e.content,
                 "stage": e.stage, "timestamp": e.timestamp} for e in self._entries]

    def load_from_list(self, data: list[dict[str, Any]]) -> None:
        """从字典列表加载。"""
        for item in data:
            self._entries.append(MemoryEntry(
                category=item["category"], content=item["content"],
                stage=item.get("stage", ""), timestamp=item.get("timestamp", "")))
