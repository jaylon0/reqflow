"""EngineMCPBridge -- read-only MCP query interface for the Engine."""

from __future__ import annotations

from .workflow_engine import WorkflowEngine


class EngineMCPBridge:
    """Read-only MCP bridge -- only exposes query and user interaction.

    All control logic lives inside the Engine. MCP tools can only
    query state and record user decisions.
    """

    def __init__(self, engine: WorkflowEngine):
        self.engine = engine

    async def handle_status(self, run_id: str) -> dict:
        """Query run status."""
        state = self.engine.get_state(run_id)
        if not state:
            return {"error": f"Run not found: {run_id}"}
        return {
            "run_id": run_id,
            "status": state.status,
            "current_stage": state.current_stage,
            "progress": f"{len(state.completed_stages)}/{state.total_stages}",
        }

    async def handle_accept(self, run_id: str) -> dict:
        """User accepts the run."""
        state = self.engine.get_state(run_id)
        if not state:
            return {"error": f"Run not found: {run_id}"}
        state.status = "accepted"
        return {"status": "accepted"}

    async def handle_reject(self, run_id: str, reason: str) -> dict:
        """User rejects the run."""
        state = self.engine.get_state(run_id)
        if not state:
            return {"error": f"Run not found: {run_id}"}
        state.status = "rejected"
        state.rejection_reason = reason
        return {"status": "rejected", "reason": reason}

    async def handle_checkpoint_list(self, run_id: str) -> dict:
        """List checkpoints for a run."""
        state = self.engine.get_state(run_id)
        if not state:
            return {"error": f"Run not found: {run_id}"}
        if self.engine.checkpoint_dir and self.engine.checkpoint_dir.exists():
            checkpoints = [
                p.stem for p in sorted(self.engine.checkpoint_dir.glob("*.json"))
            ]
            return {"checkpoints": checkpoints}
        return {"checkpoints": []}
