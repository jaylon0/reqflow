"""Tracer - hierarchical trace/span execution tracking."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class Span:
    span_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: str | None = None
    name: str = ""
    input: Any = None
    output: Any = None
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: str | None = None
    duration_ms: int = 0
    tokens: TokenUsage = field(default_factory=TokenUsage)
    status: str = "running"  # running|success|failure|error
    metadata: dict[str, Any] = field(default_factory=dict)

    def finish(self, output: Any = None, status: str = "success", tokens: TokenUsage | None = None):
        self.end_time = datetime.now().isoformat()
        self.output = output
        self.status = status
        if tokens:
            self.tokens = tokens
        # Calculate duration
        start = datetime.fromisoformat(self.start_time)
        end = datetime.fromisoformat(self.end_time)
        self.duration_ms = int((end - start).total_seconds() * 1000)


@dataclass
class Trace:
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str = ""
    name: str = ""
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: str | None = None
    spans: list[Span] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class Tracer:
    """Hierarchical trace/span execution tracker."""

    def __init__(self, run_id: str, output_dir: str | None = None):
        self.run_id = run_id
        self.output_dir = Path(output_dir) if output_dir else None
        self._trace = Trace(run_id=run_id)
        self._active_spans: dict[str, Span] = {}

    def start_span(self, name: str, parent_id: str | None = None, input_data: Any = None) -> Span:
        """Start a new span."""
        # Auto-detect parent from active spans
        if parent_id is None and self._active_spans:
            # Use the most recently started span as parent
            parent_id = list(self._active_spans.keys())[-1]

        span = Span(
            name=name,
            parent_id=parent_id,
            input=input_data,
        )
        self._active_spans[span.span_id] = span
        self._trace.spans.append(span)
        return span

    def end_span(self, span_id: str, output: Any = None, status: str = "success", tokens: TokenUsage | None = None):
        """End a span."""
        span = self._active_spans.pop(span_id, None)
        if span:
            span.finish(output=output, status=status, tokens=tokens)

    def get_span(self, span_id: str) -> Span | None:
        """Get a span by ID."""
        return self._active_spans.get(span_id)

    def finish_trace(self):
        """Finish the trace."""
        self._trace.end_time = datetime.now().isoformat()
        # End any remaining active spans
        for span in list(self._active_spans.values()):
            span.finish(status="incomplete")

    def export(self, path: str | None = None):
        """Export trace to JSON file."""
        self.finish_trace()
        output_path = Path(path) if path else self.output_dir
        if output_path is None:
            raise ValueError("No output path specified")

        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        trace_file = output_path / f"trace-{self._trace.trace_id}.json"
        trace_file.write_text(json.dumps(asdict(self._trace), indent=2, ensure_ascii=False))
        return str(trace_file)

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the trace."""
        total_spans = len(self._trace.spans)
        failed_spans = sum(1 for s in self._trace.spans if s.status in ("failure", "error"))
        total_tokens = sum(s.tokens.input_tokens + s.tokens.output_tokens for s in self._trace.spans)
        total_duration = sum(s.duration_ms for s in self._trace.spans)

        return {
            "trace_id": self._trace.trace_id,
            "run_id": self.run_id,
            "total_spans": total_spans,
            "failed_spans": failed_spans,
            "total_tokens": total_tokens,
            "total_duration_ms": total_duration,
        }
