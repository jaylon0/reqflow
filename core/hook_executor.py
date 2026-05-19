"""Knowledge Hook execution system - register and execute hooks at workflow stages."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Hook 函数签名: func(stage_name, context) -> Any
HookFunc = Callable[[str, dict[str, Any]], Any]


@dataclass
class HookResult:
    """单个 hook 执行结果。"""
    hook_name: str
    trigger: str
    success: bool
    result: Any = None
    error: str | None = None


@dataclass
class HookRegistration:
    """已注册的 hook 信息。"""
    func: HookFunc
    trigger: str  # "before_stage" | "after_stage" | 自定义
    description: str = ""


class HookExecutor:
    """Knowledge Hook 注册与执行器。

    管理 hook 注册表，在 workflow stage 前后触发对应 hook。
    Hook 函数可以是同步或异步的，执行器会自动处理。
    """

    def __init__(self):
        self._hooks: dict[str, HookRegistration] = {}

    def register_hook(
        self,
        name: str,
        func: HookFunc,
        trigger: str,
        description: str = "",
    ) -> None:
        """注册一个 hook。

        Args:
            name: hook 名称（唯一标识）。
            func: hook 函数，签名 (stage_name, context) -> Any。
            trigger: 触发类型，如 "before_stage"、"after_stage"。
            description: hook 描述。
        """
        self._hooks[name] = HookRegistration(
            func=func,
            trigger=trigger,
            description=description,
        )
        logger.debug("已注册 hook: %s (trigger=%s)", name, trigger)

    def list_hooks(self) -> list[str]:
        """返回所有已注册 hook 的名称列表。"""
        return list(self._hooks.keys())

    async def execute_hooks(
        self,
        hook_names: list[str],
        stage_name: str,
        context: dict[str, Any],
        trigger: str,
    ) -> list[HookResult]:
        """执行匹配 trigger 的指定 hooks。

        Args:
            hook_names: 要执行的 hook 名称列表。
            stage_name: 当前 stage 名称。
            context: 执行上下文。
            trigger: 当前触发类型。

        Returns:
            所有 hook 的执行结果列表。
        """
        results: list[HookResult] = []

        for name in hook_names:
            reg = self._hooks.get(name)
            if reg is None:
                logger.warning("Hook '%s' 未注册，跳过", name)
                continue

            if reg.trigger != trigger:
                continue

            result = await self._run_hook(name, reg, stage_name, context)
            results.append(result)

        return results

    async def execute_before_stage(
        self, stage_name: str, context: dict[str, Any]
    ) -> list[HookResult]:
        """执行所有 before_stage 触发类型的 hooks。

        Args:
            stage_name: 当前 stage 名称。
            context: 执行上下文。

        Returns:
            hook 执行结果列表。
        """
        hook_names = [
            name for name, reg in self._hooks.items()
            if reg.trigger == "before_stage"
        ]
        return await self.execute_hooks(hook_names, stage_name, context, "before_stage")

    async def execute_after_stage(
        self, stage_name: str, context: dict[str, Any]
    ) -> list[HookResult]:
        """执行所有 after_stage 触发类型的 hooks。

        Args:
            stage_name: 当前 stage 名称。
            context: 执行上下文。

        Returns:
            hook 执行结果列表。
        """
        hook_names = [
            name for name, reg in self._hooks.items()
            if reg.trigger == "after_stage"
        ]
        return await self.execute_hooks(hook_names, stage_name, context, "after_stage")

    async def _run_hook(
        self,
        name: str,
        reg: HookRegistration,
        stage_name: str,
        context: dict[str, Any],
    ) -> HookResult:
        """执行单个 hook，捕获异常并返回结果。"""
        try:
            if asyncio.iscoroutinefunction(reg.func):
                result = await reg.func(stage_name, context)
            else:
                result = reg.func(stage_name, context)
            return HookResult(
                hook_name=name,
                trigger=reg.trigger,
                success=True,
                result=result,
            )
        except Exception as e:
            logger.error("Hook '%s' 执行失败: %s", name, e)
            return HookResult(
                hook_name=name,
                trigger=reg.trigger,
                success=False,
                error=str(e),
            )
