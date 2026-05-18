# V2 Provider Adapters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add runtime provider dispatch to the V1 contract-only adapter system so main-flow can automatically call configured provider adapters via subprocess, with manual mode fallback.

**Architecture:** Provider registry and dispatch functions added to `runtime_support.py`. YAML config maps capabilities to adapter scripts. Subprocess invocation preserves V1 JSON stdin/stdout contract. Unconfigured providers return blocked status.

**Tech Stack:** Python 3 (runtime_support.py), YAML (config), JSON (contract)

---

## File Structure

```text
requirement-flow-plugin/
├── scripts/
│   ├── runtime_support.py                    # MODIFY — add provider registry + dispatch
│   ├── provider_adapter_regression.py        # CREATE — regression tests
│   └── test_adapter_echo.py                  # CREATE — mock adapter for testing
├── templates/
│   └── providers.template.yaml               # MODIFY — add V2 adapter/params/enabled fields
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-05-13-v2-provider-adapters-design.md  # EXISTS
```

---

### Task 1: Add Provider Registry Functions

**Files:**
- Modify: `requirement-flow-plugin/scripts/runtime_support.py`
- Create: `requirement-flow-plugin/scripts/provider_adapter_regression.py`

- [ ] **Step 1: Add PROVIDER_CAPABILITIES constant to runtime_support.py**

Add after the `ARTIFACT_PATHS` dict:

```python
PROVIDER_CAPABILITIES = [
    "git_push",
    "pull_request",
    "release",
    "deploy",
    "package_publish",
    "container_publish",
    "log_query",
    "database_query",
    "message_trigger",
    "rpc_invoke",
    "auth_check",
]
```

- [ ] **Step 2: Add load_providers() function**

Add after the `PROVIDER_CAPABILITIES` list:

```python
def load_providers(config_path: Path) -> dict:
    """Load providers.yaml → dict of capability → adapter config.
    Returns empty dict if file not found (all manual mode)."""
    if not config_path.exists():
        return {}
    import yaml  # noqa: delay import for environments without yaml
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    raw = data.get("providers", {})
    registry = {}
    for name, cfg in raw.items():
        if not cfg.get("enabled", True):
            continue
        adapter = cfg.get("adapter", "")
        if not adapter:
            continue
        registry[name] = {
            "adapter": adapter,
            "params": cfg.get("params", {}),
        }
    return registry
```

- [ ] **Step 3: Add get_provider() function**

Add after `load_providers()`:

```python
def get_provider(registry: dict, capability: str) -> dict | None:
    """Get adapter config for a capability.
    Returns None if not configured or disabled."""
    return registry.get(capability)
```

- [ ] **Step 4: Create regression test file**

Create `requirement-flow-plugin/scripts/provider_adapter_regression.py`:

```python
#!/usr/bin/env python3
"""Regression test for V2 provider adapter functions."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from runtime_support import load_providers, get_provider, PROVIDER_CAPABILITIES


def test_load_providers_missing_file():
    result = load_providers(Path("/nonexistent/providers.yaml"))
    assert result == {}


def test_load_providers_valid(tmp_path=None):
    # Use a real YAML file if available, otherwise skip
    config_path = Path(__file__).resolve().parents[1] / "templates" / "providers.template.yaml"
    if not config_path.exists():
        return  # skip
    result = load_providers(config_path)
    assert isinstance(result, dict)


def test_get_provider_found():
    registry = {"git_push": {"adapter": "test.py", "params": {}}}
    result = get_provider(registry, "git_push")
    assert result is not None
    assert result["adapter"] == "test.py"


def test_get_provider_missing():
    registry = {"git_push": {"adapter": "test.py", "params": {}}}
    result = get_provider(registry, "deploy")
    assert result is None


def test_get_provider_empty_registry():
    result = get_provider({}, "git_push")
    assert result is None


def test_provider_capabilities_count():
    assert len(PROVIDER_CAPABILITIES) == 11


ALL_TESTS = [
    test_load_providers_missing_file,
    test_load_providers_valid,
    test_get_provider_found,
    test_get_provider_missing,
    test_get_provider_empty_registry,
    test_provider_capabilities_count,
]


def main() -> int:
    passed = 0
    failed = 0
    for test in ALL_TESTS:
        try:
            test()
            print(f"  PASS: {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {test.__name__}: {e}")
            failed += 1
    print(f"\nResults: {passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run regression test**

Run: `cd /Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin && python3 scripts/provider_adapter_regression.py`
Expected: All 6 tests PASS

- [ ] **Step 6: Commit**

---

### Task 2: Add Manual Mode Fallback

**Files:**
- Modify: `requirement-flow-plugin/scripts/runtime_support.py`
- Modify: `requirement-flow-plugin/scripts/provider_adapter_regression.py`

- [ ] **Step 1: Add manual_mode_fallback() function**

Add after `get_provider()` in `runtime_support.py`:

```python
def manual_mode_fallback(capability: str, action: str, params: dict) -> dict:
    """Return blocked status with user action instructions."""
    return {
        "status": "blocked",
        "artifacts": [],
        "errors": [f"Provider for {capability}/{action} not configured. Manual action required."],
    }
