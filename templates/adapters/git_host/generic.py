#!/usr/bin/env python3
"""Generic git host adapter template."""

import json
import subprocess
import sys


def sh(args):
    return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def respond(payload):
    print(json.dumps(payload, indent=2))


def main():
    req = json.load(sys.stdin)
    action = req.get("action", "check")
    project_dir = req.get("project_dir", ".")
    ctx = req.get("context", {})
    if ctx.get("dry_run"):
        respond({"status": "success", "summary": "git host adapter structure is valid"})
        return 0
    remote = sh(["git", "-C", project_dir, "remote", "get-url", "origin"])
    if remote.returncode != 0:
        respond({"status": "blocked", "action_required": "Configure git remote origin"})
        return 2
    if action == "check":
        respond({"status": "success", "artifacts": {"remote": remote.stdout.strip()}})
        return 0
    respond({
        "status": "blocked",
        "action_required": "Implement this git host action for your provider",
        "missing_capability": action,
    })
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
