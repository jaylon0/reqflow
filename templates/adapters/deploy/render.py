#!/usr/bin/env python3
"""Render deploy adapter skeleton.

Render commonly uses Git-triggered deploys or API-triggered deploy hooks.
Configure context.deploy_hook_url outside source control when using hooks.
"""

import json
import os
import urllib.request
import sys


def respond(payload):
    print(json.dumps(payload, indent=2))


def main():
    req = json.load(sys.stdin)
    action = req.get("action", "check")
    ctx = req.get("context", {})
    if ctx.get("dry_run"):
        respond({"status": "success", "summary": "render adapter structure is valid"})
        return 0
    hook = ctx.get("deploy_hook_url") or os.environ.get("RENDER_DEPLOY_HOOK_URL")
    if not hook:
        respond({"status": "blocked", "action_required": "Set RENDER_DEPLOY_HOOK_URL or context.deploy_hook_url"})
        return 2
    if action == "check":
        respond({"status": "success", "summary": "render deploy hook configured"})
        return 0
    if action == "deploy":
        with urllib.request.urlopen(hook, timeout=20) as response:
            body = response.read().decode("utf-8", errors="replace")
        respond({"status": "success", "artifacts": {"response": body[:1000]}})
        return 0
    respond({"status": "skipped", "summary": f"unsupported render action {action}"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
