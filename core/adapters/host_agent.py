"""Generic HostAgentAdapter -- task_packet and cli_fallback execution modes."""

from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..host_agent import (
    HostAgentRuntime, HostCapabilities, HealthStatus,
    TaskPacket, ResultPacket, ArtifactInfo, CommandInfo, VerificationResult,
)


@dataclass
class GenericHostAgentAdapter:
    """Generic host agent adapter.

    Execution modes:
    - task_packet: Writes task.json, polls for result.json
    - cli_fallback: Same as task_packet (file-based protocol)
    - direct: Returns pending, expects host to call back via MCP
    """
    platform_name: str = "generic"
    run_dir: str = "."
    execution_mode: str = "cli_fallback"
    task_file: str = "task.json"
    result_file: str = "result.json"
    max_wait_seconds: int = 600
    poll_interval_seconds: int = 5
    _capabilities: HostCapabilities = field(default_factory=lambda: HostCapabilities(
        read_file=True, write_file=True, edit_file=True, bash=True,
        search=True, subagent=False, browser=False, user_input=True,
    ))

    @property
    def platform(self) -> str:
        return self.platform_name

    @property
    def capabilities(self) -> HostCapabilities:
        return self._capabilities

    def check_health(self) -> HealthStatus:
        missing = []
        run_path = Path(self.run_dir)
        if run_path.exists():
            if not os.access(self.run_dir, os.W_OK):
                missing.append("run_dir not writable")
        else:
            # Check parent directory
            parent = run_path.parent
            if not parent.exists() or not os.access(parent, os.W_OK):
                missing.append("run_dir parent not writable")
        return HealthStatus(
            platform=self.platform_name,
            status="ok" if not missing else "degraded",
            capabilities=self._capabilities,
            missing=missing,
        )

    async def execute_task(self, task: TaskPacket) -> ResultPacket:
        """Execute a task via file-based protocol.

        1. Write task.json to run_dir
        2. Poll for result.json
        3. If timeout, return blocked
        """
        start = time.monotonic()
        task_path = os.path.join(self.run_dir, self.task_file)
        result_path = os.path.join(self.run_dir, self.result_file)

        # Check capabilities
        missing = self._capabilities.missing_for(task.required_tools)
        if missing:
            return ResultPacket(
                task_id=task.task_id,
                status="blocked",
                summary=f"Missing capabilities: {', '.join(missing)}",
                blockers=[f"Platform {self.platform_name} lacks: {', '.join(missing)}"],
                missing_capabilities=missing,
                duration_ms=0,
            )

        # Write task packet
        os.makedirs(self.run_dir, exist_ok=True)
        with open(task_path, "w") as f:
            json.dump(task.to_dict(), f, indent=2, ensure_ascii=False)

        # If direct mode, return pending
        if self.execution_mode == "direct":
            return ResultPacket(
                task_id=task.task_id,
                status="blocked",
                summary="Task written, awaiting host callback",
                blockers=["direct mode: host must call back via MCP"],
                duration_ms=int((time.monotonic() - start) * 1000),
            )

        # Poll for result
        elapsed = 0.0
        while elapsed < self.max_wait_seconds:
            if os.path.exists(result_path):
                try:
                    with open(result_path) as f:
                        data = json.load(f)
                    result = ResultPacket.from_dict(data)
                    # Clean up result file only after successful parse
                    os.remove(result_path)
                    return result
                except Exception as e:
                    return ResultPacket(
                        task_id=task.task_id,
                        status="failed",
                        summary=f"Invalid result.json: {e}",
                        duration_ms=int((time.monotonic() - start) * 1000),
                    )

            await asyncio.sleep(self.poll_interval_seconds)
            elapsed = time.monotonic() - start

        # Timeout -- blocked
        return ResultPacket(
            task_id=task.task_id,
            status="blocked",
            summary=f"Timeout after {self.max_wait_seconds}s waiting for result",
            blockers=[f"No result.json found after {self.max_wait_seconds}s"],
            duration_ms=int((time.monotonic() - start) * 1000),
        )
