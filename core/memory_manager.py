"""ReqFlow Memory Manager — 长期记忆管理器。

跨会话持久化 memory.md，记录关键决策、限制、命名规则、模式。
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class MemoryManager:
    """长期记忆管理器。"""

    def __init__(self, run_dir: str):
        """Takes run_dir string."""
        self.run_dir = run_dir
        self._store: dict[str, dict[str, str]] = {}

    def save(self, category: str, key: str, value: str) -> dict[str, Any]:
        """Save a memory entry with category, key, value."""
        if category not in self._store:
            self._store[category] = {}
        self._store[category][key] = value
        logger.info("保存记忆 [%s/%s]: %s", category, key, value[:50] if len(value) > 50 else value)
        self._write_markdown()
        return {"category": category, "key": key, "value": value}

    def load(self, category: str | None = None, key: str | None = None) -> dict[str, Any]:
        """Load memories. No args = all, category = by category, category+key = specific."""
        if category is not None and key is not None:
            value = self._store.get(category, {}).get(key)
            if value is not None:
                return {"category": category, "key": key, "value": value}
            return {}
        if category is not None:
            entries = self._store.get(category, {})
            return {"category": category, "entries": {k: v for k, v in entries.items()}}
        # All
        return dict(self._store)

    def _write_markdown(self) -> None:
        """Write memory.md to run_dir."""
        md_path = os.path.join(self.run_dir, "memory.md")
        Path(self.run_dir).mkdir(parents=True, exist_ok=True)
        lines = ["# 长期记忆", ""]
        for cat, entries in self._store.items():
            lines.append(f"## {cat}")
            for k, v in entries.items():
                lines.append(f"- **{k}**: {v}")
            lines.append("")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        logger.info("记忆已保存到: %s", md_path)
