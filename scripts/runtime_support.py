#!/usr/bin/env python3
"""Shared helpers for Requirement Flow local runtime runners."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS_VALUES = {"not_started", "ready", "blocked", "failed", "complete"}

ARTIFACT_PATHS = {
    "prd_summary": "01_prd_summary.md",
    "spec_delta": "02_spec_delta.md",
    "workflow_intelligence": "03_workflow_intelligence.md",
    "context_discovery": "04_context_discovery.md",
    "tech_plan": "05_tech_plan.md",
    "impl_plan": "06_impl_plan.md",
    "agent_execution": "07_agent_execution.md",
    "code_review": "08_code_review.md",
    "verification": "09_verification.md",
    "archive": "10_archive.md",
    "agent_scenario": "agent/scenario.json",
    "agent_profile": "agent/profile.json",
    "agent_work_items_seed": "agent/work_items.seed.json",
    "agent_work_items": "agent/work_items.json",
    "agent_main_log": "agent/main-log.md",
    "agent_lessons": "agent/lessons-learned.md",
    "agent_evolution": "agent/evolution-report.md",
    "agent_compliance_report": "agent/compliance-report.md",
    "agent_memory": "agent/memory.md",
}

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


def load_providers(config_path: Path) -> dict:
    """Load providers.yaml -> dict of capability -> adapter config.
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


def get_provider(registry: dict, capability: str) -> dict | None:
    """Get adapter config for a capability.
    Returns None if not configured or disabled."""
    return registry.get(capability)


def manual_mode_fallback(capability: str, action: str, params: dict) -> dict:
    """Return blocked status with user action instructions."""
    return {
        "status": "blocked",
        "artifacts": [],
        "errors": [f"Provider for {capability}/{action} not configured. Manual action required."],
    }


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
    2. If not found -> manual_mode_fallback()
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

    if not Path(adapter_path).exists():
        return {
            "status": "failed",
            "artifacts": [],
            "errors": [f"Adapter script not found: {adapter_path}"],
        }

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


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_run_dir(run_dir: Path) -> Path:
    run_dir = run_dir.resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "agent/checklists").mkdir(parents=True, exist_ok=True)
    (run_dir / "agent/context-packs").mkdir(parents=True, exist_ok=True)
    (run_dir / "agent/reports").mkdir(parents=True, exist_ok=True)
    return run_dir


def read_text(path: Path, default: str = "") -> str:
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_state(run_dir: Path) -> dict[str, Any]:
    state = load_json(run_dir / "state.json", {})
    state.setdefault("artifact_paths", {})
    state["artifact_paths"].update({key: value for key, value in ARTIFACT_PATHS.items()})
    for section in [
        "spec_governance",
        "workflow_intelligence",
        "context_engine",
        "agent_execution",
        "delivery_verification",
        "archive",
        "providers",
    ]:
        state.setdefault(
            section,
            {
                "status": "not_started",
                "artifact_paths": [],
                "blockers": [],
                "last_updated_at": "",
                "evidence_refs": [],
            },
        )
    return state


def save_state(run_dir: Path, state: dict[str, Any]) -> None:
    write_json(run_dir / "state.json", state)


def update_section(
    state: dict[str, Any],
    section: str,
    status: str,
    artifact_paths: list[str],
    evidence_refs: list[str],
    blockers: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    if status not in STATUS_VALUES:
        raise ValueError(f"invalid status {status!r}")
    payload: dict[str, Any] = {
        "status": status,
        "artifact_paths": artifact_paths,
        "blockers": blockers or [],
        "last_updated_at": utc_now(),
        "evidence_refs": evidence_refs,
    }
    if extra:
        payload.update(extra)
    state[section] = payload


def first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or fallback
    return fallback


def requirement_text(run_dir: Path) -> str:
    state = load_json(run_dir / "state.json", {})
    if state.get("requirement"):
        return str(state["requirement"])
    return read_text(run_dir / ARTIFACT_PATHS["prd_summary"], "")
