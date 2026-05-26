"""StepTracer -- OpenTelemetry-like span model for execution tracing.

Provides structured tracing with parent-child span relationships
and cost tracking for agent operations.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Span:
    """A single trace span representing an operation.

    Attributes:
        name: Name of the operation.
        trace_id: ID of the overall trace (shared across related spans).
        span_id: Unique ID of this span.
        parent_id: ID of the parent span (None for root spans).
        start_time: When the span started.
        end_time: When the span ended (None if still active).
        duration_ms: Duration in milliseconds (calculated on end).
        status: Span status (ok, error, cancelled).
        events: List of timestamped events within this span.
    """

    name: str = ""
    trace_id: str = ""
    span_id: str = ""
    parent_id: str | None = None
    start_time: str = ""
    end_time: str | None = None
    duration_ms: float = 0.0
    status: str = "ok"
    events: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class UsageRecord:
    """Token usage record for an agent operation.

    Attributes:
        agent: Agent name or role.
        model: Model identifier.
        input_tokens: Number of input tokens.
        output_tokens: Number of output tokens.
        timestamp: When the usage was recorded.
    """

    agent: str = ""
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    timestamp: str = ""


class StepTracer:
    """Execution tracer with OpenTelemetry-like span model.

    Manages spans with parent-child relationships and provides
    trace export capabilities.
    """

    def __init__(self):
        self._spans: dict[str, Span] = {}
        self._traces: dict[str, list[str]] = {}  # trace_id -> [span_ids]

    def start_span(self, name: str, parent: Span | None = None) -> Span:
        """Start a new span.

        Args:
            name: Name of the operation.
            parent: Parent span (None for root spans).

        Returns:
            The newly created Span.
        """
        trace_id = parent.trace_id if parent else str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        parent_id = parent.span_id if parent else None

        span = Span(
            name=name,
            trace_id=trace_id,
            span_id=span_id,
            parent_id=parent_id,
            start_time=datetime.now().isoformat(),
            status="ok",
        )

        self._spans[span_id] = span

        if trace_id not in self._traces:
            self._traces[trace_id] = []
        self._traces[trace_id].append(span_id)

        return span

    def end_span(self, span: Span, status: str = "ok") -> None:
        """End a span and calculate duration.

        Args:
            span: The span to end.
            status: Final status (ok, error, cancelled).
        """
        span.end_time = datetime.now().isoformat()
        span.status = status

        # Calculate duration
        try:
            start = datetime.fromisoformat(span.start_time)
            end = datetime.fromisoformat(span.end_time)
            span.duration_ms = (end - start).total_seconds() * 1000
        except (ValueError, TypeError):
            span.duration_ms = 0.0

    def add_event(self, span: Span, name: str, attributes: dict[str, Any] | None = None) -> None:
        """Add a timestamped event to a span.

        Args:
            span: The span to add the event to.
            name: Event name.
            attributes: Optional key-value attributes.
        """
        event = {
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "attributes": attributes or {},
        }
        span.events.append(event)

    def get_span(self, span_id: str) -> Span | None:
        """Get a span by ID."""
        return self._spans.get(span_id)

    def get_trace(self, trace_id: str) -> list[Span]:
        """Get all spans in a trace, ordered by start time."""
        span_ids = self._traces.get(trace_id, [])
        spans = [self._spans[sid] for sid in span_ids if sid in self._spans]
        return sorted(spans, key=lambda s: s.start_time)

    def get_children(self, span: Span) -> list[Span]:
        """Get all direct children of a span."""
        return [s for s in self._spans.values() if s.parent_id == span.span_id]

    def export_trace(self, trace_id: str) -> dict[str, Any]:
        """Export a trace as a serializable dict.

        Args:
            trace_id: The trace ID to export.

        Returns:
            Dict with trace_id and list of span dicts.
        """
        spans = self.get_trace(trace_id)
        return {
            "trace_id": trace_id,
            "spans": [
                {
                    "name": s.name,
                    "span_id": s.span_id,
                    "parent_id": s.parent_id,
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "duration_ms": s.duration_ms,
                    "status": s.status,
                    "events": s.events,
                }
                for s in spans
            ],
        }


class CostTracker:
    """Tracks token usage and cost for agent operations.

    Records usage per agent/model and provides summary statistics.
    """

    # Default cost per 1K tokens (USD)
    DEFAULT_COST_PER_1K_INPUT = 0.003
    DEFAULT_COST_PER_1K_OUTPUT = 0.015

    def __init__(
        self,
        cost_per_1k_input: float | None = None,
        cost_per_1k_output: float | None = None,
    ):
        self._records: list[UsageRecord] = []
        self.cost_per_1k_input = cost_per_1k_input or self.DEFAULT_COST_PER_1K_INPUT
        self.cost_per_1k_output = cost_per_1k_output or self.DEFAULT_COST_PER_1K_OUTPUT

    def record_usage(
        self,
        agent: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """Record token usage for an agent operation.

        Args:
            agent: Agent name or role.
            model: Model identifier.
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.
        """
        record = UsageRecord(
            agent=agent,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            timestamp=datetime.now().isoformat(),
        )
        self._records.append(record)

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of all recorded usage.

        Returns:
            Dict with total tokens, cost breakdown, and per-agent stats.
        """
        if not self._records:
            return {
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
                "estimated_cost_usd": 0.0,
                "by_agent": {},
                "by_model": {},
            }

        total_input = sum(r.input_tokens for r in self._records)
        total_output = sum(r.output_tokens for r in self._records)

        # Per-agent breakdown
        by_agent: dict[str, dict] = {}
        for r in self._records:
            if r.agent not in by_agent:
                by_agent[r.agent] = {"input_tokens": 0, "output_tokens": 0, "calls": 0}
            by_agent[r.agent]["input_tokens"] += r.input_tokens
            by_agent[r.agent]["output_tokens"] += r.output_tokens
            by_agent[r.agent]["calls"] += 1

        # Per-model breakdown
        by_model: dict[str, dict] = {}
        for r in self._records:
            if r.model not in by_model:
                by_model[r.model] = {"input_tokens": 0, "output_tokens": 0, "calls": 0}
            by_model[r.model]["input_tokens"] += r.input_tokens
            by_model[r.model]["output_tokens"] += r.output_tokens
            by_model[r.model]["calls"] += 1

        # Cost calculation
        cost = (
            (total_input / 1000) * self.cost_per_1k_input
            + (total_output / 1000) * self.cost_per_1k_output
        )

        return {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "estimated_cost_usd": round(cost, 6),
            "by_agent": by_agent,
            "by_model": by_model,
        }
