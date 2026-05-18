#!/usr/bin/env python3
"""Test adapter that echoes input as success output. Used for testing dispatch."""

from __future__ import annotations

import json
import sys


def main() -> int:
    try:
        request = json.load(sys.stdin)
    except Exception as exc:
        print(json.dumps({
            "status": "failed",
            "artifacts": [],
            "errors": [f"Invalid JSON input: {exc}"],
        }))
        return 1

    action = request.get("action", "unknown")
    capability = request.get("capability", "unknown")
    print(json.dumps({
        "status": "success",
        "artifacts": [f"echo/{capability}/{action}"],
        "errors": [],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
