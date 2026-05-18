#!/usr/bin/env python3
"""Generic read-only database query adapter template."""

import json
import re
import subprocess
import sys


READ_ONLY = re.compile(r"^\s*(select|show|desc|describe|explain)\b", re.IGNORECASE)


def respond(payload):
    print(json.dumps(payload, indent=2))


def main():
    req = json.load(sys.stdin)
    action = req.get("action", "check")
    ctx = req.get("context", {})
    if ctx.get("dry_run"):
        respond({"status": "success", "summary": "database query adapter structure is valid"})
        return 0
    command = ctx.get("database_query_command")
    sql = ctx.get("sql", "")
    if action == "check":
        respond({"status": "success", "summary": "read-only SQL guard enabled"})
        return 0
    if not command:
        respond({"status": "blocked", "action_required": "Set context.database_query_command for your database client"})
        return 2
    if not READ_ONLY.match(sql):
        respond({"status": "blocked", "action_required": "Only read-only SQL is allowed by this adapter"})
        return 2
    proc = subprocess.run(command, shell=True, text=True, input=sql, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    status = "success" if proc.returncode == 0 else "failed"
    respond({"status": status, "artifacts": {"output": proc.stdout[-2000:]}})
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
