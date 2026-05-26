"""WorkflowEngine -- core engine that drives stage execution."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .models import RunState, Stage, StageOutput, StageState, ValidationResult
from .output_validator import OutputValidator
from .stage_executor import StageExecutor

logger = logging.getLogger(__name__)


@dataclass
class Workflow:
    """Workflow definition."""
    name: str
    version: str
    stages: list[Stage]


@dataclass
class RunResult:
    """Result of a workflow run."""
    status: str  # "completed" | "paused" | "failed"
    state: RunState
    error: str | None = None


class WorkflowEngine:
    """Core engine -- drives stage execution and validates outputs."""

    def __init__(
        self,
        executor: StageExecutor,
        validator: OutputValidator | None = None,
        checkpoint_dir: Path | None = None,
    ):
        self.executor = executor
        self.validator = validator or OutputValidator()
        self.checkpoint_dir = checkpoint_dir
        self._states: dict[str, RunState] = {}

    async def run(
        self,
        requirement: str,
        workflow: Workflow,
        routing_level: str = "L3",
    ) -> RunResult:
        """Execute a full workflow."""
        run_id = f"run-{workflow.name}"
        state = RunState(
            run_id=run_id,
            requirement=requirement,
            routing_level=routing_level,
            stages=[
                StageState(stage_id=s.id, status="pending")
                for s in workflow.stages
            ],
        )
        self._states[run_id] = state

        for stage in workflow.stages:
            state.current_stage = stage.id

            # Mark stage as running
            for s in state.stages:
                if s.stage_id == stage.id:
                    s.status = "running"
                    s.attempts += 1
                    break

            try:
                # Build prompt
                prompt = self._build_stage_prompt(stage, state)

                # Execute stage
                output = await self.executor.execute(stage, prompt, state)

                # Validate output
                validation = self.validator.validate(stage.id, output)

                if not validation.passed:
                    # Attempt repair
                    output, validation = await self._repair(
                        stage, output, validation, state
                    )

                # Save checkpoint
                if self.checkpoint_dir:
                    self._save_checkpoint(stage.id, output, state)

                # Update state
                state.mark_stage_completed(stage.id, output, validation)

            except Exception as e:
                logger.error("Stage %s failed: %s", stage.id, e)
                for s in state.stages:
                    if s.stage_id == stage.id:
                        s.status = "failed"
                        break
                state.status = "failed"
                return RunResult(status="failed", state=state, error=str(e))

        state.status = "completed"
        return RunResult(status="completed", state=state)

    def get_state(self, run_id: str) -> RunState | None:
        """Get run state by ID."""
        return self._states.get(run_id)

    # --- Internal ---

    def _build_stage_prompt(self, stage: Stage, state: RunState) -> str:
        """Build the prompt for a stage."""
        sections = [
            f"# 阶段: {stage.name}",
            f"任务: {stage.task}",
            f"需求: {state.requirement}",
        ]

        # Previous stage conclusions
        for prev in state.completed_stages:
            if prev.output and prev.output.analysis:
                sections.append(
                    f"## 前序阶段 {prev.stage_id} 结论\n"
                    f"{prev.output.analysis.summary[:500]}"
                )

        return "\n\n".join(sections)

    async def _repair(
        self,
        stage: Stage,
        output: StageOutput,
        validation: ValidationResult,
        state: RunState,
    ) -> tuple[StageOutput, ValidationResult]:
        """Repair loop -- attempt to fix validation failures."""
        max_rounds = 3
        for _round_num in range(max_rounds):
            repair_prompt = self._build_repair_prompt(stage, output, validation)
            output = await self.executor.execute_with_repair(stage, repair_prompt)
            validation = self.validator.validate(stage.id, output)
            if validation.passed:
                break

        return output, validation

    @staticmethod
    def _build_repair_prompt(
        stage: Stage,
        output: StageOutput,
        validation: ValidationResult,
    ) -> str:
        """Build a repair prompt from validation issues."""
        issues_text = "\n".join(
            f"- [{i.code}] {i.message}" for i in validation.issues
        )
        return f"""
## 修复请求

阶段 {stage.name} 的产出有以下问题：

{issues_text}

请修复以上问题后重新输出。
"""

    def _save_checkpoint(
        self, stage_id: str, output: StageOutput, state: RunState
    ) -> None:
        """Save a checkpoint for the stage."""
        if self.checkpoint_dir:
            self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
            path = self.checkpoint_dir / f"{stage_id}.json"
            path.write_text(
                json.dumps(output.to_dict(), ensure_ascii=False, indent=2)
            )
