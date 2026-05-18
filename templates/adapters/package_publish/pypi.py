#!/usr/bin/env python3
"""PyPI publish adapter template using twine."""

import json
import subprocess
import sys


def run(args, cwd=None):
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def respond(payload):
    print(json.dumps(payload, indent=2))


def main():
    req = json.load(sys.stdin)
    action = req.get("action", "check")
    project_dir = req.get("project_dir", ".")
    ctx = req.get("context", {})
    if ctx.get("dry_run"):
        respond({"status": "success", "summary": "pypi adapter structure is valid"})
        return 0
    twine = run(["python3", "-m", "twine", "--version"], cwd=project_dir)
    if twine.returncode != 0:
        respond({"status": "blocked", "action_required": "Install twine and configure PyPI credentials outside source control"})
        return 2
    if action == "check":
        respond({"status": "success", "artifacts": {"twine": twine.stdout.strip()}})
        return 0
    if action in {"publish", "package_publish"}:
        dist = ctx.get("dist", "dist/*")
        proc = run(["python3", "-m", "twine", "upload", dist], cwd=project_dir)
        if proc.returncode == 0:
            respond({"status": "success", "summary": "PyPI upload completed", "artifacts": {"output": proc.stdout[-1000:]}})
            return 0
        respond({"status": "failed", "errors": [{"stage": "pypi_publish", "message": proc.stderr or proc.stdout}]})
        return 1
    respond({"status": "skipped", "summary": f"unsupported pypi action {action}"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
