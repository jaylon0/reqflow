#!/usr/bin/env python3
"""Manual checklist adapter template."""

import json
import sys


def main():
    req = json.load(sys.stdin)
    ctx = req.get("context", {})
    checklist = ctx.get("checklist") or [
        "Run the required platform action manually.",
        "Confirm the result and provide any artifact URL.",
        "Report failures back to Requirement Flow.",
    ]
    if ctx.get("dry_run"):
        print(json.dumps({"status": "success", "summary": "manual adapter structure is valid"}, indent=2))
        return 0
    print(json.dumps({
        "status": "blocked",
        "action_required": "Manual provider confirmation required",
        "manual_checklist": checklist,
    }, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
