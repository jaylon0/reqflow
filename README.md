# ReqFlow

ReqFlow 是一个 model-agnostic 的工作流编排引擎，将需求（PRD）转化为可交付的代码变更。任何 AI 模型（Claude、GPT、Gemini、DeepSeek）都能通过适配器接入，成为完整的工作流智能体。

## 6 核心能力层

| 层 | 目录 | Python 模块 | 职责 |
|----|------|-------------|------|
| 上下文管理 | `context/` | `context_adapter.py` | 扫描项目、构建代码图、打包紧凑上下文 |
| 工具系统 | `tools/` | `tool_bridge.py` | 统一工具接口，适配不同运行时 |
| 执行编排 | `orchestration/` | `engine.py` | 工作流编排引擎，串联所有组件 |
| 状态与记忆 | `state/` | `state_manager.py` | 会话持久化、三层记忆、checkpoint |
| 评估与观测 | `evaluation/` | `tracer.py` | 层级 trace/span 执行追踪 |
| 约束与恢复 | `constraints/` | `guardrails.py` | 并行约束验证，FATAL 级别快速失败 |

## 快速开始

### 安装

```bash
cd reqflow
pip install -e .

# 可选依赖
pip install -e ".[api]"   # API 适配器（urllib3）
pip install -e ".[mcp]"   # MCP Server
pip install -e ".[all]"   # 全部
```

### 作为 CLI 使用

```bash
# 列出可用 runtime
reqflow list-runtimes

# 执行 workflow（自动检测 runtime）
reqflow run "实现用户认证功能"

# 指定 runtime
reqflow run --runtime manual "分析这个需求"

# 使用 main-flow（完整 PRD-to-code 流程）
reqflow run --workflow main-flow --runtime claude "实现用户认证功能"

# 查看运行状态
reqflow status .dev-workflow/runs/<run-id>

# 或通过 python -m
python -m reqflow.runner run "需求文本"
```

### 作为 Python 库使用

```python
from reqflow.core import Engine, RuntimeRegistry

# 加载 runtime 配置
registry = RuntimeRegistry()
config = registry.get("claude")  # 或 gpt, gemini, deepseek, manual

# 创建引擎
engine = Engine(config=config, run_dir=".dev-workflow/runs/my-run")

# 执行 workflow
result = await engine.run_workflow(
    workflow_steps=[
        {"name": "analyze", "prompt": "分析需求"},
        {"name": "plan", "prompt": "制定计划", "checkpoint": True},
        {"name": "implement", "prompt": "实现代码"},
        {"name": "verify", "prompt": "验证结果"},
    ],
    requirement="用户认证功能"
)
```

### 作为 Claude Code Skill 使用

```text
/reqflow:flow 实现用户认证功能
/reqflow:main-flow 运行完整 PRD 到代码流程
```

### 作为 MCP Server 使用

```bash
# 启动 MCP Server（stdio 传输）
python -m reqflow.runner.mcp_server

# 暴露的工具:
# - reqflow_run: 执行 workflow
# - reqflow_status: 查询运行状态
# - reqflow_list_runtimes: 列出可用 runtime
```

## 核心引擎架构

```
reqflow/core/
├── __init__.py            # 导出所有核心类
├── engine.py              # 编排引擎（串联所有组件）
├── runtime_config.py      # RuntimeConfig 数据类
├── registry.py            # 运行时注册表（加载 YAML 配置）
├── state_manager.py       # 状态持久化 + checkpoint + 记忆
├── tracer.py              # 层级 trace/span 追踪
├── tool_bridge.py         # 统一工具接口
├── context_adapter.py     # 上下文格式适配
├── guardrails.py          # 并行约束验证
└── adapters/
    ├── base.py            # ModelAdapter 协议
    ├── claude_code.py     # Claude Code 嵌入适配器
    ├── api.py             # OpenAI/Anthropic/Gemini/DeepSeek API
    ├── cli.py             # 子进程 CLI 调用
    └── manual.py          # 人工模式（兜底）

reqflow/runner/
├── cli.py                 # CLI 入口：reqflow run ...
├── mcp_server.py          # MCP Server 入口
└── skill/
    ├── flow.md            # /reqflow:flow Claude Code skill
    └── main-flow.md       # /reqflow:main-flow Claude Code skill

reqflow/workflows/         # YAML workflow 定义
├── flow.yaml              # 快速工作流（3 阶段）
└── main-flow.yaml         # 完整 PRD-to-code（11 阶段）

reqflow/references/        # 领域知识参考
├── routing-levels.md      # L0-L3 路由级别定义
├── context-schema.md      # 项目上下文 schema
├── context-files.md       # 运行时上下文文件路径
├── manual-mode.md         # Manual 模式行为
├── coding-standards-java.md  # Java 编码规范示例
├── adapter-lifecycle.md   # 适配器生命周期
├── template-policy.md     # 模板策略
└── domain-catalog-template.md  # 领域组件目录模板
```

## 适配器选择

Engine 启动时自动选择适配器：

| Runtime | 适配器 | 特点 |
|---------|--------|------|
| `claude` | ClaudeCodeAdapter | 嵌入 Claude Code，零配置，完整能力 |
| `gpt` / `gemini` / `deepseek` | APIAdapter | 通过 API function calling |
| `cli:<command>` | CLIAdapter | 子进程调用外部 CLI |
| `manual` | ManualAdapter | 输出 checklist，人工执行（兜底） |

自动检测逻辑：`CLAUDE_CODE` 环境变量 → `REQFLOW_RUNTIME` 环境变量 → API key 检测 → 回退到 manual。

## 6 层 Skill 定义

| 层 | 目录 | 文件数 |
|----|------|--------|
| 上下文管理 | `context/` | 7 |
| 工具系统 | `tools/` | 9 |
| 执行编排 | `orchestration/` | 7 |
| 状态与记忆 | `state/` | 6 |
| 评估与观测 | `evaluation/` | 6 |
| 约束与恢复 | `constraints/` | 9 |

## 运行时配置

预置 5 种运行时配置（`runtime/providers/`）：

| 配置 | 说明 |
|------|------|
| `claude.yaml` | 完整能力，Agent 工具原生支持 |
| `gpt.yaml` | function calling 适配 |
| `gemini.yaml` | 类似 GPT，更长上下文 |
| `deepseek.yaml` | 代码能力强，工具支持有限 |
| `manual.yaml` | 纯人工模式 |

## 设计原则

| 铁律 | 含义 |
|------|------|
| 文件即记忆 | 子智能体的所有产出必须持久化到文件 |
| 隔离即常态 | 每个子智能体只看到主智能体给它的信息 |
| 记录即保险 | 主智能体和子智能体都写日志，全程可回溯 |
