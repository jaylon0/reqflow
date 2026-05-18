#!/usr/bin/env python3
"""GitHub adapter template using the GitHub CLI."""

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
        respond({"status": "success", "summary": "github adapter structure is valid"})
        return 0
    auth = run(["gh", "auth", "status"])
    if auth.returncode != 0:
        respond({"status": "blocked", "action_required": "Run `gh auth login` and retry"})
        return 2
    if action == "check":
        remote = run(["git", "remote", "get-url", "origin"], cwd=project_dir)
        respond({"status": "success", "artifacts": {"remote": remote.stdout.strip()}})
        return 0
    if action == "push":
        branch = run(["git", "branch", "--show-current"], cwd=project_dir).stdout.strip()
        proc = run(["git", "push", "-u", "origin", branch], cwd=project_dir)
        if proc.returncode == 0:
            respond({"status": "success", "summary": f"pushed branch {branch}"})
            return 0
        respond({"status": "failed", "errors": [{"message": proc.stderr or proc.stdout}]})
        return 1
    if action == "pull_request":
        title = ctx.get("title", "Requirement Flow change")
        body = ctx.get("body", "Created by Requirement Flow.")
        proc = run(["gh", "pr", "create", "--title", title, "--body", body], cwd=project_dir)
        if proc.returncode == 0:
            respond({"status": "success", "artifacts": {"pull_request": proc.stdout.strip()}})
            return 0
        respond({"status": "failed", "errors": [{"message": proc.stderr or proc.stdout}]})
        return 1
    respond({"status": "skipped", "summary": f"unsupported github action {action}"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
