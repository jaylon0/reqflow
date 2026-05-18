"""StateManager - state persistence, checkpoints, session, and memory."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class Session:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    working_context: dict[str, Any] = field(default_factory=dict)
    conversation_summary: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())

    def touch(self):
        self.last_active = datetime.now().isoformat()


@dataclass
class Memory:
    short_term: list[dict[str, Any]] = field(default_factory=list)
    long_term: list[dict[str, Any]] = field(default_factory=list)
    entity: list[dict[str, Any]] = field(default_factory=list)

    def add_short_term(self, key: str, value: Any):
        self.short_term.append({
            "key": key,
            "value": value,
            "timestamp": datetime.now().isoformat(),
        })

    def add_long_term(self, lesson: str, source: str, category: str = ""):
        self.long_term.append({
            "lesson": lesson,
            "source": source,
            "category": category,
            "timestamp": datetime.now().isoformat(),
        })

    def add_entity(self, name: str, entity_type: str, location: str, dependencies: list[str] | None = None):
        self.entity.append({
            "name": name,
            "type": entity_type,
            "location": location,
            "dependencies": dependencies or [],
            "timestamp": datetime.now().isoformat(),
        })


@dataclass
class Checkpoint:
    checkpoint_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str = ""
    stage: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    state_snapshot: str = ""
    context_snapshot: str = ""
    log_snapshot: str = ""


@dataclass
class RunState:
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    current_stage: str = ""
    completed_modules: list[str] = field(default_factory=list)
    pending_confirmations: list[str] = field(default_factory=list)
    spec_status: str = "draft"  # draft|approved|archived
    quality_gates: dict[str, Any] = field(default_factory=dict)
    session: Session = field(default_factory=Session)
    memory: Memory = field(default_factory=Memory)
    checkpoints: list[Checkpoint] = field(default_factory=list)
    lessons_learned: list[str] = field(default_factory=list)
    agent_execution_log: list[dict[str, Any]] = field(default_factory=list)
    stage_records: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class StateManager:
    """Manages run state, checkpoints, session, and memory."""

    def __init__(self, run_dir: str):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir = self.run_dir / "checkpoints"
        self.checkpoint_dir.mkdir(exist_ok=True)
        self._state: RunState | None = None

    @property
    def state(self) -> RunState:
        if self._state is None:
            self._state = self.load_state()
        return self._state

    def save_state(self, state: RunState | None = None):
        """Save current state to state.json."""
        s = state or self.state
        s.updated_at = datetime.now().isoformat()
        state_file = self.run_dir / "state.json"
        state_file.write_text(json.dumps(asdict(s), indent=2, ensure_ascii=False))

    def load_state(self) -> RunState:
        """Load state from state.json, or create a new one."""
        state_file = self.run_dir / "state.json"
        if state_file.exists():
            data = json.loads(state_file.read_text())
            return self._from_dict(data)
        return RunState()

    def _from_dict(self, data: dict) -> RunState:
        """Reconstruct RunState from a dict."""
        session_data = data.pop("session", {})
        memory_data = data.pop("memory", {})
        checkpoints_data = data.pop("checkpoints", [])

        session = Session(**session_data) if session_data else Session()
        memory = Memory(**memory_data) if memory_data else Memory()
        checkpoints = [Checkpoint(**c) for c in checkpoints_data]

        return RunState(
            session=session,
            memory=memory,
            checkpoints=checkpoints,
            **{k: v for k, v in data.items() if k not in ("session", "memory", "checkpoints")},
        )

    def update_stage(self, stage: str):
        """Update the current stage and save."""
        self.state.current_stage = stage
        self.save_state()

    def complete_module(self, module: str):
        """Mark a module as completed."""
        if module not in self.state.completed_modules:
            self.state.completed_modules.append(module)
            self.save_state()

    def create_checkpoint(self, stage: str, context: dict[str, Any] | None = None) -> Checkpoint:
        """Create a checkpoint for the current state."""
        checkpoint = Checkpoint(
            run_id=self.state.run_id,
            stage=stage,
        )

        # Save state snapshot
        checkpoint_dir = self.checkpoint_dir / checkpoint.checkpoint_id
        checkpoint_dir.mkdir(exist_ok=True)

        state_snapshot = checkpoint_dir / "state.json"
        state_snapshot.write_text(json.dumps(asdict(self.state), indent=2, ensure_ascii=False))
        checkpoint.state_snapshot = str(state_snapshot)

        # Save context snapshot if provided
        if context:
            context_snapshot = checkpoint_dir / "context.json"
            context_snapshot.write_text(json.dumps(context, indent=2, ensure_ascii=False))
            checkpoint.context_snapshot = str(context_snapshot)

        self.state.checkpoints.append(checkpoint)
        self.save_state()
        return checkpoint

    def restore_checkpoint(self, checkpoint_id: str) -> tuple[RunState, dict[str, Any] | None]:
        """Restore state and context from a checkpoint."""
        checkpoint_dir = self.checkpoint_dir / checkpoint_id
        if not checkpoint_dir.exists():
            raise FileNotFoundError(f"Checkpoint {checkpoint_id} not found")

        # Restore state
        state_file = checkpoint_dir / "state.json"
        if state_file.exists():
            data = json.loads(state_file.read_text())
            self._state = self._from_dict(data)

        # Restore context
        context = None
        context_file = checkpoint_dir / "context.json"
        if context_file.exists():
            context = json.loads(context_file.read_text())

        return self.state, context

    def list_checkpoints(self) -> list[Checkpoint]:
        """List all checkpoints."""
        return self.state.checkpoints

    def log_agent_execution(self, agent_id: str, task: str, result: str, duration_ms: int = 0):
        """Log an agent execution event."""
        self.state.agent_execution_log.append({
            "agent_id": agent_id,
            "task": task,
            "result": result,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
        })
        self.save_state()

    def cleanup(self):
        """Clean up the run directory."""
        import shutil
        if self.run_dir.exists():
            shutil.rmtree(self.run_dir)
