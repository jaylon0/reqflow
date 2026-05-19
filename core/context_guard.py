"""ReqFlow Context Guard — Context 保护器。

保护主会话不被大量 IO 操作撑爆。
"""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

MAX_RESULTS = 50


class ContextGuard:
    """Context 保护器。核心规则：
    - 大量 IO 操作必须用 subagent 隔离
    - 主会话不做全量扫描，只做定向搜索
    - 单次搜索结果限制 50 条
    - 每个阶段结束时清理临时 context
    """

    def __init__(self, max_results: int = MAX_RESULTS):
        self.max_results = max_results
        self._temp_keys: dict[str, list[str]] = {}  # stage -> keys

    def limit_results(self, results: list, max_count: int | None = None) -> list:
        """限制单次搜索结果数量。"""
        limit = max_count or self.max_results
        if len(results) > limit:
            logger.warning("结果数量 %d 超过限制 %d，已截断", len(results), limit)
            return results[:limit]
        return results

    def register_temp(self, stage: str, key: str) -> None:
        """注册临时 context key。"""
        self._temp_keys.setdefault(stage, []).append(key)

    def cleanup_stage(self, stage: str) -> list[str]:
        """阶段结束时清理临时 context，返回被清理的 key 列表。"""
        keys = self._temp_keys.pop(stage, [])
        if keys:
            logger.info("清理阶段 %s 的临时 context: %s", stage, keys)
        return keys

    def cleanup_all(self) -> dict[str, list[str]]:
        """清理所有临时 context。"""
        cleaned = dict(self._temp_keys)
        self._temp_keys.clear()
        return cleaned

    def check_overflow(self, context_size: int, max_size: int = 100000) -> bool:
        """检查 context 是否接近溢出。"""
        if context_size > max_size * 0.8:
            logger.warning("Context 大小 %d 接近溢出阈值 %d", context_size, max_size)
            return True
        return False

    def should_use_subagent(self, estimated_items: int, threshold: int = 20) -> bool:
        """判断是否应该使用 subagent 隔离。"""
        return estimated_items > threshold
