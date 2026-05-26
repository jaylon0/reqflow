"""CheckpointManager -- stage boundary checkpoints for resume support."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .models import RunState, StageOutput


class CheckpointManager:
    """Manages stage boundary checkpoints."""

    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.checkpoint_dir = run_dir / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save(self, stage_id: str, output: StageOutput, state: RunState) -> None:
        """Save a checkpoint for a completed stage."""
        checkpoint = {
            "stage_id": stage_id,
            "timestamp": datetime.now().isoformat(),
            "output": output.to_dict(),
            "state": state.to_dict(),
        }
        path = self.checkpoint_dir / f"{stage_id}.json"
        path.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2))

    def restore(self, stage_id: str) -> tuple[dict, dict] | None:
        """Restore a checkpoint by stage ID.

        Returns:
            Tuple of (output_dict, state_dict) or None if not found.
        """
        path = self.checkpoint_dir / f"{stage_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return data["output"], data["state"]

    def list_checkpoints(self) -> list[str]:
        """List all checkpoint stage IDs."""
        return [p.stem for p in sorted(self.checkpoint_dir.glob("*.json"))]

    def get_resume_point(self) -> str | None:
        """Get the latest checkpoint as a resume point."""
        checkpoints = self.list_checkpoints()
        return checkpoints[-1] if checkpoints else None
