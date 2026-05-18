"""HostAgentAdapter - adapter for host agent runtime with task/result packet protocol."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .base import ModelAdapter, ModelResponse, ToolResult, TokenUsage


class HostAgentAdapter(ModelAdapter):
    """Adapter that communicates via TaskPacket/ResultPacket file protocol."""

    def __init__(self, run_dir: str | None = None, timeout_seconds: int = 120):
        self._run_dir = run_dir or ".reqflow/runs/default"
        self._step_count = 0
        self._timeout_seconds = timeout_seconds

    @property
    def name(self) -> str:
        return "host"

    def create_task_packet(
        self,
        stage_id: str,
        stage_name: str,
        prompt: str,
        required_tools: list[str] | None = None,
        expected_artifacts: list[str] | None = None,
        acceptance_criteria: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create and write a task packet for the host agent."""
        packet = {
            "stage_id": stage_id,
            "stage_name": stage_name,
            "prompt": prompt,
            "required_tools": required_tools or [],
            "expected_artifacts": expected_artifacts or [],
            "acceptance_criteria": acceptance_criteria or [],
            "created_at": time.time(),
        }
        task_file = Path(self._run_dir) / "task.json"
        task_file.write_text(json.dumps(packet, indent=2, ensure_ascii=False))
        packet["task_file"] = str(task_file)
        return packet

    def _check_timeout(self) -> bool:
        """Check if the current task has timed out."""
        task_file = Path(self._run_dir) / "task.json"
        if not task_file.exists():
            return False
        try:
            task_data = json.loads(task_file.read_text())
            created_at = task_data.get("created_at", 0)
            if created_at and (time.time() - created_at) > self._timeout_seconds:
                return True
        except (json.JSONDecodeError, OSError):
            pass
        return False

    def _mark_timeout(self) -> None:
        """Mark the current task as timed out and add recovery info."""
        task_file = Path(self._run_dir) / "task.json"
        if not task_file.exists():
            return
        try:
            task_data = json.loads(task_file.read_text())
            task_data["timeout_at"] = time.time()
            task_data["recovery"] = {
                "instructions": "Task timed out. To resume: submit a result.json with status and summary, then call again.",
                "result_file": str(Path(self._run_dir) / "result.json"),
                "task_file": str(task_file),
            }
            task_file.write_text(json.dumps(task_data, indent=2, ensure_ascii=False))
        except (json.JSONDecodeError, OSError):
            pass

    def call(
        self,
        prompt: str,
        tools: list[str] | None = None,
        context: str | None = None,
        system_prompt: str | None = None,
    ) -> ModelResponse:
        self._step_count += 1

        result_file = Path(self._run_dir) / "result.json"
        if result_file.exists():
            try:
                result_data = json.loads(result_file.read_text())
                status = result_data.get("status", "unknown")
                summary = result_data.get("summary", "")
                artifacts = result_data.get("artifacts", [])
                files_changed = result_data.get("files_changed", [])
                result_file.unlink()

                content_parts = [f"[HOST RESULT] Status: {status}"]
                if summary:
                    content_parts.append(f"Summary: {summary}")
                if artifacts:
                    content_parts.append(f"Artifacts: {', '.join(artifacts)}")
                if files_changed:
                    content_parts.append(f"Files changed: {', '.join(files_changed)}")

                return ModelResponse(
                    content="\n".join(content_parts),
                    tool_calls=[],
                    tokens=TokenUsage(),
                    raw=result_data,
                )
            except (json.JSONDecodeError, OSError):
                pass

        # Check for timeout on existing task
        if self._check_timeout():
            self._mark_timeout()
            return ModelResponse(
                content=f"[TIMEOUT] Host agent 未在 {self._timeout_seconds} 秒内响应。"
                        f"请检查 task.json 并提交 result.json 以恢复执行。",
                tool_calls=[],
                tokens=TokenUsage(),
                raw={"status": "timeout", "timeout_seconds": self._timeout_seconds},
            )

        # Create new task packet
        task_packet = self.create_task_packet(
            stage_id=f"step-{self._step_count}",
            stage_name=f"Step {self._step_count}",
            prompt=prompt,
            required_tools=tools or [],
        )

        return ModelResponse(
            content=f"[BLOCKED] 等待 host agent 执行任务。Task packet: {task_packet.get('task_file', 'task.json')}",
            tool_calls=[],
            tokens=TokenUsage(),
            raw={"status": "blocked", "task_packet": task_packet},
        )

    def execute_tool(self, tool_name: str, args: dict[str, Any]) -> ToolResult:
        return ToolResult(
            success=False, output="",
            error="Host adapter delegates tool execution to host agent.",
        )

    def supports_capability(self, capability: str) -> bool:
        return True
