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
                marker = "OK" if st == "success" else "FAIL" if st == "failure" else "TIMEOUT" if st == "timeout" else st.upper()
                lines.append(f"  [{marker:7s}] {name}")

        # Show stage artifacts
        stage_records = status.get("stage_records", [])
        if stage_records:
            lines.append(f"\n--- Stage Artifacts ---")
            for record in stage_records:
                name = record.get("name", "?")
                content = record.get("content", "")
                error = record.get("error", "")
                if content:
                    preview = content[:100] + ("..." if len(content) > 100 else "")
                    lines.append(f"  {name}: {preview}")
                elif error:
                    lines.append(f"  {name}: [ERROR] {error}")

        # Show recovery info if any timeout
        has_timeout = any(st == "timeout" for st in step_statuses.values())
        if has_timeout:
            lines.append(f"\n--- Recovery ---")
            lines.append(f"  检测到超时。请检查 task.json 并提交 result.json 以恢复执行。")
            lines.append(f"  使用: reqflow host-task status <run_dir> 查看详情")

        # Show reports
        reports = status.get("reports", [])
        if reports:
            lines.append(f"\n--- Reports ({len(reports)}) ---")
            for r in reports[-5:]:  # 最近 5 条
                stage = r.get("stage", "?")
                st = r.get("status", "?")
                icon = "OK" if st == "done" else "FAIL" if st == "failed" else "BLOCK" if st == "blocked" else st.upper()
                arts = ", ".join(r.get("artifacts", [])) if r.get("artifacts") else ""
                line = f"  [{icon:5s}] {stage}"
                if arts:
                    line += f" -> {arts}"
                lines.append(line)

        # Show verifications
        verifications = status.get("verifications", [])
        if verifications:
            lines.append(f"\n--- Verifications ({len(verifications)}) ---")
            for v in verifications[-5:]:
                gate = v.get("gate", "?")
                passed = v.get("passed", False)
                icon = "PASS" if passed else "FAIL"
                lines.append(f"  [{icon:4s}] {gate}")
                if v.get("summary"):
                    lines.append(f"         {v['summary']}")

        # Show blockers
        blockers = status.get("blockers", [])
        open_blockers = [b for b in blockers if b.get("status") == "open"]
        if open_blockers:
            lines.append(f"\n--- Blockers ({len(open_blockers)} open) ---")
            for b in open_blockers:
                lines.append(f"  [{b.get('level', '?')}] {b.get('id', '?')}: {b.get('question', '?')}")

        # Show acceptance criteria
        criteria = status.get("acceptance_criteria", [])
        if criteria:
            verified = sum(1 for c in criteria if c.get("status") == "verified")
            lines.append(f"\n--- Acceptance Criteria ({verified}/{len(criteria)} verified) ---")
            for c in criteria:
                st = c.get("status", "pending")
                icon = "x" if st == "verified" else " " if st == "pending" else "!"
                lines.append(f"  [{icon}] {c.get('id', '?')}: {c.get('description', '?')}")

        # Show workflow status
        wf_status = status.get("workflow_status", "")
        if wf_status:
            lines.append(f"\nWorkflow Status: {wf_status}")

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
