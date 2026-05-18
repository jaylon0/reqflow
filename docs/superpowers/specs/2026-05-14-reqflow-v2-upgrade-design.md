# ReqFlow V2 Upgrade Design

> **Goal:** Upgrade ReqFlow from a skill-definition collection into a fully executable, graph-orchestrated, ecosystem-integrated workflow engine.

> **Architecture:** Three-phase incremental upgrade. Each phase produces a working, deliverable system. Phase 1 (core engine) is prerequisite for Phase 2 (graph orchestration). Phase 3 (ecosystem) can overlap with Phase 2.

---

## Phase 1: Core Engine Completion

### 1.1 API Adapter

**Problem:** Engine cannot actually call LLMs. Manual mode only outputs checklists. Claude mode depends on Claude Code environment.

**Solution:** Implement `core/adapters/api.py` with real HTTP-based LLM calls.

**Design:**
- Use `urllib3` (already in optional deps) for HTTP calls — no SDK dependency
- Support OpenAI-compatible API format (works with OpenAI, Anthropic, Gemini, DeepSeek via `/v1/chat/completions`)
- Unified `ModelResponse` dataclass: `content: str`, `tool_calls: list[ToolCall]`, `tokens: TokenUsage`
- Tool/function calling via JSON schema in request body
- Streaming support via SSE (optional, Phase 1.1+)

**API Adapter interface:**
```python
class APIAdapter:
    def __init__(self, config: RuntimeConfig):
        self.api_key = config.api_key
        self.base_url = config.api_base
        self.model = config.model

    async def call(self, prompt: str, tools: list[dict], context: str) -> ModelResponse:
        """Send prompt to LLM with tool definitions, return structured response."""

    async def execute_tool(self, tool_name: str, args: dict) -> ToolResult:
        """Execute a tool call and return result. For local tools (bash, read_file), execute locally."""

    def supports_capability(self, capability: str) -> bool:
        """Check if this adapter supports a capability (tool_calling, streaming, etc)."""
```

**RuntimeConfig additions:**
- `api_key: str` — API key (from env var or config)
- `api_base: str` — API base URL
- `model: str` — model ID (e.g., "gpt-4o", "claude-sonnet-4-6")

**Provider YAML additions:**
```yaml
# runtime/providers/gpt.yaml
api_base: "https://api.openai.com/v1"
model: "gpt-4o"
env_key: "OPENAI_API_KEY"
```

### 1.2 Test Suite Restructuring

**Problem:** Only 1 test file (444 lines), no pytest structure, no CI.

**Solution:** Split into per-module pytest files, add CI.

**Test structure:**
```
tests/
├── conftest.py              # shared fixtures
├── test_engine.py           # Engine workflow execution
├── test_workflow_loader.py  # YAML loading, stage conversion
├── test_state_manager.py    # state persistence, checkpoint, memory
├── test_tracer.py           # trace/span recording, export
├── test_guardrails.py       # constraint checking, file boundary
├── test_tool_bridge.py      # tool mapping, prompt formatting
├── test_context_adapter.py  # context formatting, truncation
├── test_api_adapter.py      # API adapter (mock HTTP)
├── test_graph.py            # Phase 2: graph engine
├── integration/
│   ├── test_fin_ktms.py     # fin-ktms integration (existing)
│   └── test_cli.py          # CLI end-to-end
```

**CI configuration:** GitHub Actions workflow for pytest on push/PR.

### 1.3 Parallel Agent Dispatch

**Problem:** verify+review agents execute sequentially.

**Solution:** Use `asyncio.gather` for parallel dispatch.

**Change in engine.py:**
```python
# Before (sequential):
verify_result = await self._dispatch_agent(verify_agent, verify_prompt)
review_result = await self._dispatch_agent(review_agent, review_prompt)

# After (parallel):
verify_result, review_result = await asyncio.gather(
    self._dispatch_agent(verify_agent, verify_prompt),
    self._dispatch_agent(review_agent, review_prompt),
)
```

