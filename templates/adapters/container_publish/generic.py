#!/usr/bin/env python3
"""Generic container publish adapter template."""

import json
import sys


def main():
    req = json.load(sys.stdin)
    if req.get("context", {}).get("dry_run"):
        print(json.dumps({"status": "success", "summary": "container adapter structure is valid"}, indent=2))
        return 0
    print(json.dumps({
        "status": "blocked",
        "action_required": "Customize this adapter with build and push commands for your registry",
        "missing_capability": "container_publish",
    }, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