```

- [ ] **Step 2: Add manual mode test to regression file**

Add to `provider_adapter_regression.py`:

```python
from runtime_support import manual_mode_fallback


def test_manual_mode_fallback():
    result = manual_mode_fallback("git_push", "push", {"branch": "main"})
    assert result["status"] == "blocked"
    assert len(result["errors"]) == 1
    assert "git_push" in result["errors"][0]
    assert "Manual action required" in result["errors"][0]
    assert result["artifacts"] == []
```

Add `test_manual_mode_fallback` to the `ALL_TESTS` list.

- [ ] **Step 3: Run regression test**

Run: `cd /Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin && python3 scripts/provider_adapter_regression.py`
Expected: All tests PASS (7 total)

- [ ] **Step 4: Commit**

---

### Task 3: Add Dispatch Mechanism

**Files:**
- Modify: `requirement-flow-plugin/scripts/runtime_support.py`
- Create: `requirement-flow-plugin/scripts/test_adapter_echo.py`
- Modify: `requirement-flow-plugin/scripts/provider_adapter_regression.py`

- [ ] **Step 1: Create test adapter echo script**

Create `requirement-flow-plugin/scripts/test_adapter_echo.py`:

```python
#!/usr/bin/env python3
"""Test adapter that echoes input as success output. Used for testing dispatch."""

from __future__ import annotations

import json
import sys


