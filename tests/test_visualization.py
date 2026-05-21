from core.visualization import Visualizer


def test_progress_bar():
    v = Visualizer()
    bar = v.progress_bar(0.75, width=20)
    assert "75%" in bar
    assert "█" in bar


def test_comparison_table():
    v = Visualizer()
    table = v.comparison_table(
        headers=["维度", "方案A", "方案B"],
        rows=[
            ["复杂度", "低", "中"],
            ["风险", "低", "高"],
        ],
    )
    assert "方案A" in table
    assert "复杂度" in table


def test_mermaid_flowchart():
    v = Visualizer()
    chart = v.mermaid_flowchart(
        nodes=["A: 开始", "B: 处理", "C: 结束"],
        edges=[("A", "B"), ("B", "C")],
    )
    assert "graph TD" in chart
    assert "A" in chart


def test_mermaid_gantt():
    v = Visualizer()
    chart = v.mermaid_gantt(
        tasks=[
            ("启动", "2026-01-01", "1d"),
            ("PRD理解", "2026-01-02", "2d"),
        ],
    )
    assert "gantt" in chart


def test_ascii_bar_chart():
    v = Visualizer()
    chart = v.ascii_bar_chart(
        data={"启动": 1.0, "PRD": 0.8, "技术方案": 0.6},
        width=30,
    )
    assert "启动" in chart
    assert "PRD" in chart
