#!/usr/bin/env python3
"""GitHub release adapter template using gh."""

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
        respond({"status": "success", "summary": "github release adapter structure is valid"})
        return 0
    auth = run(["gh", "auth", "status"])
    if auth.returncode != 0:
        respond({"status": "blocked", "action_required": "Run `gh auth login` and retry"})
        return 2
    if action == "check":
        respond({"status": "success", "summary": "gh auth is available"})
        return 0
    if action == "release":
        tag = ctx.get("tag")
        if not tag:
            respond({"status": "blocked", "action_required": "Provide context.tag for release creation"})
            return 2
        title = ctx.get("title", tag)
        notes = ctx.get("notes", "Created by Requirement Flow.")
        proc = run(["gh", "release", "create", tag, "--title", title, "--notes", notes], cwd=project_dir)
        if proc.returncode == 0:
            respond({"status": "success", "artifacts": {"release": proc.stdout.strip()}})
            return 0
        respond({"status": "failed", "errors": [{"stage": "release", "message": proc.stderr or proc.stdout}]})
        return 1
    respond({"status": "skipped", "summary": f"unsupported github release action {action}"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
