---
name: dashboard
description: >
  ReqFlow 工作流可视化面板。查看运行状态、trace 时间线、checkpoint 列表。
tools:
  - Bash
  - Read
---

# dashboard

ReqFlow 工作流可视化。

## 触发方式

```
/reqflow:dashboard <run-dir>
```

## 使用方式

```python
from reqflow.runner.dashboard import Dashboard

dashboard = Dashboard(run_dir=".reqflow/runs/run-abc123")

# 格式化状态
status = engine.get_status()
print(dashboard.format_status(status))

# 格式化 trace
trace_data = json.loads(Path("trace.json").read_text())
print(dashboard.format_trace(trace_data))

# Rich TUI（需要 pip install rich）
dashboard.rich_render(status)
```

## 输出示例

```
=== ReqFlow Dashboard ===
Run:     run-abc12345
Config:  gpt (api_gpt)
Stage:   Agent Execution
Steps:   4 executed
Done:    启动或恢复运行, PRD 理解, Spec Governance, Java Context Discovery

--- Step Status ---
  [OK   ] 启动或恢复运行
  [OK   ] PRD 理解
  [OK   ] Spec Governance
  [OK   ] Java Context Discovery

Checkpoints: 3
Memory:      12 entries
```

## CLI 方式

```bash
python3 -m reqflow.runner status <run-dir>
```
