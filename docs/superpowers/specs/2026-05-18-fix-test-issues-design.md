# ReqFlow 测试问题修复 设计方案

## 目标

修复 reqflow 在真实项目测试中暴露的 12 个问题，使状态可信、runtime 可靠、产物可追踪。

## 设计原则

- **分层修复**：三层独立可测，不引入大重构
- **YAGNI**：只修已暴露的问题，不做预防性设计
- **向后兼容**：现有 workflow YAML 和 API 不变

## 三层架构

### 第一层：状态可信度

**覆盖问题：** Issue 1, 2, 10, 11

#### 1.1 API Adapter 错误传播

`core/adapters/api.py` 的 `call()` 方法在 HTTP 错误时当前返回 `ModelResponse(content="API call failed: ...")`，engine 把它当正常响应，step 标记为 success。

**修改：** HTTP 错误时抛 `RuntimeError`，不再返回带错误内容的 ModelResponse。

Engine 的 `run_step` 已有 try/except，捕获后返回 `StepResult(status="failure")`，无需额外改动。

#### 1.2 Engine Fail-Fast

`core/engine.py` 的 `run_workflow` 在 step failure 时继续执行后续步骤，最终标记为 completed。

**修改：** step 返回 `failure` 时跳出循环，设置 `final_result["status"] = "failed"`，记录 `failed_at` 字段。循环结束后仅在 status 不为 failed/aborted 时设为 completed。

#### 1.3 Dashboard 真实状态

`runner/dashboard.py` 的 `format_status` 只显示 completed_modules 数量，不区分成功/失败。

**修改：** 读取 `step_statuses` dict，每步骤用 `[OK]`/`[FAIL]`/`[SKIP]`/`[STOP]` 标记。

#### 1.4 Manual EOF 修正

`core/adapters/manual.py` 在 EOF 时 break 出循环，返回空 content 的 ModelResponse，在非交互场景造成假成功。

**修改：** EOF 时直接返回 `ModelResponse(content="[BLOCKED] 非交互模式无法获取人工输入...")`，raw 中标记 `status="blocked"`。同步修改 `execute_tool` 中的 EOF 处理。

---

### 第二层：Runtime 生命周期

**覆盖问题：** Issue 3, 4, 5, 6, 12

#### 2.1 Runtime Readiness Check

`core/registry.py` 的 `RuntimeRegistry` 新增方法：

```python
def check_readiness(self, name: str) -> tuple[bool, str]:
```

- API runtime：检查 `env_key` 对应环境变量或 `api_key` 是否有值
- Host/Manual runtime：始终返回 `(True, "")`
- 其他：检查 `api_base` 和 `api_key`

#### 2.2 默认 Runtime 选择策略

`runner/mcp_server.py` 和 `runner/cli.py` 的 `_detect_runtime` 当前按 `claude > gpt > gemini > deepseek > manual` 优先级。

**新策略：** `REQFLOW_RUNTIME 环境变量 > host > manual > 有 API key 的外部 runtime`

不隐式选中未配置 key 的外部 runtime。

#### 2.3 Health Check 增强

新增 `reqflow_health` MCP 工具，三层报告：
- **System**：reqflow 包、MCP 依赖是否可用
- **Runtimes**：每个 runtime 的 readiness 状态和不可用原因
- **Recommended**：推荐使用的 runtime

#### 2.4 Host Runtime + Adapter

新建文件：

**`runtime/providers/host.yaml`** — 通用 host runtime 配置，capabilities 全开（bash/file_edit/agent_tools），run_dir 为 `.reqflow/runs/`。

**`runtime/providers/host-codex.yaml`** — Codex 平台配置，与 host.yaml 相同结构。

**`core/adapters/host.py`** — `HostAgentAdapter`：

```python
class HostAgentAdapter:
    def call(self, prompt, tools, context, system_prompt) -> ModelResponse:
        # 1. 检查 run_dir/result.json 是否存在
        #    → 存在：消费并返回结果，删除 result.json
        # 2. 不存在：写 task.json (TaskPacket)，返回 [BLOCKED]

    def create_task_packet(self, stage_id, stage_name, prompt, ...) -> dict:
        # 写 task.json 到 run_dir
```

**`core/engine.py`** 的 `select_adapter` 新增 host 类型分支：

```python
elif name in ("host", "host-codex", "host-claude-code", "host-cursor", "host-copilot"):
    from .adapters.host import HostAgentAdapter
    self._adapter = HostAgentAdapter(run_dir=self.run_dir)
```

---

### 第三层：产物可观测性

**覆盖问题：** Issue 7, 8, 9

#### 3.1 Run ID 统一

`core/engine.py` 的 `__init__` 中，当 `run_dir` 为 None 时当前生成 `run-{uuid}`。

**修改：** 改为 `run-{YYYYMMDD-HHMMSS}` 格式。`run_id` 始终等于 `Path(run_dir).name`。Dashboard/Status/Trace 统一使用同一 run_id。

#### 3.2 Stage Records

`core/state_manager.py` 的 `RunState` 新增字段：

```python
stage_records: list[dict[str, Any]] = field(default_factory=list)
```

`core/engine.py` 的 `run_workflow` 每步执行后追加：

```python
self.state_manager.state.stage_records.append({
    "name": step["name"],
    "status": step_result.status,
    "duration_ms": step_result.duration_ms,
    "error": step_result.error,
})
```

Dashboard 优先从 `stage_records` 读取状态，fallback 到 `completed_modules`。

#### 3.3 Host Task CLI Fallback

新建 `runner/host_task.py`，三个函数：

- `get_next_task(run_dir) -> dict | None` — 读取 task.json
- `submit_result(run_dir, result_path) -> dict` — 复制 result 文件到 run_dir/result.json
- `get_status(run_dir) -> dict` — 读取 state.json

CLI 子命令 `reqflow host-task next/complete/status` 已在 cli.py 中定义，调用上述函数。

---

## 不做的事

- 不重写 engine 为状态机
- 不引入新的依赖
- 不修改 workflow YAML 格式
- 不修改 MCP 工具接口（除新增 reqflow_health）
- 不为每个平台写完整 adapter（只做 host + codex 薄 adapter）

## 测试策略

每个改动对应独立测试文件，TDD 驱动：

| 测试文件 | 覆盖 |
|---------|------|
| test_fail_fast.py | API adapter raise + engine fail-fast |
| test_runtime_readiness.py | readiness check + 默认 runtime 选择 |
| test_health.py | reqflow_health 工具 |
| test_manual_eof.py | manual EOF blocked |
| test_host_adapter.py | HostAgentAdapter task/result 协议 |
| test_dashboard_real.py | dashboard 真实状态 |
| test_run_id.py | run id 一致性 |
| test_stage_records.py | stage_records 写入 |
| test_host_task_cli.py | host task CLI fallback |
| test_mcp_run_integration.py | MCP 入口集成 |
