"""Session management for cross-turn context persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from datetime import datetime


class Session:
    """Session-level state persistence across workflow turns."""

    def __init__(self, session_id: str, storage_dir: str):
        self.session_id = session_id
        self.storage_dir = Path(storage_dir)
        self._context: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []

    def save_context(self, key: str, value: Any) -> None:
        """Save a piece of context for this session."""
        self._context[key] = value

    def get_context(self, key: str) -> Any:
        """Retrieve context from this session. Returns None if not found."""
        return self._context.get(key)

    def add_history(self, step: str, result: str) -> None:
        """Add an entry to the session history."""
        self.history.append({
            "step": step,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        })

    def summarize(self, max_length: int = 500) -> str:
        """Generate a compressed summary of session history."""
        if not self.history:
            return ""
        parts = []
        for entry in self.history:
            parts.append(f"[{entry['step']}] {entry['result'][:100]}")
        summary = " | ".join(parts)
        if len(summary) > max_length:
            summary = summary[:max_length - 3] + "..."
        return summary

    def save(self) -> None:
        """Save session state to disk."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "session_id": self.session_id,
            "context": self._context,
            "history": self.history,
        }
        path = self._session_path()
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self) -> None:
        """Load session state from disk."""
        path = self._session_path()
        if not path.exists():
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        self._context = data.get("context", {})
        self.history = data.get("history", [])

    @staticmethod
    def list_sessions(storage_dir: str) -> list[str]:
        """List all session IDs in the storage directory."""
        dir_path = Path(storage_dir)
        if not dir_path.is_dir():
            return []
        prefix = "session-"
        return sorted(
            p.stem[len(prefix):]
            for p in dir_path.glob("session-*.json")
            if p.stem.startswith(prefix)
        )

    def _session_path(self) -> Path:
        return self.storage_dir / f"session-{self.session_id}.json"
