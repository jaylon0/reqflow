"""ReqFlow Memory Manager — V7 长期记忆管理器，含跨运行 Skill 库。

跨会话持久化 memory.md，记录关键决策、限制、命名规则、模式。
V7: 新增 SkillLibrary 跨运行 skill 复用。
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SkillEntry:
    """可复用 Skill 条目。"""
    name: str
    description: str
    category: str  # "pattern" | "solution" | "workaround" | "best_practice"
    content: str  # skill 内容（markdown）
    tags: list[str] = field(default_factory=list)
    source_run: str = ""  # 来源运行 ID
    source_stage: str = ""  # 来源阶段
    success_count: int = 0  # 成功复用次数
    failure_count: int = 0  # 失败次数
    confidence: float = 0.5  # 置信度 0-1
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_used: str = ""


class SkillLibrary:
    """跨运行 Skill 库 — 存储和检索可复用的 skill/pattern。"""

    def __init__(self, library_dir: str = ".reqflow/skills"):
        self.library_dir = Path(library_dir)
        self.library_dir.mkdir(parents=True, exist_ok=True)
        self._index_file = self.library_dir / "index.json"
        self._skills: list[SkillEntry] = []
        self._load()

    def _load(self):
        """从索引文件加载 skill 列表。"""
        if self._index_file.exists():
            try:
                data = json.loads(self._index_file.read_text(encoding="utf-8"))
                self._skills = [SkillEntry(**s) for s in data]
            except Exception:
                self._skills = []

    def _save_index(self):
        """保存索引文件。"""
        self._index_file.write_text(
            json.dumps([asdict(s) for s in self._skills], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add(self, entry: SkillEntry) -> str:
        """添加 skill 到库中。返回 skill ID (name)。"""
        # 检查是否已存在同名 skill
        existing = self.get(entry.name)
        if existing:
            # 更新已有 skill
            existing.description = entry.description
            existing.content = entry.content
            existing.tags = entry.tags
            existing.confidence = entry.confidence
        else:
            self._skills.append(entry)

        # 保存 skill 内容到独立文件
        skill_file = self.library_dir / f"{entry.name}.md"
        skill_file.write_text(
            f"# {entry.name}\n\n{entry.description}\n\n{entry.content}",
            encoding="utf-8",
        )

        self._save_index()
        logger.info("Skill 已添加到库: %s", entry.name)
        return entry.name

    def get(self, name: str) -> SkillEntry | None:
        """获取指定名称的 skill。"""
        for s in self._skills:
            if s.name == name:
                return s
        return None

    def query(
        self,
        category: str = "",
        tags: list[str] | None = None,
        min_confidence: float = 0.0,
        keyword: str = "",
        limit: int = 10,
    ) -> list[SkillEntry]:
        """查询 skill 库。"""
        results = self._skills

        if category:
            results = [s for s in results if s.category == category]
        if tags:
            tag_set = set(tags)
            results = [s for s in results if tag_set.intersection(s.tags)]
        if min_confidence > 0:
            results = [s for s in results if s.confidence >= min_confidence]
        if keyword:
            keyword_lower = keyword.lower()
            results = [s for s in results if keyword_lower in s.name.lower() or keyword_lower in s.description.lower()]

        # 按置信度和成功次数排序
        results.sort(key=lambda s: (s.confidence, s.success_count), reverse=True)
        return results[:limit]

    def record_success(self, name: str) -> None:
        """记录 skill 复用成功。"""
        skill = self.get(name)
        if skill:
            skill.success_count += 1
            skill.last_used = datetime.now().isoformat()
            # 提升置信度
            skill.confidence = min(1.0, skill.confidence + 0.05)
            self._save_index()

    def record_failure(self, name: str) -> None:
        """记录 skill 复用失败。"""
        skill = self.get(name)
        if skill:
            skill.failure_count += 1
            # 降低置信度
            skill.confidence = max(0.0, skill.confidence - 0.1)
            self._save_index()

    def get_stats(self) -> dict[str, Any]:
        """获取库统计。"""
        if not self._skills:
            return {"total": 0, "by_category": {}}

        by_category: dict[str, int] = {}
        for s in self._skills:
            by_category[s.category] = by_category.get(s.category, 0) + 1

        return {
            "total": len(self._skills),
            "by_category": by_category,
            "avg_confidence": sum(s.confidence for s in self._skills) / len(self._skills),
            "total_success": sum(s.success_count for s in self._skills),
        }

    def format_summary(self, category: str = "") -> str:
        """格式化 skill 库摘要。"""
        skills = self.query(category=category, limit=5) if category else self._skills[:5]
        if not skills:
            return "Skill 库为空"

        lines = [f"Skill 库 ({len(skills)} 条):"]
        for s in skills:
            icon = {"pattern": "🔄", "solution": "✅", "workaround": "⚠️", "best_practice": "⭐"}.get(s.category, "📋")
            lines.append(f"  {icon} {s.name}: {s.description[:40]} (置信度: {s.confidence:.0%}, 成功: {s.success_count}次)")
        return "\n".join(lines)


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
