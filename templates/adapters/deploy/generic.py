#!/usr/bin/env python3
"""Generic deploy adapter template."""

import json
import subprocess
import sys


def respond(payload):
    print(json.dumps(payload, indent=2))


def main():
    req = json.load(sys.stdin)
    action = req.get("action", "check")
    ctx = req.get("context", {})
    if ctx.get("dry_run"):
        respond({"status": "success", "summary": "deploy adapter structure is valid"})
        return 0
    command = ctx.get("deploy_command")
    if not command:
        respond({
            "status": "blocked",
            "action_required": "Set context.deploy_command or customize this deploy adapter",
            "missing_capability": "deploy",
        })
        return 2
    if action == "check":
        respond({"status": "success", "summary": "deploy_command configured"})
        return 0
    proc = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if proc.returncode == 0:
        respond({"status": "success", "summary": "deploy command completed", "artifacts": {"output": proc.stdout[-1000:]}})
        return 0
    respond({"status": "failed", "errors": [{"stage": "deploy", "message": proc.stdout[-2000:]}]})
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
