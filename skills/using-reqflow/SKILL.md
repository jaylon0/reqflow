---
name: using-reqflow
description: Use when the user provides a requirement, PRD, issue, bug, or feature request - guides the full workflow from requirements analysis to code delivery
---

# using-reqflow

ReqFlow 主流程入口。引导用户完成从需求到交付的全流程。

## 触发方式

**自然语言：**
```
使用 reqflow 帮我处理这个需求：<需求内容>
```

**Slash 命令：**
```
/reqflow:using-reqflow <需求内容>
```

## 流程

### 1. 项目上下文扫描

首先了解项目结构和上下文：

```
读取项目根目录的文件结构，了解：
- 项目类型（Java/Python/Node.js 等）
- 构建工具（Maven/Gradle/npm 等）
- 测试框架
- 代码规范
```

### 2. 需求分析

分析用户需求，确定：
- 需求类型（新功能/bug 修复/重构/分析）
- 复杂度级别（L0-L3）
- 涉及的模块和文件

### 3. 工作流选择

根据需求复杂度选择工作流：

| 级别 | 工作流 | 说明 |
|------|--------|------|
| L0 | 直接分析 | 只读分析，不修改代码 |
| L1 | flow | 快速 3 阶段：分析→实现→验证 |
| L2 | main-flow | 完整 10 阶段 PRD→代码流程 |
| L3 | graph-flow | 图编排，支持分支和循环 |

### 4. 执行工作流

调用 MCP 工具执行选定的工作流：

```
调用 reqflow_run 或 reqflow_run_graph 执行工作流
```

### 5. 结果验证

检查执行结果：
- 代码变更是否正确
- 测试是否通过
- 是否满足需求

### 6. 交付报告

调用 reqflow_dashboard 生成运行面板，展示：
- 执行状态
- 各步骤结果
- Checkpoint 信息
- 耗时统计

## 可用能力

| 能力 | MCP 工具 | 说明 |
|------|----------|------|
| 线性工作流 | reqflow_run | 执行 flow/main-flow |
| 图编排 | reqflow_run_graph | 执行图工作流 |
| 会话持久化 | reqflow_session_save/load | 跨轮次状态 |
| Checkpoint | reqflow_checkpoint | 检查点管理 |
| 并行调度 | reqflow_parallel | 并行 agent |
| Trace | reqflow_trace | 执行追踪 |
| 约束检查 | reqflow_guardrails | 规则验证 |
| 面板 | reqflow_dashboard | 运行面板 |
