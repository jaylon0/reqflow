"""StateManager - state persistence, checkpoints, session, memory, and experience cache."""

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
class ExperienceEntry:
    """单条经验缓存。"""
    stage: str
    pattern: str  # 成功/失败模式描述
    outcome: str  # "success" | "failure" | "partial"
    confidence: float = 0.0  # 经验置信度 0-1
    context: str = ""  # 适用场景
    tags: list[str] = field(default_factory=list)
    source_run: str = ""  # 来源运行 ID
    reuse_count: int = 0  # 被复用次数
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class ExperienceCache:
    """经验缓存 — 跨运行的阶段经验复用。"""

    def __init__(self, cache_dir: str = ".reqflow/experience"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_file = self.cache_dir / "experience.json"
        self._entries: list[ExperienceEntry] = []
        self._load()

    def _load(self):
        """从文件加载经验缓存。"""
        if self._cache_file.exists():
            try:
                data = json.loads(self._cache_file.read_text(encoding="utf-8"))
                self._entries = [ExperienceEntry(**e) for e in data]
            except Exception:
                self._entries = []

    def _save(self):
        """保存经验缓存到文件。"""
        self._cache_file.write_text(
            json.dumps([asdict(e) for e in self._entries], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add(self, entry: ExperienceEntry) -> None:
        """添加经验条目。"""
        self._entries.append(entry)
        self._save()

    def query(
        self,
        stage: str = "",
        outcome: str = "",
        tags: list[str] | None = None,
        min_confidence: float = 0.0,
        limit: int = 10,
    ) -> list[ExperienceEntry]:
        """查询经验缓存。"""
        results = self._entries

        if stage:
            results = [e for e in results if e.stage == stage]
        if outcome:
            results = [e for e in results if e.outcome == outcome]
        if tags:
            tag_set = set(tags)
            results = [e for e in results if tag_set.intersection(e.tags)]
        if min_confidence > 0:
            results = [e for e in results if e.confidence >= min_confidence]

        # 按置信度和复用次数排序
        results.sort(key=lambda e: (e.confidence, e.reuse_count), reverse=True)
        return results[:limit]

    def record_reuse(self, index: int) -> None:
        """记录经验被复用。"""
        if 0 <= index < len(self._entries):
            self._entries[index].reuse_count += 1
            self._save()

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计。"""
        if not self._entries:
            return {"total": 0, "by_stage": {}, "by_outcome": {}}

        by_stage: dict[str, int] = {}
        by_outcome: dict[str, int] = {}
        for e in self._entries:
            by_stage[e.stage] = by_stage.get(e.stage, 0) + 1
            by_outcome[e.outcome] = by_outcome.get(e.outcome, 0) + 1

        return {
            "total": len(self._entries),
            "by_stage": by_stage,
            "by_outcome": by_outcome,
            "avg_confidence": sum(e.confidence for e in self._entries) / len(self._entries),
        }

    def format_summary(self, stage: str = "") -> str:
        """格式化经验摘要。"""
        entries = self.query(stage=stage, limit=5) if stage else self._entries[:5]
        if not entries:
            return "无经验缓存"

        lines = [f"经验缓存 ({len(entries)} 条):"]
        for e in entries:
            icon = {"success": "✅", "failure": "❌", "partial": "⚠️"}.get(e.outcome, "?")
            lines.append(f"  {icon} [{e.stage}] {e.pattern[:50]} (置信度: {e.confidence:.0%}, 复用: {e.reuse_count}次)")
        return "\n".join(lines)


@dataclass
class Checkpoint:
    checkpoint_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str = ""
    stage: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    state_snapshot: str = ""
    context_snapshot: str = ""
    log_snapshot: str = ""


_RUNSTATE_FIELDS: set[str] = set()

@dataclass
class RunState:
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    requirement: str = ""
    routing_level: str = ""
    change_name: str = ""
    stages: list[str] = field(default_factory=list)
    current_stage: str = ""
    current_stage_index: int = 0  # index in stages list
    steps_executed: int = 0  # total MCP tool calls executed
    status: str = "active"  # active|completed|failed
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
    stage_experiences: list[dict[str, Any]] = field(default_factory=list)  # V7 经验缓存
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    extra: dict[str, Any] = field(default_factory=dict)  # 未知字段存这里


# Build field set after class definition
_RUNSTATE_FIELDS = {f.name for f in RunState.__dataclass_fields__.values()}


class StateManager:
    """Manages run state, checkpoints, session, and memory."""

    def __init__(self, run_dir: str, run_id: str | None = None):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir = self.run_dir / "checkpoints"
        self.checkpoint_dir.mkdir(exist_ok=True)
        self._run_id = run_id
        self._state: RunState | None = None

    @property
    def state(self) -> RunState:
        if self._state is None:
            self._state = self.load_state()
        return self._state

    def save_state(self, state: RunState | dict | None = None):
        """Save current state to state.json."""
        if isinstance(state, dict):
            # Merge dict into current state
            s = self.state
            for k, v in state.items():
                if k in _RUNSTATE_FIELDS and k != "extra":
                    setattr(s, k, v)
                else:
                    s.extra[k] = v
        else:
            s = state or self.state
        s.updated_at = datetime.now().isoformat()
        state_file = self.run_dir / "state.json"
        data = asdict(s)
        # Flatten extra into top-level for backward compatibility
        extra = data.pop("extra", {})
        data.update(extra)
        state_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def load_state(self) -> RunState:
        """Load state from state.json, or create a new one."""
        state_file = self.run_dir / "state.json"
        if state_file.exists():
            data = json.loads(state_file.read_text())
            return self._from_dict(data)
        return RunState(run_id=self._run_id) if self._run_id else RunState()

    def _from_dict(self, data: dict) -> RunState:
        """Reconstruct RunState from a dict."""
        session_data = data.pop("session", {})
        memory_data = data.pop("memory", {})
        checkpoints_data = data.pop("checkpoints", [])

        session = Session(**session_data) if session_data else Session()
        memory = Memory(**memory_data) if memory_data else Memory()
        checkpoints = [Checkpoint(**c) for c in checkpoints_data]

        known = {}
        extra = {}
        for k, v in data.items():
            if k in _RUNSTATE_FIELDS:
                known[k] = v
            else:
                extra[k] = v
        known["extra"] = extra

        return RunState(
            session=session,
            memory=memory,
            checkpoints=checkpoints,
            **known,
        )

    def update_stage(self, stage: str):
        """Update the current stage and save."""
        self.state.current_stage = stage
        self.save_state()

    def update_stage_progress(self, stage: str, stage_index: int | None = None):
        """Update current stage and index, increment steps."""
        self.state.current_stage = stage
        if stage_index is not None:
            self.state.current_stage_index = stage_index
        self.state.steps_executed += 1
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
