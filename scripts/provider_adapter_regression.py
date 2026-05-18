#!/usr/bin/env python3
"""Regression test for V2 provider adapter functions."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from runtime_support import load_providers, get_provider, manual_mode_fallback, PROVIDER_CAPABILITIES, dispatch_provider, write_dispatch_result


def _write_yaml(tmp_dir: Path, content: str) -> Path:
    p = tmp_dir / "providers.yaml"
    p.write_text(content, encoding="utf-8")
    return p


def test_load_providers_missing_file():
    result = load_providers(Path("/nonexistent/providers.yaml"))
    assert result == {}


def test_load_providers_valid():
    with tempfile.TemporaryDirectory() as tmp:
        cfg = _write_yaml(Path(tmp), """providers:
  git_push:
    adapter: "adapters/git_host/github.py"
    params:
      repo: "owner/repo"
    enabled: true
  deploy:
    adapter: "adapters/deploy/generic.py"
    params:
      target: "staging"
    enabled: true
""")
        result = load_providers(cfg)
        assert isinstance(result, dict)
        assert len(result) == 2
        assert "git_push" in result
        assert "deploy" in result
        assert result["git_push"]["adapter"] == "adapters/git_host/github.py"


def test_load_providers_disabled():
    with tempfile.TemporaryDirectory() as tmp:
        cfg = _write_yaml(Path(tmp), """providers:
  git_push:
    adapter: "adapters/git_host/github.py"
    params: {}
    enabled: true
  deploy:
    adapter: "adapters/deploy/generic.py"
    params: {}
    enabled: false
""")
        result = load_providers(cfg)
        assert "git_push" in result
        assert "deploy" not in result


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


def test_manual_mode_fallback():
    result = manual_mode_fallback("git_push", "push", {"branch": "main"})
    assert result["status"] == "blocked"
    assert len(result["errors"]) == 1
    assert "git_push" in result["errors"][0]
    assert "Manual action required" in result["errors"][0]
    assert result["artifacts"] == []


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


def test_dispatch_provider_timeout():
    registry = {"git_push": {
        "adapter": str(Path(__file__).resolve().parent / "test_adapter_slow.py"),
        "params": {},
    }}
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


def test_write_dispatch_result():
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


ALL_TESTS = [
    test_load_providers_missing_file,
    test_load_providers_valid,
    test_load_providers_disabled,
    test_get_provider_found,
    test_get_provider_missing,
    test_get_provider_empty_registry,
    test_provider_capabilities_count,
    test_manual_mode_fallback,
    test_dispatch_provider_echo,
    test_dispatch_provider_blocked,
    test_dispatch_provider_missing_adapter,
    test_dispatch_provider_timeout,
    test_dispatch_provider_invalid_json,
    test_write_dispatch_result,
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
