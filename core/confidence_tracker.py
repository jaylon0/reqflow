"""ConfidenceTracker — 6+5 Dimension Model with Trend Tracking.

Provides 6 core weighted dimensions, 5 optional extended dimensions,
Unicode visualization, history persistence, and trend delta tracking.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# 6 core dimension weights (must sum to 1.0)
CORE_WEIGHTS: dict[str, tuple[str, float]] = {
    "completeness":    ("完整性",     0.20),
    "consistency":     ("一致性",     0.15),
    "accuracy":        ("准确性",     0.20),
    "testability":     ("可测试性",   0.15),
    "risk_coverage":   ("风险覆盖",   0.15),
    "spec_compliance": ("规范合规",   0.15),
}

EXTENDED_DIMENSIONS = ["security", "performance", "maintainability", "dependency_health", "documentation"]

HEAT_THRESHOLDS = [
    (0.85, "\U0001f7e9"),  # green square
    (0.70, "\U0001f7e8"),  # yellow square
    (0.60, "\U0001f7e7"),  # orange square
    (0.00, "\U0001f7e5"),  # red square
]

SPARKLINE_CHARS = "▁▂▃▄▅▆▇█"


@dataclass
class DimensionResult:
    """Single dimension score."""
    name: str
    display_name: str
    score: float
    weight: float
    heat: str


@dataclass
class ConfidenceWarning:
    """Warning for a dimension below gate threshold."""
    dimension: str
    score: float
    threshold: float
    message: str


@dataclass
class ConfidenceReport:
    """Full confidence assessment result."""
    core_dimensions: list[DimensionResult]
    extended_dimensions: list[DimensionResult]
    overall: float
    warnings: list[ConfidenceWarning]
    trend_delta: float | None = None
    previous_overall: float | None = None


class ConfidenceTracker:
    """6+5 dimension confidence tracker with trend tracking and visualization."""

    GATE_THRESHOLD = 0.6

    def __init__(self, history_file: str | None = None) -> None:
        self.history_file = history_file

    # ------------------------------------------------------------------
    # Core assessment
    # ------------------------------------------------------------------

    def assess(
        self,
        scores: dict[str, float],
        extended_scores: dict[str, float] | None = None,
    ) -> ConfidenceReport:
        """Run a confidence assessment and persist to history."""
        core_dims = self._build_core_dimensions(scores)
        ext_dims = self._build_extended_dimensions(extended_scores or {})
        overall = self._weighted_average(core_dims)
        warnings = self._check_gates(core_dims)
        previous_overall, trend_delta = self._compute_trend(overall)

        report = ConfidenceReport(
            core_dimensions=core_dims,
            extended_dimensions=ext_dims,
            overall=overall,
            warnings=warnings,
            trend_delta=trend_delta,
            previous_overall=previous_overall,
        )

        self._persist(overall, scores, extended_scores)
        return report

    # ------------------------------------------------------------------
    # Visualization helpers
    # ------------------------------------------------------------------

    def render_progress_bar(self, score: float, width: int = 10) -> str:
        """Render a Unicode progress bar: '████████░░'."""
        filled = round(score * width)
        return "█" * filled + "░" * (width - filled)

    def heat_emoji(self, score: float) -> str:
        """Return heat-map emoji based on score thresholds."""
        for threshold, emoji in HEAT_THRESHOLDS:
            if score >= threshold:
                return emoji
        return HEAT_THRESHOLDS[-1][1]

    def trend_arrow(self, current: float, previous: float) -> str:
        """Return trend arrow string: '↑3', '↓5', '→'."""
        delta_pct = round((current - previous) * 100)
        if delta_pct > 0:
            return f"↑{delta_pct}"
        elif delta_pct < 0:
            return f"↓{abs(delta_pct)}"
        return "→"

    def render_sparkline(self, scores: list[float]) -> str:
        """Render scores as a sparkline using Unicode block characters."""
        chars = []
        for s in scores:
            clamped = max(0.0, min(1.0, s))
            idx = round(clamped * (len(SPARKLINE_CHARS) - 1))
            chars.append(SPARKLINE_CHARS[idx])
        return "".join(chars)

    # ------------------------------------------------------------------
    # Report formatting
    # ------------------------------------------------------------------

    def format_per_stage_report(self, result: ConfidenceReport, stage_name: str) -> str:
        """Format a markdown table for a single stage."""
        lines = [
            f"## Confidence Report — {stage_name}",
            "",
            "| Dimension | Score | Weight | Bar | Heat |",
            "|-----------|-------|--------|-----|------|",
        ]
        for d in result.core_dimensions:
            bar = self.render_progress_bar(d.score, width=10)
            lines.append(
                f"| {d.display_name} ({d.name}) | {d.score:.2f} | {d.weight:.0%} | `{bar}` | {d.heat} |"
            )

        lines.append("")
        lines.append(f"**Overall:** {result.overall:.2f}")

        if result.trend_delta is not None:
            arrow = self.trend_arrow(result.overall, result.previous_overall or 0)
            lines.append(f"**Trend:** {arrow} (delta: {result.trend_delta:+.2f})")

        if result.warnings:
            lines.append("")
            lines.append("### Warnings")
            for w in result.warnings:
                lines.append(f"- **{w.dimension}** ({w.score:.2f}): {w.message}")

        return "\n".join(lines)

    def format_full_dashboard(self, results: list[ConfidenceReport], stage_names: list[str]) -> str:
        """Format a full dashboard with sparklines and heat map."""
        lines = [
            "# Confidence Dashboard",
            "",
        ]

        # Per-stage summary
        lines.append("## Stage Summary")
        lines.append("")
        lines.append("| Stage | Overall | Heat |")
        lines.append("|-------|---------|------|")
        for name, result in zip(stage_names, results):
            heat = self.heat_emoji(result.overall)
            lines.append(f"| {name} | {result.overall:.2f} | {heat} |")

        # Sparklines per dimension
        lines.append("")
        lines.append("## Dimension Sparklines")
        lines.append("")
        dim_names = [d.name for d in results[0].core_dimensions] if results else []
        for dim_name in dim_names:
            dim_scores = []
            for r in results:
                for d in r.core_dimensions:
                    if d.name == dim_name:
                        dim_scores.append(d.score)
                        break
            sparkline = self.render_sparkline(dim_scores)
            display = CORE_WEIGHTS.get(dim_name, (dim_name, 0))[0]
            lines.append(f"- **{display}** ({dim_name}): `{sparkline}`")

        # Heat map distribution
        lines.append("")
        lines.append("## Heat Map Distribution")
        lines.append("")
        heat_counts = {emoji: 0 for _, emoji in HEAT_THRESHOLDS}
        for r in results:
            heat = self.heat_emoji(r.overall)
            heat_counts[heat] = heat_counts.get(heat, 0) + 1
        for emoji, count in heat_counts.items():
            if count > 0:
                lines.append(f"- {emoji} x {count}")

        # All warnings
        all_warnings = []
        for name, result in zip(stage_names, results):
            for w in result.warnings:
                all_warnings.append(f"- **{name}**: {w.dimension} ({w.score:.2f}) — {w.message}")
        if all_warnings:
            lines.append("")
            lines.append("## Warnings")
            lines.extend(all_warnings)

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_core_dimensions(self, scores: dict[str, float]) -> list[DimensionResult]:
        dims = []
        for name, (display, weight) in CORE_WEIGHTS.items():
            score = scores.get(name, 0.0)
            dims.append(DimensionResult(
                name=name,
                display_name=display,
                score=score,
                weight=weight,
                heat=self.heat_emoji(score),
            ))
        return dims

    def _build_extended_dimensions(self, scores: dict[str, float]) -> list[DimensionResult]:
        dims = []
        for name in EXTENDED_DIMENSIONS:
            score = scores.get(name, 0.0)
            dims.append(DimensionResult(
                name=name,
                display_name=name,
                score=score,
                weight=0.0,
                heat=self.heat_emoji(score),
            ))
        return dims

    def _weighted_average(self, dims: list[DimensionResult]) -> float:
        total = sum(d.score * d.weight for d in dims)
        return round(total, 4)

    def _check_gates(self, dims: list[DimensionResult]) -> list[Warning]:
        warnings = []
        for d in dims:
            if d.score < self.GATE_THRESHOLD:
                warnings.append(ConfidenceWarning(
                    dimension=d.name,
                    score=d.score,
                    threshold=self.GATE_THRESHOLD,
                    message=f"{d.display_name} score {d.score:.2f} below gate threshold {self.GATE_THRESHOLD}",
                ))
        return warnings

    def _compute_trend(self, current: float) -> tuple[float | None, float | None]:
        history = self._load_history()
        if not history:
            return None, None
        previous = history[-1]["overall"]
        return previous, round(current - previous, 4)

    def _load_history(self) -> list[dict]:
        if not self.history_file:
            return []
        try:
            with open(self.history_file) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _persist(
        self,
        overall: float,
        scores: dict[str, float],
        extended_scores: dict[str, float] | None,
    ) -> None:
        if not self.history_file:
            return
        history = self._load_history()
        entry = {
            "timestamp": time.time(),
            "overall": overall,
            "scores": scores,
            "extended_scores": extended_scores or {},
        }
        history.append(entry)
        with open(self.history_file, "w") as f:
            json.dump(history, f, indent=2)
