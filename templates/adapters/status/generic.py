#!/usr/bin/env python3
"""Generic status adapter template."""

import json
import subprocess
import sys


def main():
    req = json.load(sys.stdin)
    ctx = req.get("context", {})
    if ctx.get("dry_run"):
        print(json.dumps({"status": "success", "summary": "status adapter structure is valid"}, indent=2))
        return 0
    command = ctx.get("status_command")
    if not command:
        print(json.dumps({"status": "blocked", "action_required": "Set context.status_command"}, indent=2))
        return 2
    proc = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(json.dumps({
        "status": "success" if proc.returncode == 0 else "failed",
        "artifacts": {"output": proc.stdout[-2000:]},
    }, indent=2))
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
