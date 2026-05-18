# Java Context Engine Local V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local, zero-dependency V1 Java context provider that writes run-level heuristic graph, semantic, impact, and context-pack artifacts.

**Architecture:** Keep existing Java context skills as workflow entry points. Add one Python provider script that scans Java source heuristically and writes provider-shaped artifacts under a run directory. Add one regression script that creates a temporary Java project and verifies the provider outputs without external services.

**Tech Stack:** Python standard library, Markdown skills, JSON run artifacts.

---

## File Structure

- Create `requirement-flow-plugin/scripts/java_context_engine_regression.py`: TDD regression driver that builds a temporary Java project, runs the provider CLI, and asserts artifact behavior.
- Create `requirement-flow-plugin/scripts/java_context_engine.py`: local provider CLI with source scanning, semantic ranking, impact merge, and markdown artifact writing.
- Modify `requirement-flow-plugin/skills/java-context-engine/SKILL.md`: document local V1 provider first, manual/blocked fallback second.
- Modify `requirement-flow-plugin/skills/java-code-graph/SKILL.md`: document local graph response artifact behavior.
- Modify `requirement-flow-plugin/skills/java-semantic-index/SKILL.md`: document local semantic response artifact behavior.
- Modify `requirement-flow-plugin/skills/java-impact-analysis/SKILL.md`: document local impact response artifact behavior.

## Task 1: Write Regression First

**Files:**
- Create: `requirement-flow-plugin/scripts/java_context_engine_regression.py`

- [ ] **Step 1: Add failing regression script**

Create a Python script that:

- Creates a temporary Java project with:
  `OrderController` annotated with `@RestController`, `@RequestMapping("/orders")`, and `@GetMapping("/list")`;
  `OrderController.list(OrderDTO)` calling `OrderService.listOrders(dto)`;
  `OrderService.listOrders(OrderDTO)` calling `OrderMapper.countOrders(dto)` and `OrderMapper.listOrders(dto, total)`;
  `OrderDTO` and `OrderVO` classes.
- Runs:
  `python3 scripts/java_context_engine.py analyze --project-root <tmp-project> --run-dir <tmp-run> --requirement "新增订单列表筛选并同步 list count 查询" --top-k 5`
- Expects these files:
  `graph/java-code-graph.response.json`,
  `rag/java-semantic-index.response.json`,
  `graph/java-impact-analysis.response.json`,
  `agent/context-packs/java-context.md`,
  `03_context_discovery.md`.
- Asserts:
  controller entrypoint is found,
  at least one call chain mentions controller, service, and mapper symbols,
  semantic matches include controller or service,
  risk signals mention list/count and DTO/VO or Mapper,
  a low-confidence requirement such as `"完全无关的天文观测需求"` produces non-empty `missing_context`.

- [ ] **Step 2: Verify RED**

Run:

Run from `/Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin`:

```bash
python3 scripts/java_context_engine_regression.py
```

Expected before implementation: failure because `scripts/java_context_engine.py` does not exist or provider artifacts are missing.

## Task 2: Implement Local Provider CLI

**Files:**
- Create: `requirement-flow-plugin/scripts/java_context_engine.py`

- [ ] **Step 1: Add CLI skeleton**

Implement `analyze` with arguments:

```text
--project-root <path>
--run-dir <path>
--requirement <text>
--scope-path <path> optional, repeatable or single path
--top-k <int> default 20
```

The command must create `graph/`, `rag/`, and `agent/context-packs/` under the run directory.

- [ ] **Step 2: Add Java source scanner**

Scan `.java` files under `project-root`, limited by `scope-path` when provided. Extract package, class/interface names, method names, annotations, route annotations, comments, simple method calls, and referenced class-like identifiers.

- [ ] **Step 3: Write graph response**

Write `graph/java-code-graph.response.json` with:

```json
{
  "status": "success",
  "provider": "local-source-scan-v1",
  "graph_version": "local-source-scan-v1",
  "entrypoints": [],
  "call_chains": [],
  "affected_nodes": [],
  "risk_signals": [],
  "evidence": []
}
```

Populate evidence with file/symbol/source references. Do not claim bytecode or real graph database evidence.

- [ ] **Step 4: Write semantic response**

Write `rag/java-semantic-index.response.json` with:

```json
{
  "status": "success",
  "provider": "local-lexical-semantic-v1",
  "index_version": "local-lexical-semantic-v1",
  "matches": [],
  "missing_context": []
}
```

Rank candidates using local tokens from path, class, method, annotations, comments, and requirement text. Include score, reason, and source reference.

- [ ] **Step 5: Write impact response**

Write `graph/java-impact-analysis.response.json` with status, provider, `entrypoint_confidence`, candidate files/modules/symbols, risk signals, required follow-ups, missing context, and evidence refs.

- [ ] **Step 6: Write markdown artifacts**

Write `agent/context-packs/java-context.md` and `03_context_discovery.md`. Markdown must summarize artifact paths and evidence, not paste large source bodies.

- [ ] **Step 7: Verify GREEN**

Run:

Run from `/Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin`:

```bash
python3 scripts/java_context_engine_regression.py
```

Expected: regression passes.

## Task 3: Update Java Context Skills

**Files:**
- Modify: `requirement-flow-plugin/skills/java-context-engine/SKILL.md`
- Modify: `requirement-flow-plugin/skills/java-code-graph/SKILL.md`
- Modify: `requirement-flow-plugin/skills/java-semantic-index/SKILL.md`
- Modify: `requirement-flow-plugin/skills/java-impact-analysis/SKILL.md`