def main() -> int:
    try:
        request = json.load(sys.stdin)
    except Exception as exc:
        print(json.dumps({
            "status": "failed",
            "artifacts": [],
            "errors": [f"Invalid JSON input: {exc}"],
        }))
        return 1

    action = request.get("action", "unknown")
    capability = request.get("capability", "unknown")
    print(json.dumps({
        "status": "success",
        "artifacts": [f"echo/{capability}/{action}"],
        "errors": [],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Add dispatch_provider() function**

Add after `manual_mode_fallback()` in `runtime_support.py`:

```python
PROVIDER_TIMEOUT_SECONDS = 30


def dispatch_provider(
    run_dir: Path,
    capability: str,
    action: str,
    params: dict,
    registry: dict,
) -> dict:
    """Dispatch a provider action via subprocess.

    1. Get adapter config from registry
    2. If not found → manual_mode_fallback()
    3. Build JSON input
    4. Run adapter with JSON on stdin
    5. Parse JSON output
    6. Return result dict
    """
    import subprocess  # noqa: delay import

    provider = get_provider(registry, capability)
    if provider is None:
        return manual_mode_fallback(capability, action, params)

    adapter_path = provider["adapter"]
    provider_params = provider.get("params", {})

    request = {
        "capability": capability,
        "action": action,
        "params": {**provider_params, **params},
        "run_dir": str(run_dir),
    }

    try:
        result = subprocess.run(
            [sys.executable, adapter_path],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=PROVIDER_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "failed",
            "artifacts": [],
            "errors": [f"Provider {capability}/{action} timed out after {PROVIDER_TIMEOUT_SECONDS}s."],
        }
    except FileNotFoundError:
        return {
            "status": "failed",
            "artifacts": [],
            "errors": [f"Adapter script not found: {adapter_path}"],
        }

    try:
        output = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        return {
            "status": "failed",
            "artifacts": [],
            "errors": [f"Provider returned invalid JSON: {result.stdout[:200]}"],
        }

    return {
        "status": output.get("status", "failed"),
        "artifacts": output.get("artifacts", []),
        "errors": output.get("errors", []),
    }
```

Also add `import sys` at the top of `runtime_support.py` (after `import json`):
```python
import sys
```

- [ ] **Step 3: Add dispatch tests to regression file**

Add to `provider_adapter_regression.py`:

```python
from runtime_support import dispatch_provider


def test_dispatch_provider_echo():
    registry = {"git_push": {
        "adapter": str(Path(__file__).resolve().parent / "test_adapter_echo.py"),
        "params": {},
    }}
    result = dispatch_provider(
        Path("/tmp/test-run"), "git_push", "push",
        {"branch": "main"}, registry,
    )
    assert result["status"] == "success"
    assert len(result["artifacts"]) == 1


def test_dispatch_provider_blocked():
    result = dispatch_provider(
        Path("/tmp/test-run"), "git_push", "push",
        {"branch": "main"}, {},
    )
    assert result["status"] == "blocked"


def test_dispatch_provider_missing_adapter():
    registry = {"git_push": {
        "adapter": "/nonexistent/adapter.py",
        "params": {},
    }}
    result = dispatch_provider(
        Path("/tmp/test-run"), "git_push", "push",
        {"branch": "main"}, registry,
    )
    assert result["status"] == "failed"
    assert any("not found" in e.lower() for e in result["errors"])
```

Add these 3 tests to the `ALL_TESTS` list.

- [ ] **Step 4: Run regression test**

Run: `cd /Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin && python3 scripts/provider_adapter_regression.py`
Expected: All tests PASS (10 total)

- [ ] **Step 5: Commit**

---

### Task 4: Add Timeout and Invalid JSON Tests

**Files:**
- Create: `requirement-flow-plugin/scripts/test_adapter_slow.py`
- Create: `requirement-flow-plugin/scripts/test_adapter_bad_json.py`
- Modify: `requirement-flow-plugin/scripts/provider_adapter_regression.py`

- [ ] **Step 1: Create slow adapter for timeout test**

Create `requirement-flow-plugin/scripts/test_adapter_slow.py`:

```python
#!/usr/bin/env python3
"""Test adapter that sleeps forever. Used for timeout testing."""

from __future__ import annotations

import time

def main() -> int:
    time.sleep(999)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Create bad JSON adapter**

Create `requirement-flow-plugin/scripts/test_adapter_bad_json.py`:

```python
#!/usr/bin/env python3
"""Test adapter that outputs invalid JSON. Used for error handling testing."""

from __future__ import annotations

def main() -> int:
    print("this is not json")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Add timeout and invalid JSON tests**

Add to `provider_adapter_regression.py`:

```python
def test_dispatch_provider_timeout():
    registry = {"git_push": {
        "adapter": str(Path(__file__).resolve().parent / "test_adapter_slow.py"),
        "params": {},
    }}
    # Temporarily set a short timeout
    import runtime_support
    old_timeout = runtime_support.PROVIDER_TIMEOUT_SECONDS
    runtime_support.PROVIDER_TIMEOUT_SECONDS = 1
    try:
        result = dispatch_provider(
            Path("/tmp/test-run"), "git_push", "push",
            {"branch": "main"}, registry,
        )
        assert result["status"] == "failed"
        assert any("timed out" in e.lower() for e in result["errors"])
    finally:
        runtime_support.PROVIDER_TIMEOUT_SECONDS = old_timeout


def test_dispatch_provider_invalid_json():
    registry = {"git_push": {
        "adapter": str(Path(__file__).resolve().parent / "test_adapter_bad_json.py"),
        "params": {},
    }}
    result = dispatch_provider(
        Path("/tmp/test-run"), "git_push", "push",
        {"branch": "main"}, registry,
    )
    assert result["status"] == "failed"
    assert any("invalid json" in e.lower() for e in result["errors"])
```

Add these 2 tests to the `ALL_TESTS` list.

- [ ] **Step 4: Run regression test**

Run: `cd /Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin && python3 scripts/provider_adapter_regression.py`
Expected: All tests PASS (12 total)

- [ ] **Step 5: Commit**

---

### Task 5: Update state.json and Templates

**Files:**
- Modify: `requirement-flow-plugin/scripts/runtime_support.py`
- Modify: `requirement-flow-plugin/templates/providers.template.yaml`
- Modify: `requirement-flow-plugin/scripts/provider_adapter_regression.py`

- [ ] **Step 1: Add providers section to load_state()**

In `runtime_support.py`, in the `load_state()` function, add `"providers"` to the section defaults list:

```python
    for section in [
        "spec_governance",
        "workflow_intelligence",
        "context_engine",
        "agent_execution",
        "delivery_verification",
        "archive",
        "providers",
    ]:
```

- [ ] **Step 2: Add write_dispatch_result() function**

Add after `dispatch_provider()`:

```python
def write_dispatch_result(run_dir: Path, capability: str, action: str, result: dict) -> None:
    """Write provider dispatch result to run artifacts for audit."""
    results_dir = run_dir / "agent" / "provider-results"
    results_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{capability}-{action}-{utc_now().replace(':', '-')}.json"
    write_json(results_dir / filename, {
        "capability": capability,
        "action": action,
        "result": result,
        "timestamp": utc_now(),
    })
```

- [ ] **Step 3: Update providers.template.yaml**

Replace the content of `requirement-flow-plugin/templates/providers.template.yaml`:

```yaml
# Requirement Flow V2 provider configuration.
# Store secrets in environment variables or keychains, not here.

providers:
  git_push:
    adapter: "templates/adapters/git_host/github.py"
    params:
      repo: "owner/repo"
      token_env: "GITHUB_TOKEN"
    enabled: true

  pull_request:
    adapter: "templates/adapters/git_host/github.py"
    params:
      repo: "owner/repo"
      token_env: "GITHUB_TOKEN"
    enabled: true

  release:
    adapter: "templates/adapters/release/generic.py"
    params: {}
    enabled: false

  deploy:
    adapter: "templates/adapters/deploy/generic.py"
    params:
      target: "staging"
    enabled: false

  package_publish:
    adapter: "templates/adapters/package_publish/generic.py"
    params:
      registry: "npm"
    enabled: false

  container_publish:
    adapter: "templates/adapters/container_publish/generic.py"
    params: {}
    enabled: false

  log_query:
    adapter: "templates/adapters/log_query/generic.py"
    params: {}
    enabled: false

  database_query:
    adapter: "templates/adapters/database_query/generic.py"
    params: {}
    enabled: false

  message_trigger:
    adapter: "templates/adapters/message_trigger/generic.py"
    params: {}
    enabled: false

  rpc_invoke:
    adapter: "templates/adapters/rpc_invoke/generic.py"
    params: {}
    enabled: false

  auth_check:
    adapter: "templates/adapters/auth/generic.py"
    params: {}
    enabled: false
```

- [ ] **Step 4: Add write_dispatch_result test**

Add to `provider_adapter_regression.py`:

```python
from runtime_support import write_dispatch_result


def test_write_dispatch_result(tmp_path=None):
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = Path(tmp)
        (run_dir / "agent").mkdir()
        result = {"status": "success", "artifacts": [], "errors": []}
        write_dispatch_result(run_dir, "git_push", "push", result)
        results_dir = run_dir / "agent" / "provider-results"
        assert results_dir.exists()
        files = list(results_dir.glob("git_push-push-*.json"))
        assert len(files) == 1
```

Add `test_write_dispatch_result` to the `ALL_TESTS` list.

- [ ] **Step 5: Run regression test**

Run: `cd /Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin && python3 scripts/provider_adapter_regression.py`
Expected: All tests PASS (13 total)

- [ ] **Step 6: Commit**

---

### Task 6: Update Unified Runtime Regression

**Files:**
- Modify: `requirement-flow-plugin/scripts/unified_runtime_regression.py`

- [ ] **Step 1: Read the current unified runtime regression file**

Read `requirement-flow-plugin/scripts/unified_runtime_regression.py` to understand existing assertions.

- [ ] **Step 2: Add provider state assertion**

Add an assertion that `state.json` includes the `providers` section after a run. Find where state assertions are made and add:

```python
    assert "providers" in state, "state.json should have providers section"
    assert state["providers"]["status"] == "not_started"
```

- [ ] **Step 3: Run unified runtime regression**

Run: `cd /Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin && python3 scripts/unified_runtime_regression.py`
Expected: PASS

- [ ] **Step 4: Commit**

---

### Task 7: Install and Verify

**Files:**
- All install roots

- [ ] **Step 1: Run plugin self-check**

Run: `cd /Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin && python3 scripts/plugin_self_check.py`
Expected: status success, 85 skills

- [ ] **Step 2: Run all regression tests**

Run: `cd /Users/yuanjulong/Documents/ai_flow/requirement-flow-plugin && python3 scripts/provider_adapter_regression.py && python3 scripts/workflow_intelligence_regression.py && python3 scripts/unified_runtime_regression.py && python3 scripts/agent_execution_regression.py`
Expected: All PASS

- [ ] **Step 3: Verify skill count unchanged**

Check that skill count is still 85 (no new skills, only modifications).

- [ ] **Step 4: Commit**
