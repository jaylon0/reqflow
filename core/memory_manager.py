"""ReqFlow Memory Manager — 长期记忆管理器。

跨会话持久化 memory.md，记录关键决策、限制、命名规则、模式。
"""

from __future__ import annotations

import json
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
        self._write_json()
        self._write_markdown()
        return {"category": category, "key": key, "value": value}

    def load(self, category: str | None = None, key: str | None = None) -> dict[str, Any]:
        """Load memories. No args = all, category = by category, category+key = specific."""
        if not self._store:
            self._read_json()
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

    def _write_json(self) -> None:
        """Write memory.json to run_dir for persistence."""
        json_path = os.path.join(self.run_dir, "memory.json")
        Path(self.run_dir).mkdir(parents=True, exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self._store, f, ensure_ascii=False, indent=2)
        logger.info("记忆已保存到: %s", json_path)

    def _read_json(self) -> None:
        """Read memory.json from run_dir if it exists."""
        json_path = os.path.join(self.run_dir, "memory.json")
        if not os.path.exists(json_path):
            return
        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self._store = data
                logger.info("从 JSON 加载记忆: %s", json_path)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("读取 memory.json 失败: %s", exc)

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
