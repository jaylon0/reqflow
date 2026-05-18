#!/usr/bin/env python3
"""npm publish adapter template."""

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
        respond({"status": "success", "summary": "npm adapter structure is valid"})
        return 0
    whoami = run(["npm", "whoami"], cwd=project_dir)
    if whoami.returncode != 0:
        respond({"status": "blocked", "action_required": "Run `npm login` or configure NPM_TOKEN"})
        return 2
    if action == "check":
        respond({"status": "success", "artifacts": {"account": whoami.stdout.strip()}})
        return 0
    if action in {"publish", "package_publish"}:
        args = ["npm", "publish"]
        if ctx.get("tag"):
            args.extend(["--tag", str(ctx["tag"])])
        proc = run(args, cwd=project_dir)
        if proc.returncode == 0:
            respond({"status": "success", "summary": "npm publish completed", "artifacts": {"output": proc.stdout[-1000:]}})
            return 0
        respond({"status": "failed", "errors": [{"stage": "npm_publish", "message": proc.stderr or proc.stdout}]})
        return 1
    respond({"status": "skipped", "summary": f"unsupported npm action {action}"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