**Configuration:** `max_concurrent_agents` in workflow YAML config section (default: 3).

---

## Phase 2: Graph Orchestration

### 2.1 Graph Engine Core

**Problem:** Workflow is linear (list of stages). Loop engine is hardcoded state machine. No support for branching, conditional edges, or parallel fan-out/fan-in.

**Solution:** Introduce `core/graph.py` with a directed graph execution engine.

**Core classes:**
```python
@dataclass
class Node:
    id: str
    type: Literal["agent", "tool", "decision", "human_gate", "subgraph"]
    handler: Callable  # function or agent reference
    config: dict = field(default_factory=dict)

@dataclass
class Edge:
    source: str  # node id
    target: str  # node id
    condition: Callable[[State], bool] | None = None  # None = unconditional

@dataclass
class Graph:
    nodes: dict[str, Node]
    edges: list[Edge]
    entry: str  # entry node id
    exit: list[str]  # terminal node ids

class GraphEngine:
    def __init__(self, graph: Graph, state: State):
        ...

    async def run(self) -> State:
        """Execute graph from entry to exit. State flows through nodes."""

    async def run_from(self, node_id: str) -> State:
        """Resume execution from a specific node (for checkpoint recovery)."""
```

**Node types:**
- `agent`: dispatches to an agent (dev, verify, review, repair, etc.)
- `tool`: executes a tool (build, deploy, verify-api, etc.)
- `decision`: evaluates condition, routes to different edges
- `human_gate`: pauses for human input (checkpoint)
- `subgraph`: embeds another graph (for loop engine, repair cycles)

**State passing:** Shared `State` dict flows through nodes. Each node reads from and writes to the state. State is checkpointed at configurable points.

### 2.2 Workflow YAML Upgrade

**Current format (linear):**
```yaml
stages:
  - id: 0
    name: "Stage 0"
    ...
  - id: 1
    name: "Stage 1"
    ...
```

**New format (graph):**
```yaml
graph:
  entry: "analyze"
  nodes:
    - id: "analyze"
      type: "agent"
      agent: "intelligence-agent"
      output: "intelligence_result"
    - id: "gate"
      type: "decision"
      condition: "state.confidence >= 0.7"
      edges:
        - target: "plan"
          when: "true"
        - target: "clarify"
          when: "false"
    - id: "clarify"
      type: "human_gate"
      prompt: "请确认场景检测结果"
      edges:
        - target: "plan"
    - id: "plan"
      type: "agent"
      ...
```

**Backward compatibility:** Linear `stages` format auto-converts to graph:
```
stages: [A, B, C] → graph with nodes [A, B, C] and edges [A→B, B→C]
```

### 2.3 Loop Engine Refactoring

**Current:** Hardcoded `observe → classify → localize → patch → verify → review → decide` state machine.

**Refactored:** Loop engine becomes a subgraph pattern:
```yaml
loop_engine:
  max_rounds: 3
  graph:
    entry: "observe"
    nodes:
      - id: "observe"
        type: "tool"
        tool: "read_failures"
      - id: "classify"
        type: "decision"
        condition: "classify_failure(state.failures)"
      - id: "patch"
        type: "agent"
        agent: "repair-agent"
      - id: "verify"
        type: "agent"
        agent: "verify-agent"
      - id: "review"
        type: "agent"
        agent: "review-agent"
      - id: "decide"
        type: "decision"
        condition: "should_continue(state)"
```

**Benefit:** Users can define custom repair strategies by providing their own loop graph.

---

## Phase 3: Ecosystem Integration

### 3.1 MCP Tool Bridge

**Problem:** ToolBridge uses custom tool definitions. No integration with MCP ecosystem.

**Solution:** `core/mcp_bridge.py` connects to MCP servers for tool discovery and invocation.

