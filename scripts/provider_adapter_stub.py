#!/usr/bin/env python3
"""Reference custom provider adapter.

Reads JSON from stdin and returns a blocked result. Copy this file and
replace the action handlers for a real provider.
"""

from __future__ import annotations

import json
import sys


def main() -> int:
    try:
        request = json.load(sys.stdin)
    except Exception as exc:
        print(json.dumps({
            "status": "failed",
            "errors": [{"message": f"Invalid JSON input: {exc}"}],
        }, indent=2))
        return 1

    action = request.get("action", "unknown")
    print(json.dumps({
        "status": "blocked",
        "action_required": (
            f"No provider implementation is configured for action '{action}'. "
            "Copy provider_adapter_stub.py and implement this action."
        ),
        "missing_capability": action,
    }, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
