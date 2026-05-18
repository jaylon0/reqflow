"""Terminal dashboard for workflow observability."""

from __future__ import annotations

from typing import Any


class Dashboard:
    """Terminal-based workflow status display."""

    def __init__(self, run_dir: str):
        self.run_dir = run_dir

    def format_status(self, status: dict[str, Any]) -> str:
        """Format engine status as readable text."""
        lines = [
            f"=== ReqFlow Dashboard ===",
            f"Run:     {status.get('run_id', 'unknown')}",
            f"Config:  {status.get('config', 'unknown')} ({status.get('adapter', 'unknown')})",
            f"Stage:   {status.get('current_stage', 'none')}",
            f"Steps:   {status.get('steps_executed', 0)} executed",
        ]

        completed = status.get("completed_modules", [])
        if completed:
            lines.append(f"Done:    {', '.join(completed)}")

        step_statuses = status.get("step_statuses", {})
        if step_statuses:
            lines.append(f"\n--- Step Status ---")
            for name, st in step_statuses.items():
                marker = "OK" if st == "success" else "FAIL" if st == "failure" else st.upper()
                lines.append(f"  [{marker:6s}] {name}")

        lines.append(f"\nCheckpoints: {status.get('checkpoints', 0)}")
        lines.append(f"Memory:      {status.get('memory_entries', 0)} entries")

        return "\n".join(lines)

    def format_trace(self, trace_data: dict[str, Any]) -> str:
        """Format trace data as readable text."""
        spans = trace_data.get("spans", [])
        if not spans:
            return "No trace data."

        lines = ["=== Trace Timeline ==="]
        for span in spans:
            name = span.get("name", "unknown")
            duration = span.get("duration_ms", 0)
            status = span.get("status", "unknown")
            marker = "OK" if status == "success" else "ERR"
            lines.append(f"  [{marker}] {name} ({duration}ms)")

        total = sum(s.get("duration_ms", 0) for s in spans)
        lines.append(f"\nTotal: {total}ms across {len(spans)} spans")

        return "\n".join(lines)

    def rich_render(self, status: dict[str, Any]) -> None:
        """Render status using rich library (if available). Falls back to plain text."""
        try:
            from rich.console import Console
            from rich.table import Table

            console = Console()
            table = Table(title="ReqFlow Dashboard")
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Run ID", str(status.get("run_id", "")))
            table.add_row("Config", f"{status.get('config', '')} ({status.get('adapter', '')})")
            table.add_row("Stage", str(status.get("current_stage", "")))
            table.add_row("Steps", str(status.get("steps_executed", 0)))
            table.add_row("Checkpoints", str(status.get("checkpoints", 0)))

            console.print(table)
        except ImportError:
            print(self.format_status(status))
