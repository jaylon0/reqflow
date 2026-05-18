#!/usr/bin/env python3
"""Run configured or detected local project checks."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from pathlib import Path


def read_package_scripts(root: Path) -> dict:
    package_file = root / "package.json"
    if not package_file.exists():
        return {}
    try:
        return json.loads(package_file.read_text()).get("scripts", {}) or {}
    except Exception:
        return {}


def detect_commands(root: Path, scope: str) -> list[str]:
    commands: list[str] = []
    scripts = read_package_scripts(root)
    package_manager = "npm"
    if (root / "pnpm-lock.yaml").exists():
        package_manager = "pnpm"
    elif (root / "yarn.lock").exists():
        package_manager = "yarn"

    for script in ["lint", "typecheck", "test"]:
        if script in scripts:
            commands.append(f"{package_manager} run {script}")
    if scope == "full" and "build" in scripts:
        commands.append(f"{package_manager} run build")

    if (root / "pom.xml").exists():
        commands.append("mvn test" if scope == "focused" else "mvn package")
    if (root / "build.gradle").exists() or (root / "build.gradle.kts").exists():
        commands.append("./gradlew test" if scope == "focused" else "./gradlew build")
    if (root / "go.mod").exists():
        commands.append("go test ./...")
    if (root / "pyproject.toml").exists():
        commands.append("pytest")
    if (root / "Makefile").exists():
        commands.append("make test" if scope == "focused" else "make build")

    return commands


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--scope", choices=["focused", "full"], default="focused")
    parser.add_argument("--command", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(args.project_dir).resolve()
    commands = args.command or detect_commands(root, args.scope)

    if not commands:
        print(json.dumps({
            "status": "blocked",
            "action_required": "No check command configured or detected",
        }, indent=2))
        return 2

    results = []
    for command in commands:
        if args.dry_run:
            results.append({"command": command, "status": "skipped"})
            continue
        proc = subprocess.run(
            shlex.split(command),
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        output = proc.stdout[-4000:]
        results.append({
            "command": command,
            "exit_code": proc.returncode,
            "status": "success" if proc.returncode == 0 else "failed",
            "output_tail": output,
        })
        if proc.returncode != 0:
            print(json.dumps({"status": "failed", "results": results}, indent=2))
            return proc.returncode

    print(json.dumps({"status": "success", "results": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
