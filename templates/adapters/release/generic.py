#!/usr/bin/env python3
"""Generic release adapter template."""

import json
import sys


def main():
    req = json.load(sys.stdin)
    if req.get("context", {}).get("dry_run"):
        print(json.dumps({"status": "success", "summary": "release adapter structure is valid"}, indent=2))
        return 0
    print(json.dumps({
        "status": "blocked",
        "action_required": "Customize this release adapter for your release platform",
        "missing_capability": "release",
    }, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
