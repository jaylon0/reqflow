#!/usr/bin/env python3
"""Generic auth adapter template."""

import json
import os
import sys


def respond(payload):
    print(json.dumps(payload, indent=2))


def main():
    req = json.load(sys.stdin)
    ctx = req.get("context", {})
    if ctx.get("dry_run"):
        respond({"status": "success", "summary": "auth adapter structure is valid"})
        return 0
    token_env = ctx.get("token_env", "PROVIDER_TOKEN")
    if os.environ.get(token_env):
        respond({"status": "success", "summary": f"found token env {token_env}"})
        return 0
    respond({
        "status": "blocked",
        "action_required": f"Set {token_env} or configure this auth adapter for your provider",
        "missing_capability": "auth",
    })
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
