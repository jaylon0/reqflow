# V2 Provider Adapters Design

## Overview

V2 Provider Adapters adds runtime provider dispatch to the V1 contract-only adapter system. The main-flow can automatically call configured provider adapters via subprocess, with manual mode fallback when providers are not configured.

## Architecture

```text
main-flow steps (3, 4, 5, 6, 7, 8, 9, 10)
      │
      ▼
runtime_support.py
  ├── load_providers(config_path) → registry dict
  ├── get_provider(registry, capability) → adapter config | None
  ├── dispatch_provider(run_dir, capability, action, params, registry) → result dict
  └── manual_mode_fallback(capability, action, params) → blocked result
      │
      ▼ (subprocess)
provider adapter script (templates/adapters/<capability>/<impl>.py)
      │
      ▼ (JSON stdin/stdout)
{ status, artifacts, errors }
```

**Responsibilities:**
- `runtime_support.py`: provider registry, dispatch, manual mode fallback
- Provider adapter scripts: execute actual work (git push, deploy, etc.)
- YAML config: maps capability → adapter script path + parameters
- main-flow steps: call `dispatch_provider()` when provider work is needed

**Key constraints:**
- Subprocess invocation preserves V1 JSON stdin/stdout contract
- Unconfigured providers → manual mode (blocked status, user action needed)
- Provider results written to run artifacts for audit
- No provider secrets in run artifacts

## Provider Registry

### YAML Config Format

Extends existing `providers.template.yaml`:

```yaml
providers:
  git_host:
    adapter: "templates/adapters/git_host/github.py"
    params:
      repo: "owner/repo"
      token_env: "GITHUB_TOKEN"
    enabled: true
  deploy:
    adapter: "templates/adapters/deploy/generic.py"
    params:
      target: "staging"
    enabled: false  # manual mode
  package_publish:
    adapter: "templates/adapters/package_publish/generic.py"
    params:
      registry: "npm"
    enabled: true
  # ... other capabilities
```

### Registry Functions

```python
def load_providers(config_path: Path) -> dict:
    """Load providers.yaml → dict of capability → adapter config.
    Returns empty dict if file not found (all manual mode)."""

def get_provider(registry: dict, capability: str) -> dict | None:
    """Get adapter config for a capability.
    Returns None if not configured or disabled."""
```

### 11 Capabilities

| Capability | Description | Typical Steps |
|------------|-------------|---------------|
| git_push | Push to remote | 10 |
| pull_request | Create PR | 10 |
| release | Create release | 10 |
| deploy | Deploy to environment | 9 |
| package_publish | Publish package | 9 |
| container_publish | Publish container | 9 |
| log_query | Query logs | 9 |
| database_query | Query database | 9 |
| message_trigger | Trigger message | 9 |
| rpc_invoke | Invoke RPC | 9 |
| auth_check | Check auth | 9 |

## Dispatch Mechanism

### Dispatch Function

```python
def dispatch_provider(
    run_dir: Path,
    capability: str,
    action: str,
    params: dict,
    registry: dict,
) -> dict:
    """Dispatch a provider action via subprocess.

    1. Get adapter config from registry
    2. If not found or disabled → manual_mode_fallback()
    3. Build JSON input: { capability, action, params, run_dir }
    4. Run: python <adapter_path> with JSON on stdin
    5. Parse JSON output: { status, artifacts, errors }
    6. Write result to run artifacts for audit
    7. Return result dict
    """
```

### JSON Contract (Preserves V1)

Input:
```json
{
  "capability": "git_push",
  "action": "push",
  "params": {"branch": "main", "remote": "origin"},
  "run_dir": ".dev-workflow/runs/run-123"
}
```

Output:
```json
{
  "status": "success|blocked|failed",
  "artifacts": ["path/to/artifact"],
  "errors": []
}
```

### Manual Mode Fallback

```python
def manual_mode_fallback(capability: str, action: str, params: dict) -> dict:
    """Return blocked status with user action instructions."""
    return {
        "status": "blocked",
        "artifacts": [],
        "errors": [f"Provider for {capability}/{action} not configured. Manual action required."],
    }
```

## Integration Points

### main-flow Steps That Use Providers

| Step | Provider Usage | Capabilities (V2) |
|------|---------------|--------------|
| 3 | Workflow intelligence (future) | — |
| 4 | Context discovery (future) | — |
| 7 | Agent execution (future) | — |
| 9 | Delivery verification | deploy, package_publish, container_publish, log_query, database_query, message_trigger, rpc_invoke, auth_check |
| 10 | Archive (git push, PR, release) | git_push, pull_request, release |

### Integration Pattern in Runner Scripts

```python
from runtime_support import load_providers, dispatch_provider

registry = load_providers(run_dir / "providers.yaml")

# Example: Step 10 git push
result = dispatch_provider(run_dir, "git_push", "push",
                           {"branch": branch, "remote": "origin"}, registry)
if result["status"] == "blocked":
    # Write to pending_confirmations
    ...
```

### state.json Additions

```json
{
  "providers": {
    "config_path": "providers.yaml",
    "registry_loaded": true,
    "dispatch_history": [
      {"capability": "git_push", "action": "push", "status": "success", "timestamp": "..."}
    ]
  }
}
```

## Testing

### Unit Tests

`provider_adapter_regression.py`:

- `test_load_providers_valid` — loads YAML config correctly
- `test_load_providers_missing_file` — returns empty dict
- `test_get_provider_found` — returns adapter config
- `test_get_provider_disabled` — returns None
- `test_get_provider_missing` — returns None
- `test_manual_mode_fallback` — returns blocked status
- `test_dispatch_provider_success` — subprocess mock returns success
- `test_dispatch_provider_blocked` — unconfigured provider returns blocked
- `test_dispatch_provider_failed` — adapter returns failed status
- `test_dispatch_provider_timeout` — subprocess timeout handling
- `test_dispatch_provider_invalid_json` — malformed adapter output

### Integration with Existing Regressions

- `unified_runtime_regression.py` — verify provider fields in state.json
- `plugin_self_check.py` — skill count unchanged

### Mock Strategy

Use a test adapter script that returns deterministic JSON. No real provider calls in tests.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Dispatch mechanism | Subprocess | Preserves V1 JSON contract, adapter isolation |
| Registry location | runtime_support.py | Natural extension of existing runtime |
| Config format | YAML | Matches existing providers.template.yaml |
| Manual mode | Blocked status | User action required, not silent failure |
| Capabilities | All 11 | Complete coverage for delivery flow |
| Test approach | Mock adapter script | Deterministic, no real provider calls |

## Out of Scope (V2)

- Real provider implementations (GitHub API, K8s deploy, etc.)
- Provider authentication management
- Provider health checks
- Async/polling for long-running providers
- Provider retry logic
