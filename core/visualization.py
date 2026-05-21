"""Visualization — 可视化图表生成。"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class Visualizer:
    """图表生成器。"""

    def progress_bar(self, value: float, width: int = 20) -> str:
        """生成 ASCII 进度条。"""
        filled = int(value * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {value:.0%}"

    def comparison_table(
        self,
        headers: list[str],
        rows: list[list[str]],
    ) -> str:
        """生成 ASCII 对比表格。"""
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(cell))

        lines = []
        header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        lines.append(header_line)
        lines.append("-+-".join("-" * w for w in col_widths))
        for row in rows:
            line = " | ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(row))
            lines.append(line)
        return "\n".join(lines)

    def mermaid_flowchart(
        self,
        nodes: list[str],
        edges: list[tuple[str, str]],
    ) -> str:
        """生成 Mermaid 流程图。"""
        lines = ["graph TD"]
        for node in nodes:
            node_id, label = node.split(": ", 1)
            lines.append(f'    {node_id}["{label}"]')
        for src, dst in edges:
            lines.append(f"    {src} --> {dst}")
        return "\n".join(lines)

    def mermaid_gantt(
        self,
        tasks: list[tuple[str, str, str]],
    ) -> str:
        """生成 Mermaid 甘特图。"""
        lines = [
            "gantt",
            "    title 阶段耗时分布",
            "    dateFormat YYYY-MM-DD",
        ]
        for name, start, duration in tasks:
            lines.append(f"    {name} :{start}, {duration}")
        return "\n".join(lines)

    def ascii_bar_chart(
        self,
        data: dict[str, float],
        width: int = 30,
    ) -> str:
        """生成 ASCII 柱状图。"""
        max_val = max(data.values()) if data else 1
        max_label = max(len(k) for k in data) if data else 0
        lines = []
        for label, value in data.items():
            bar_len = int((value / max_val) * width)
            bar = "█" * bar_len
            lines.append(f"{label.ljust(max_label)} | {bar} {value:.2f}")
        return "\n".join(lines)

    def confidence_trend(
        self,
        stages: list[str],
        levels: list[str],
    ) -> str:
        """生成置信度趋势 ASCII 图。"""
        symbol_map = {"high": "●", "medium": "◐", "low": "○"}
        max_label = max(len(s) for s in stages) if stages else 0
        lines = ["置信度趋势:"]
        for stage, level in zip(stages, levels):
            symbol = symbol_map.get(level, "?")
            lines.append(f"  {stage.ljust(max_label)} {symbol} {level}")
        return "\n".join(lines)
