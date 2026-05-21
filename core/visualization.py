"""Visualization V7 — 可视化图表生成，含共识表和质量门。"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class Visualizer:
    """图表生成器 V7。"""

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
        symbol_map = {"high": "●", "medium": "◐", "low": "○", "very_high": "◉", "very_low": "◌"}
        max_label = max(len(s) for s in stages) if stages else 0
        lines = ["置信度趋势:"]
        for stage, level in zip(stages, levels):
            symbol = symbol_map.get(level, "?")
            lines.append(f"  {stage.ljust(max_label)} {symbol} {level}")
        return "\n".join(lines)

    def agent_role_table(
        self,
        agents: list[dict],
    ) -> str:
        """生成 Agent 角色表。

        agents: [{"name": "research-agent", "role": "调研分析", "model": "any", "responsibility": "..."}]
        """
        headers = ["Agent", "角色", "职责"]
        rows = []
        for a in agents:
            rows.append([
                f"`{a['name']}`",
                a.get("role", "通用"),
                a.get("responsibility", ""),
            ])
        return self._build_table(headers, rows)

    def consensus_table(
        self,
        title: str,
        leader_role: str,
        agents: list[str],
        dimensions: list[str],
        agent_opinions: dict[str, dict[str, tuple[float, str]]],  # {agent: {dim: (score, status)}}
        leader_verdict: str = "",
        decision_type: str = "Taste",
        overall_score: float = 0.0,
        overall_level: str = "HIGH",
        overall_action: str = "proceed",
    ) -> str:
        """生成共识表。

        agent_opinions: {agent_name: {dimension: (score, status)}}
            status: "CONFIRMED" | "DISAGREE" | "FLAGGED" | "N/A"
        """
        # 计算列宽
        dim_width = max(len(d) for d in dimensions) if dimensions else 10
        agent_width = max(len(a) for a in agents) if agents else 10
        agent_width = max(agent_width, 8)

        lines = []
        lines.append(f"┌{'─' * 70}┐")
        lines.append(f"│ 📋 {title} — 阶段共识表{' ' * max(0, 62 - len(title))}│")
        lines.append(f"├{'─' * 70}┤")
        lines.append(f"│ 🧑‍💼 leader-agent: {leader_role}{' ' * max(0, 52 - len(leader_role))}│")
        agents_str = ", ".join(a.split("-")[0][:5] for a in agents)
        lines.append(f"│ 参与 agents: {agents_str}{' ' * max(0, 55 - len(agents_str))}│")
        lines.append(f"├{'─' * 70}┤")

        # 表头
        header = f"│ {'维度'.ljust(dim_width)} │"
        for a in agents:
            short = a.split("-")[0][:6]
            header += f" {short.ljust(agent_width)} │"
        header += f" {'共识'.ljust(8)} │"
        lines.append(header)
        lines.append(f"│{'─' * (dim_width + 2)}┼" + "─" * (agent_width + 2) + "┼" * len(agents) + "─" * 10 + "┤")

        # 数据行
        consensus_counts = {"CONFIRMED": 0, "DISAGREE": 0, "FLAGGED": 0, "N/A": 0}
        for dim in dimensions:
            row = f"│ {dim.ljust(dim_width)} │"
            statuses = []
            for a in agents:
                opinion = agent_opinions.get(a, {}).get(dim)
                if opinion:
                    score, status = opinion
                    icon = self._status_icon(status)
                    cell = f"{score:.2f} {icon}"
                    statuses.append(status)
                else:
                    cell = "—"
                    statuses.append("N/A")
                row += f" {cell.ljust(agent_width)} │"

            # 共识判定
            consensus = self._calc_consensus(statuses)
            consensus_counts[consensus] = consensus_counts.get(consensus, 0) + 1
            row += f" {consensus.ljust(8)} │"
            lines.append(row)

        # 共识统计
        lines.append(f"├{'─' * 70}┤")
        stats = "  ".join(f"{k}={v}" for k, v in consensus_counts.items() if v > 0)
        lines.append(f"│ 共识统计: {stats}{' ' * max(0, 57 - len(stats))}│")

        # Leader 裁决
        if leader_verdict:
            lines.append(f"│{'─' * 70}│")
            lines.append(f"│ 🧑‍💼 leader 裁决:                                              │")
            # 分行显示裁决内容
            verdict_lines = self._wrap_text(leader_verdict, 66)
            for vl in verdict_lines:
                lines.append(f"│  {vl}{' ' * max(0, 67 - len(vl))}│")

        # 决策类型和置信度
        lines.append(f"│{'─' * 70}│")
        dt_line = f"决策类型: {decision_type}"
        lines.append(f"│ {dt_line}{' ' * max(0, 68 - len(dt_line))}│")
        score_line = f"综合置信度: {overall_score:.2f} ({overall_level}) → {overall_action}"
        lines.append(f"│ {score_line}{' ' * max(0, 68 - len(score_line))}│")
        lines.append(f"└{'─' * 70}┘")

        return "\n".join(lines)

    def quality_gate_report(
        self,
        stage_name: str,
        checks: list[dict],  # [{"name": "...", "result": "pass|warn|fail", "detail": "..."}]
        mode: str = "hybrid",
        retry_count: int = 0,
        max_retries: int = 3,
        overall: str = "PASS",
        suggestions: list[str] | None = None,
    ) -> str:
        """生成质量门报告。"""
        lines = []
        lines.append(f"┌{'─' * 50}┐")
        lines.append(f"│ 🔒 质量门 — {stage_name}{' ' * max(0, 37 - len(stage_name))}│")
        lines.append(f"├{'─' * 50}┤")

        for check in checks:
            name = check["name"]
            result = check["result"]
            detail = check.get("detail", "")
            icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}.get(result, "?")
            line = f"│ {name.ljust(20)} {icon} {result.upper().ljust(6)} {detail.ljust(18)} │"
            lines.append(line)

        lines.append(f"├{'─' * 50}┤")
        overall_line = f"综合: {overall} ({mode} 模式，自动重试 {retry_count}/{max_retries})"
        lines.append(f"│ {overall_line}{' ' * max(0, 48 - len(overall_line))}│")

        if suggestions:
            for s in suggestions:
                sug_line = f"建议: {s}"
                for vl in self._wrap_text(sug_line, 48):
                    lines.append(f"│ {vl}{' ' * max(0, 48 - len(vl))}│")

        lines.append(f"└{'─' * 50}┘")
        return "\n".join(lines)

    def confidence_report(
        self,
        dimensions: list[dict],  # [{"name": "...", "score": 0.8, "icon": "🟢"}]
        overall_score: float = 0.0,
        overall_level: str = "HIGH",
        action: str = "proceed",
        agent_confidences: list[dict] | None = None,  # [{"name": "...", "score": 0.85, "reasoning": "..."}]
        consensus_degree: float = 0.0,
    ) -> str:
        """生成置信度报告（ASCII 盒子）。"""
        lines = []
        lines.append(f"┌{'─' * 45}┐")
        lines.append(f"│ 📊 阶段置信度报告{' ' * 27}│")
        lines.append(f"├{'─' * 45}┤")

        for dim in dimensions:
            name = dim["name"]
            score = dim["score"]
            icon = dim.get("icon", self._score_icon(score))
            bar = self.progress_bar(score, 10)
            line = f"│ {name}: {bar} {icon}{' ' * max(0, 22 - len(name) - 14)}│"
            lines.append(line)

        lines.append(f"├{'─' * 45}┤")
        score_line = f"│ 综合分: {overall_score:.2f}  级别: {overall_level}{' ' * max(0, 22 - len(overall_level))}│"
        lines.append(score_line)
        action_label = self._action_label(action)
        action_line = f"│ 建议:   {action_label}{' ' * max(0, 35 - len(action_label))}│"
        lines.append(action_line)

        if agent_confidences:
            lines.append(f"├{'─' * 45}┤")
            lines.append(f"│ Agent 共识详情:                       │")
            for ac in agent_confidences:
                name = ac["name"]
                score = ac["score"]
                reasoning = ac.get("reasoning", "")
                ac_line = f"│  {name}: {score:.2f}"
                if reasoning:
                    ac_line += f" ({reasoning[:20]})"
                ac_line += " " * max(0, 44 - len(ac_line) + 1)
                ac_line += "│"
                lines.append(ac_line)
            cons_line = f"│  共识度: {consensus_degree:.2f}{' ' * max(0, 34 - len(f'{consensus_degree:.2f}'))}│"
            lines.append(cons_line)

        lines.append(f"└{'─' * 45}┘")
        return "\n".join(lines)

    def _build_table(self, headers: list[str], rows: list[list[str]]) -> str:
        """通用表格构建。"""
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

    def _status_icon(self, status: str) -> str:
        """状态图标。"""
        return {"CONFIRMED": "✅", "DISAGREE": "❌", "FLAGGED": "⚠️", "N/A": "—"}.get(status, "?")

    def _score_icon(self, score: float) -> str:
        """分数图标。"""
        if score >= 0.9:
            return "🟢"
        elif score >= 0.75:
            return "🟢"
        elif score >= 0.5:
            return "🟡"
        elif score >= 0.3:
            return "🟠"
        else:
            return "🔴"

    def _calc_consensus(self, statuses: list[str]) -> str:
        """计算共识。"""
        if not statuses:
            return "N/A"
        if all(s == "CONFIRMED" for s in statuses):
            return "CONFIRMED"
        if any(s == "DISAGREE" for s in statuses):
            return "DISAGREE"
        if any(s == "FLAGGED" for s in statuses):
            return "FLAGGED"
        return "N/A"

    def _action_label(self, action: str) -> str:
        """动作中文标签。"""
        labels = {
            "auto_proceed": "自动进入下一阶段",
            "proceed": "进入下一阶段",
            "pause": "暂停，列出不确定点",
            "retry": "自动重试",
            "escalate": "升级到用户",
        }
        return labels.get(action, action)

    def _wrap_text(self, text: str, width: int) -> list[str]:
        """文本换行。"""
        lines = []
        while len(text) > width:
            lines.append(text[:width])
            text = text[width:]
        lines.append(text)
        return lines
