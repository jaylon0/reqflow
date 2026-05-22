"""Tests for ConfidenceTracker — 6+5 Dimension Model with Trend Tracking."""

import json
from core.confidence_tracker import (
    ConfidenceTracker,
    DimensionResult,
    Warning,
    ConfidenceReport,
)


def test_six_core_dimensions():
    """Tracker should have exactly 6 core dimensions with correct weights."""
    tracker = ConfidenceTracker()
    scores = {
        "completeness": 1.0,
        "consistency": 1.0,
        "accuracy": 1.0,
        "testability": 1.0,
        "risk_coverage": 1.0,
        "spec_compliance": 1.0,
    }
    report = tracker.assess(scores)
    assert len(report.core_dimensions) == 6
    names = {d.name for d in report.core_dimensions}
    assert names == {"completeness", "consistency", "accuracy", "testability", "risk_coverage", "spec_compliance"}
    # Check weights sum to 1.0
    total_weight = sum(d.weight for d in report.core_dimensions)
    assert abs(total_weight - 1.0) < 1e-6


def test_weighted_average():
    """All 1.0 scores should produce overall 1.0."""
    tracker = ConfidenceTracker()
    scores = {
        "completeness": 1.0,
        "consistency": 1.0,
        "accuracy": 1.0,
        "testability": 1.0,
        "risk_coverage": 1.0,
        "spec_compliance": 1.0,
    }
    report = tracker.assess(scores)
    assert report.overall == 1.0


def test_minimum_gate_warning():
    """Any core dimension < 0.6 should trigger a Warning."""
    tracker = ConfidenceTracker()
    scores = {
        "completeness": 1.0,
        "consistency": 1.0,
        "accuracy": 0.3,
        "testability": 1.0,
        "risk_coverage": 1.0,
        "spec_compliance": 1.0,
    }
    report = tracker.assess(scores)
    assert len(report.warnings) >= 1
    assert any(w.dimension == "accuracy" for w in report.warnings)
    assert all(isinstance(w, Warning) for w in report.warnings)


def test_progress_bar_rendering():
    """Progress bar should render correctly at various scores."""
    tracker = ConfidenceTracker()
    # Full score
    bar = tracker.render_progress_bar(1.0, width=10)
    assert bar == "██████████"
    # Empty
    bar = tracker.render_progress_bar(0.0, width=10)
    assert bar == "░░░░░░░░░░"
    # Half
    bar = tracker.render_progress_bar(0.5, width=10)
    assert bar == "█████░░░░░"


def test_heat_map_emoji():
    """Heat emoji should map scores to correct emoji."""
    tracker = ConfidenceTracker()
    assert tracker.heat_emoji(0.90) == "\U0001f7e9"   # >= 0.85 green
    assert tracker.heat_emoji(0.85) == "\U0001f7e9"   # >= 0.85 green
    assert tracker.heat_emoji(0.75) == "\U0001f7e8"   # >= 0.70 yellow
    assert tracker.heat_emoji(0.65) == "\U0001f7e7"   # >= 0.60 orange
    assert tracker.heat_emoji(0.50) == "\U0001f7e5"   # < 0.60 red


def test_trend_arrow():
    """Trend arrow should show delta direction and magnitude."""
    tracker = ConfidenceTracker()
    assert "↑" in tracker.trend_arrow(0.9, 0.8)
    assert "↓" in tracker.trend_arrow(0.7, 0.9)
    assert "→" in tracker.trend_arrow(0.8, 0.8)


def test_sparkline_rendering():
    """Sparkline should map scores to Unicode block characters."""
    tracker = ConfidenceTracker()
    line = tracker.render_sparkline([0.0, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1.0])
    assert len(line) == 8
    # Should contain different block characters
    assert "▁" in line
    assert "█" in line


def test_history_persistence(tmp_path):
    """assess() should persist results to history file."""
    history_file = tmp_path / "history.json"
    tracker = ConfidenceTracker(history_file=str(history_file))
    scores = {
        "completeness": 0.8,
        "consistency": 0.7,
        "accuracy": 0.9,
        "testability": 0.6,
        "risk_coverage": 0.5,
        "spec_compliance": 0.75,
    }
    tracker.assess(scores)
    assert history_file.exists()
    data = json.loads(history_file.read_text())
    assert isinstance(data, list)
    assert len(data) == 1
    assert "overall" in data[0]
    assert "timestamp" in data[0]


def test_trend_from_history(tmp_path):
    """Second assess should compute trend delta from previous entry."""
    history_file = tmp_path / "history.json"
    tracker = ConfidenceTracker(history_file=str(history_file))
    scores = {
        "completeness": 0.8,
        "consistency": 0.8,
        "accuracy": 0.8,
        "testability": 0.8,
        "risk_coverage": 0.8,
        "spec_compliance": 0.8,
    }
    report1 = tracker.assess(scores)
    # Second assessment with higher scores
    scores2 = {k: 0.9 for k in scores}
    report2 = tracker.assess(scores2)
    assert report2.previous_overall is not None
    assert report2.trend_delta is not None
    assert report2.trend_delta > 0


def test_format_per_stage_report():
    """Per-stage report should contain dimension names and progress bars."""
    tracker = ConfidenceTracker()
    scores = {
        "completeness": 0.8,
        "consistency": 0.7,
        "accuracy": 0.9,
        "testability": 0.6,
        "risk_coverage": 0.5,
        "spec_compliance": 0.75,
    }
    report = tracker.assess(scores)
    output = tracker.format_per_stage_report(report, "PRD Review")
    assert "PRD Review" in output
    assert "completeness" in output
    assert "accuracy" in output
    assert "spec_compliance" in output
    assert "overall" in output.lower() or "综合" in output


def test_format_full_dashboard():
    """Full dashboard should contain sparklines and heat map."""
    tracker = ConfidenceTracker()
    results = []
    stage_names = ["Stage 1", "Stage 2"]
    for _ in stage_names:
        scores = {
            "completeness": 0.8,
            "consistency": 0.7,
            "accuracy": 0.9,
            "testability": 0.6,
            "risk_coverage": 0.5,
            "spec_compliance": 0.75,
        }
        results.append(tracker.assess(scores))
    output = tracker.format_full_dashboard(results, stage_names)
    assert "Stage 1" in output
    assert "Stage 2" in output
    # Should contain sparkline-like Unicode characters
    blocks = "▁▂▃▄▅▆▇█"
    assert any(c in output for c in blocks)
