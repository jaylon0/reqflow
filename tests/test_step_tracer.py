"""Tests for StepTracer and CostTracker."""

from __future__ import annotations

import pytest
from unittest.mock import patch

from core.step_tracer import StepTracer, CostTracker, Span


# ---------------------------------------------------------------------------
# StepTracer tests
# ---------------------------------------------------------------------------


class TestStepTracer:
    """Tests for StepTracer."""

    def test_start_span_creates_span(self):
        tracer = StepTracer()
        span = tracer.start_span("test_operation")

        assert span.name == "test_operation"
        assert span.span_id  # Should have an ID
        assert span.trace_id  # Should have a trace ID
        assert span.parent_id is None  # Root span
        assert span.start_time  # Should have start time
        assert span.end_time is None  # Not ended yet

    def test_parent_child_span_relationship(self):
        tracer = StepTracer()
        parent = tracer.start_span("parent_operation")
        child = tracer.start_span("child_operation", parent=parent)

        assert child.parent_id == parent.span_id
        assert child.trace_id == parent.trace_id  # Same trace

    def test_end_span_sets_duration(self):
        tracer = StepTracer()
        span = tracer.start_span("test_operation")

        # Small delay to ensure non-zero duration
        import time
        time.sleep(0.01)

        tracer.end_span(span, status="ok")

        assert span.end_time is not None
        assert span.duration_ms > 0
        assert span.status == "ok"

    def test_end_span_with_error_status(self):
        tracer = StepTracer()
        span = tracer.start_span("failing_operation")
        tracer.end_span(span, status="error")

        assert span.status == "error"

    def test_add_event(self):
        tracer = StepTracer()
        span = tracer.start_span("test_operation")

        tracer.add_event(span, "checkpoint", {"step": 1})
        tracer.add_event(span, "validation", {"result": "pass"})

        assert len(span.events) == 2
        assert span.events[0]["name"] == "checkpoint"
        assert span.events[0]["attributes"]["step"] == 1

    def test_get_span(self):
        tracer = StepTracer()
        span = tracer.start_span("test_operation")

        retrieved = tracer.get_span(span.span_id)
        assert retrieved is span

    def test_get_nonexistent_span(self):
        tracer = StepTracer()
        assert tracer.get_span("nonexistent") is None

    def test_get_trace(self):
        tracer = StepTracer()
        parent = tracer.start_span("parent")
        child1 = tracer.start_span("child1", parent=parent)
        child2 = tracer.start_span("child2", parent=parent)

        trace = tracer.get_trace(parent.trace_id)
        assert len(trace) == 3

    def test_get_children(self):
        tracer = StepTracer()
        parent = tracer.start_span("parent")
        child1 = tracer.start_span("child1", parent=parent)
        child2 = tracer.start_span("child2", parent=parent)
        grandchild = tracer.start_span("grandchild", parent=child1)

        children = tracer.get_children(parent)
        assert len(children) == 2
        assert child1 in children
        assert child2 in children

    def test_export_trace(self):
        tracer = StepTracer()
        parent = tracer.start_span("parent")
        child = tracer.start_span("child", parent=parent)
        tracer.add_event(parent, "test_event", {"key": "value"})
        tracer.end_span(child)

        exported = tracer.export_trace(parent.trace_id)

        assert exported["trace_id"] == parent.trace_id
        assert len(exported["spans"]) == 2
        # Check span structure
        span_data = exported["spans"][0]
        assert "name" in span_data
        assert "span_id" in span_data
        assert "parent_id" in span_data
        assert "duration_ms" in span_data
        assert "events" in span_data


# ---------------------------------------------------------------------------
# CostTracker tests
# ---------------------------------------------------------------------------


class TestCostTracker:
    """Tests for CostTracker."""

    def test_record_usage(self):
        tracker = CostTracker()
        tracker.record_usage("dev-agent", "claude-3", 1000, 500)

        summary = tracker.get_summary()
        assert summary["total_input_tokens"] == 1000
        assert summary["total_output_tokens"] == 500
        assert summary["total_tokens"] == 1500

    def test_cost_calculation(self):
        tracker = CostTracker(cost_per_1k_input=0.01, cost_per_1k_output=0.03)
        tracker.record_usage("agent", "model", 1000, 1000)

        summary = tracker.get_summary()
        # 1000/1000 * 0.01 + 1000/1000 * 0.03 = 0.04
        assert summary["estimated_cost_usd"] == pytest.approx(0.04, abs=0.001)

    def test_multiple_records(self):
        tracker = CostTracker()
        tracker.record_usage("agent-a", "model-1", 500, 200)
        tracker.record_usage("agent-b", "model-1", 300, 100)
        tracker.record_usage("agent-a", "model-2", 400, 150)

        summary = tracker.get_summary()
        assert summary["total_input_tokens"] == 1200
        assert summary["total_output_tokens"] == 450
        assert summary["total_tokens"] == 1650

    def test_by_agent_breakdown(self):
        tracker = CostTracker()
        tracker.record_usage("dev", "model", 100, 50)
        tracker.record_usage("dev", "model", 200, 100)
        tracker.record_usage("qa", "model", 150, 75)

        summary = tracker.get_summary()
        assert "dev" in summary["by_agent"]
        assert "qa" in summary["by_agent"]
        assert summary["by_agent"]["dev"]["calls"] == 2
        assert summary["by_agent"]["dev"]["input_tokens"] == 300
        assert summary["by_agent"]["qa"]["calls"] == 1

    def test_by_model_breakdown(self):
        tracker = CostTracker()
        tracker.record_usage("agent", "claude-3", 100, 50)
        tracker.record_usage("agent", "gpt-4", 200, 100)

        summary = tracker.get_summary()
        assert "claude-3" in summary["by_model"]
        assert "gpt-4" in summary["by_model"]

    def test_empty_summary(self):
        tracker = CostTracker()
        summary = tracker.get_summary()

        assert summary["total_input_tokens"] == 0
        assert summary["total_output_tokens"] == 0
        assert summary["total_tokens"] == 0
        assert summary["estimated_cost_usd"] == 0.0
        assert summary["by_agent"] == {}
        assert summary["by_model"] == {}
