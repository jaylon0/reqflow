#!/usr/bin/env python3
"""Generic log query adapter template."""

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
        respond({"status": "success", "summary": "log query adapter structure is valid"})
        return 0
    command = ctx.get("log_query_command")
    if not command:
        respond({"status": "blocked", "action_required": "Set context.log_query_command or use manual log checks"})
        return 2
    if action == "check":
        respond({"status": "success", "summary": "log_query_command configured"})
        return 0
    proc = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    status = "success" if proc.returncode == 0 else "failed"
    respond({"status": status, "artifacts": {"output": proc.stdout[-2000:]}})
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