**Design:**
```python
class MCPBridge:
    def __init__(self, server_configs: list[MCPServerConfig]):
        ...

    async def discover_tools(self) -> list[Tool]:
        """Connect to MCP servers, discover available tools."""

    async def call_tool(self, server: str, tool: str, args: dict) -> ToolResult:
        """Call a tool on an MCP server."""
```

**Workflow YAML integration:**
```yaml
config:
  mcp_servers:
    - name: "database"
      command: "mcp-server-postgres"
      args: ["--connection-string", "..."]
    - name: "filesystem"
      command: "mcp-server-filesystem"
      args: ["/path/to/project"]
```

### 3.2 Observability Dashboard

**Problem:** Tracer records data but no visualization. Hard to debug multi-agent workflows.

**Solution:** Terminal-based TUI dashboard using `rich` library (optional dependency).

**Dashboard views:**
- Pipeline progress (current stage, completed stages)
- Agent status (running/idle, current task)
- Trace timeline (span hierarchy with durations)
- Checkpoint list (with resume capability)
- Error log (failures and repair rounds)

**Entry point:** `reqflow dashboard <run-dir>`

### 3.3 Session Management

**Problem:** No cross-turn context persistence. Each workflow run starts fresh.

**Solution:** `core/session.py` provides session-level state.

**Design:**
```python
class Session:
    def __init__(self, session_id: str, storage_dir: str):
        ...

    def save_context(self, key: str, value: Any):
        """Save a piece of context for this session."""

    def get_context(self, key: str) -> Any:
        """Retrieve context from this session."""

    def summarize(self) -> str:
        """Generate a compressed summary of session history for context window."""

    def list_sessions(self) -> list[str]:
        """List all sessions for the current project."""
```

**Integration:** Session auto-saves after each workflow step. On resume, loads session context into agent prompts.

---

## Cross-Cutting Concerns

### RuntimeConfig V2

```python
@dataclass
class RuntimeConfig:
    name: str
    display_name: str

    # API settings (Phase 1)
    api_key: str = ""
    api_base: str = ""
    model: str = ""

    # Capabilities
    capabilities: Capabilities

    # Tool mapping
    tool_mapping: dict[str, str]

    # Context format
    context_format: ContextFormat

    # MCP servers (Phase 3)
    mcp_servers: list[MCPServerConfig] = field(default_factory=list)

    # Paths
    run_dir: str = ""
```

### Backward Compatibility

- Existing `stages` format continues to work (auto-converted to graph)
- Existing `flow.yaml` and `main-flow.yaml` require no changes for Phase 1
- Phase 2 adds optional `graph` key; `stages` remains supported
- Phase 3 adds optional `mcp_servers` config; absence means no MCP

### Testing Strategy

- Phase 1: Unit tests for each module + integration test with fin-ktms
- Phase 2: Graph engine unit tests + workflow conversion tests
- Phase 3: MCP mock server tests + session persistence tests

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| API adapter breaks existing Claude Code embedding | ClaudeCodeAdapter remains default when `CLAUDE_CODE` env detected |
| Graph engine over-engineering | Phase 2 only adds graph; linear workflows keep working unchanged |
| MCP dependency conflicts | MCP is optional dependency (`pip install reqflow[mcp]`) |
| TUI dashboard terminal compatibility | Use `rich` which has broad terminal support; dashboard is optional |

---

## Phase Dependencies

```
Phase 1 (Core Engine)
  ├── 1.1 API Adapter
  ├── 1.2 Test Suite
  └── 1.3 Parallel Agents
        │
        ├──→ Phase 2 (Graph) ──→ 2.1 Graph Engine
        │                        ├── 2.2 YAML Upgrade
        │                        └── 2.3 Loop Refactor
        │
        └──→ Phase 3 (Ecosystem) ──→ 3.1 MCP Bridge
                                     ├── 3.2 Dashboard
                                     └── 3.3 Session
```

Phase 2 and Phase 3 can proceed in parallel after Phase 1 completes.