- [ ] **Step 1: Update provider guidance**

Each skill should say the local V1 provider is the default first attempt when a Java project root and run directory are available.

- [ ] **Step 2: Preserve evidence honesty**

Each skill must retain the rule that heuristic local source scan evidence is not ASM bytecode, graph database, or true vector RAG evidence.

- [ ] **Step 3: Verify skill structure**

Run:

```bash
python3 requirement-flow-plugin/scripts/plugin_self_check.py --root requirement-flow-plugin
```

Run from `/Users/yuanjulong/Documents/ai_flow`. Expected: top-level status is `success`.

## Task 4: Source Verification And Review

**Files:**
- Verify all changed files.

- [ ] **Step 1: Run regression**

Run from `/Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin`:

```bash
python3 scripts/java_context_engine_regression.py
```

Expected: regression passes.

- [ ] **Step 2: Run plugin self-check**

```bash
python3 requirement-flow-plugin/scripts/plugin_self_check.py --root requirement-flow-plugin
```

Run from `/Users/yuanjulong/Documents/ai_flow`. Expected: top-level status is `success`.

- [ ] **Step 3: Run placeholder scan**

```bash
rg -n "T[B]D|T[O]DO|F[I]XME|待[定]|未[定]" requirement-flow-plugin/scripts requirement-flow-plugin/skills/java-context-engine requirement-flow-plugin/skills/java-code-graph requirement-flow-plugin/skills/java-semantic-index requirement-flow-plugin/skills/java-impact-analysis
```

Run from `/Users/yuanjulong/Documents/ai_flow`. Expected: no matches introduced by this iteration.

- [ ] **Step 4: Run code review**

Use a fresh code-review subagent for spec compliance and code quality. Fix critical or important findings, then repeat verification.

## Task 5: Sync Installed Copies

**Files:**
- Sync source tree to installed plugin locations only after source verification passes.

- [ ] **Step 1: Validate install roots**

Run from `/Users/yuanjulong/Documents/ai_flow`:

```bash
test -f /Users/yuanjulong/.codex/plugins/marketplaces/local-requirement-flow/plugins/requirement-flow-plugin/.codex-plugin/plugin.json
test -f /Users/yuanjulong/.codex/plugins/cache/local-requirement-flow/requirement-flow-plugin/0.1.0/.codex-plugin/plugin.json
test -f /Users/yuanjulong/.codeflicker/plugins/installed/requirement-flow-plugin/.codex-plugin/plugin.json
test -f /Users/yuanjulong/.claude/plugins/marketplaces/local-requirement-flow/plugins/requirement-flow-plugin/.claude-plugin/plugin.json
test -f /Users/yuanjulong/.claude/plugins/cache/local-requirement-flow/requirement-flow-plugin/0.1.0/.claude-plugin/plugin.json
```

Expected: all commands exit with status 0. If any root is missing, stop and ask before syncing.

- [ ] **Step 2: Sync Codex marketplace and cache**

Use these exact commands from `/Users/yuanjulong/Documents/ai_flow`:

```bash
rsync -a --delete --exclude .DS_Store --exclude .git/ --exclude .dev-workflow/ --exclude __pycache__/ --exclude '*.pyc' requirement-flow-plugin/ /Users/yuanjulong/.codex/plugins/marketplaces/local-requirement-flow/plugins/requirement-flow-plugin/
rsync -a --delete --exclude .DS_Store --exclude .git/ --exclude .dev-workflow/ --exclude __pycache__/ --exclude '*.pyc' requirement-flow-plugin/ /Users/yuanjulong/.codex/plugins/cache/local-requirement-flow/requirement-flow-plugin/0.1.0/
```

- [ ] **Step 3: Sync CodeFlicker installed plugin**

Use this exact command from `/Users/yuanjulong/Documents/ai_flow`:

```bash
rsync -a --delete --exclude .DS_Store --exclude .git/ --exclude .dev-workflow/ --exclude __pycache__/ --exclude '*.pyc' requirement-flow-plugin/ /Users/yuanjulong/.codeflicker/plugins/installed/requirement-flow-plugin/
```

- [ ] **Step 4: Sync Claude marketplace and cache**

Use these exact commands from `/Users/yuanjulong/Documents/ai_flow`:

```bash
rsync -a --delete --exclude .DS_Store --exclude .git/ --exclude .dev-workflow/ --exclude __pycache__/ --exclude '*.pyc' requirement-flow-plugin/ /Users/yuanjulong/.claude/plugins/marketplaces/local-requirement-flow/plugins/requirement-flow-plugin/
rsync -a --delete --exclude .DS_Store --exclude .git/ --exclude .dev-workflow/ --exclude __pycache__/ --exclude '*.pyc' requirement-flow-plugin/ /Users/yuanjulong/.claude/plugins/cache/local-requirement-flow/requirement-flow-plugin/0.1.0/
```

- [ ] **Step 5: Verify install roots**

Run `plugin_self_check.py` with source root plus all install roots via `--install-root`.

Expected: top-level status is `success`.

## Non-goals

- Do not implement ASM bytecode parsing.
- Do not start Neo4j, vector databases, or external services.
- Do not generate project-level context skills.
- Do not add global install logic to plugin runtime.
- Do not move development-only evaluation material back into plugin runtime skills.
