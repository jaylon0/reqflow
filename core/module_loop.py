"""ReqFlow Module Loop — 模块级 7 步循环。

每个模块执行：准备→建组件→生成→验收自检→Review→人确认→提交→更新state
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ModuleStep(Enum):
    PREPARE = "prepare"
    BUILD_COMPONENTS = "build"
    GENERATE = "generate"
    SELF_CHECK = "self_check"
    REVIEW = "review"
    HUMAN_CONFIRM = "confirm"
    COMMIT = "commit"
    UPDATE_STATE = "update"


@dataclass
class StepResult:
    step: ModuleStep
    status: str  # done | failed | skipped
    output: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ModuleResult:
    module_name: str
    steps: list[StepResult] = field(default_factory=list)
    status: str = "pending"  # pending | in_progress | completed | failed

    @property
    def completed_steps(self) -> list[ModuleStep]:
        return [s.step for s in self.steps if s.status == "done"]

    @property
    def all_done(self) -> bool:
        required = {ModuleStep.PREPARE, ModuleStep.GENERATE, ModuleStep.SELF_CHECK,
                    ModuleStep.REVIEW, ModuleStep.HUMAN_CONFIRM, ModuleStep.COMMIT, ModuleStep.UPDATE_STATE}
        return required.issubset(set(self.completed_steps))


class ModuleLoop:
    """模块级 7 步循环。核心规则：
    - 每个模块必须走完 7 步
    - Review +1 确认后才开启下一个模块
    - 禁止修改无关逻辑
    - 已完成模块禁止重新生成
    """

    def __init__(self):
        self._completed_modules: list[str] = []
        self._current_module: str | None = None
        self._current_result: ModuleResult | None = None

    def start_module(self, module_name: str) -> ModuleResult:
        """开始一个模块的 7 步循环。"""
        if module_name in self._completed_modules:
            logger.warning("模块 %s 已完成，禁止重新生成", module_name)
            return ModuleResult(module_name=module_name, status="failed",
                                steps=[StepResult(step=ModuleStep.PREPARE, status="failed",
                                                  output="模块已完成，禁止重新生成")])

        self._current_module = module_name
        self._current_result = ModuleResult(module_name=module_name, status="in_progress")
        logger.info("开始模块: %s", module_name)
        return self._current_result

    def complete_step(self, step: ModuleStep, output: str = "") -> StepResult:
        """完成当前模块的一个步骤。"""
        if not self._current_result:
            raise RuntimeError("没有活跃的模块")

        result = StepResult(step=step, status="done", output=output)
        self._current_result.steps.append(result)
        logger.info("模块 %s 完成步骤: %s", self._current_module, step.value)
        return result

    def fail_step(self, step: ModuleStep, output: str = "") -> StepResult:
        """标记当前步骤失败。"""
        if not self._current_result:
            raise RuntimeError("没有活跃的模块")

        result = StepResult(step=step, status="failed", output=output)
        self._current_result.steps.append(result)
        return result

    def finish_module(self) -> ModuleResult:
        """完成当前模块。"""
        if not self._current_result:
            raise RuntimeError("没有活跃的模块")

        if self._current_result.all_done:
            self._current_result.status = "completed"
            self._completed_modules.append(self._current_module)
            logger.info("模块 %s 完成", self._current_module)
        else:
            self._current_result.status = "failed"
            logger.warning("模块 %s 未完成所有步骤", self._current_module)

        result = self._current_result
        self._current_module = None
        self._current_result = None
        return result

    def should_proceed(self, module_result: ModuleResult) -> bool:
        """检查是否可以进入下一个模块。"""
        return module_result.status == "completed"

    def get_completed(self) -> list[str]:
        """获取已完成的模块列表。"""
        return list(self._completed_modules)

    def is_completed(self, module_name: str) -> bool:
        """检查模块是否已完成。"""
        return module_name in self._completed_modules

    def to_dict(self) -> dict[str, Any]:
        """导出为字典。"""
        return {"completed_modules": list(self._completed_modules)}

    def load_from_dict(self, data: dict[str, Any]) -> None:
        """从字典加载。"""
        self._completed_modules = data.get("completed_modules", [])
