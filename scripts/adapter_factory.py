#!/usr/bin/env python3
"""Generate project-local Requirement Flow provider adapters."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ALLOWED_STATUS = {"success", "failed", "blocked", "skipped"}
CAPABILITIES = {
    "auth",
    "git_host",
    "deploy",
    "release",
    "package_publish",
    "container_publish",
    "log_query",
    "database_query",
    "message_trigger",
    "rpc_invoke",
    "status",
    "manual",
}

WRITE_ACTIONS = {
    "auth": [],
    "git_host": ["push", "pull_request"],
    "deploy": ["deploy"],
    "release": ["release"],
    "package_publish": ["publish", "package_publish"],
    "container_publish": ["build", "push", "container_publish"],
    "log_query": [],
    "database_query": [],
    "message_trigger": ["trigger", "send"],
    "rpc_invoke": ["invoke"],
    "status": [],
    "manual": [],
}


def plugin_root() -> Path:
    return Path(__file__).resolve().parents[1]


def template_path(capability: str, platform: str) -> tuple[Path, str]:
    base = plugin_root() / "templates" / "adapters" / capability
    exact = base / f"{platform}.py"
    if exact.exists():
        return exact, f"{capability}/{platform}.py"
    generic = base / "generic.py"
    if generic.exists():
        return generic, f"{capability}/generic.py"
    return plugin_root() / "scripts" / "provider_adapter_stub.py", "provider_adapter_stub.py"


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def append_manifest(manifest: Path, entry: dict) -> None:
    manifest.parent.mkdir(parents=True, exist_ok=True)
    block = [
        "- name: " + yaml_quote(entry["name"]),
        "  capability: " + yaml_quote(entry["capability"]),
        "  platform: " + yaml_quote(entry["platform"]),
        "  template: " + yaml_quote(entry["template"]),
        "  template_version: " + yaml_quote(entry["template_version"]),
        "  adapter_file: " + yaml_quote(entry["adapter_file"]),
        "  run_command: " + yaml_quote(entry["run_command"]),
        "  check_command: " + yaml_quote(entry["check_command"]),
    ]
    if entry["external_write_actions"]:
        block.append("  external_write_actions:")
        for action in entry["external_write_actions"]:
            block.append("    - " + yaml_quote(action))
    else:
        block.append("  external_write_actions: []")
    block.extend([
        "  generated_at: " + yaml_quote(entry["generated_at"]),
        "  user_maintained: false",
        "",
    ])

    if not manifest.exists():
        manifest.write_text("adapters:\n" + "\n".join("  " + line if line else "" for line in block))
        return

    text = manifest.read_text()
    if f'name: "{entry["name"]}"' in text:
        raise FileExistsError(f"manifest already contains adapter {entry['name']}")
    with manifest.open("a") as f:
        f.write("\n")
        for line in block:
            f.write(("  " + line if line else "") + "\n")


def append_provider_config(config: Path, capability: str, platform: str, adapter_rel: str) -> None:
    config.parent.mkdir(parents=True, exist_ok=True)
    block = f"""
  {capability}_{platform}:
    type: "custom"
    capabilities:
      - "{capability}"
    run_command: "python3 {adapter_rel}"
    check_command: "python3 {adapter_rel}"
    confirm_before_write: true
"""
    if not config.exists():
        config.write_text("# Generated provider entries. Store secrets outside this file.\nproviders:\n")
    text = config.read_text()
    key = f"  {capability}_{platform}:"
    if key in text:
        return
    with config.open("a") as f:
        f.write(block)


def validate_adapter(adapter: Path, capability: str, project: Path) -> tuple[str, str]:
    sample = {
        "action": "check",
        "project_dir": str(project),
        "environment": "dry-run",
        "change": {"branch": "", "commit": "", "files": []},
        "context": {
            "dry_run": True,
            "capability": capability,
        },
    }
    proc = subprocess.run(
        [sys.executable, str(adapter)],
        input=json.dumps(sample),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        data = json.loads(proc.stdout)
    except Exception as exc:
        return "failed", f"adapter did not return JSON: {exc}; stderr={proc.stderr[-500:]}"
    status = data.get("status")
    if status not in ALLOWED_STATUS:
        return "failed", f"adapter returned invalid status: {status!r}"
    return status, json.dumps(data, ensure_ascii=False)


def write_plan(args, target: Path, template: Path, template_name: str) -> dict:
    rel = target.relative_to(Path(args.project_dir).resolve())
    return {
        "status": "planned",
        "capability": args.capability,
        "platform": args.platform,
        "template": template_name,
        "adapter_file": str(target),
        "provider_config": str(Path(args.project_dir).resolve() / ".dev-workflow.example" / "providers.template.yaml"),
        "actions": [
            f"copy {template} to {target}",
            f"register provider command python3 {rel}",
            "run structure dry-run",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--capability", required=True, choices=sorted(CAPABILITIES))
    parser.add_argument("--platform", default="generic")
    parser.add_argument("--name", default="")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    project = Path(args.project_dir).resolve()
    platform = args.platform.replace("-", "_")
    name = args.name or platform

    template, template_name = template_path(args.capability, platform)
    target_dir = project / ".dev-workflow.example" / "adapters" / args.capability
    target = target_dir / f"{name}.py"
    manifest = project / ".dev-workflow.example" / "adapters" / "adapter-manifest.yaml"
    provider_config = project / ".dev-workflow.example" / "providers.template.yaml"

    if not args.write:
        print(json.dumps(write_plan(args, target, template, template_name), indent=2))
        return 0

    if target.exists():
        print(json.dumps({
            "status": "blocked",
            "action_required": (
                f"Adapter already exists at {target}. Review it and apply a minimal patch "
                "manually, or choose a different --name."
            ),
            "adapter_file": str(target),
            "template": str(template),
        }, indent=2))
        return 2

    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template, target)
    target.chmod(0o755)

    adapter_rel = str(target.relative_to(project))
    entry = {
        "name": f"{args.capability}_{name}",
        "capability": args.capability,
        "platform": platform,
        "template": template_name,
        "template_version": "1",
        "adapter_file": adapter_rel,
        "run_command": f"python3 {adapter_rel}",
        "check_command": f"python3 {adapter_rel}",
        "external_write_actions": WRITE_ACTIONS.get(args.capability, []),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    append_manifest(manifest, entry)
    append_provider_config(provider_config, args.capability, platform, adapter_rel)
    validation_status, validation_output = validate_adapter(target, args.capability, project)

    print(json.dumps({
        "status": "generated",
        "adapter_file": str(target),
        "manifest_file": str(manifest),
        "provider_config": str(provider_config),
        "validation_status": validation_status,
        "validation_output": validation_output,
    }, indent=2))
    return 0 if validation_status in ALLOWED_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
