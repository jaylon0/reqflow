#!/usr/bin/env python3
"""Vercel deploy adapter template."""

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
        respond({"status": "success", "summary": "vercel adapter structure is valid"})
        return 0
    whoami = run(["vercel", "whoami"], cwd=project_dir)
    if whoami.returncode != 0:
        respond({"status": "blocked", "action_required": "Run `vercel login` and link the project if needed"})
        return 2
    if action == "check":
        respond({"status": "success", "artifacts": {"account": whoami.stdout.strip()}})
        return 0
    if action == "deploy":
        args = ["vercel", "--yes"]
        if ctx.get("production"):
            args.append("--prod")
        proc = run(args, cwd=project_dir)
        if proc.returncode == 0:
            respond({"status": "success", "artifacts": {"deploy_url": proc.stdout.strip().splitlines()[-1]}})
            return 0
        respond({"status": "failed", "errors": [{"stage": "deploy", "message": proc.stderr or proc.stdout}]})
        return 1
    respond({"status": "skipped", "summary": f"unsupported vercel action {action}"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
