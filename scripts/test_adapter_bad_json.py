#!/usr/bin/env python3
"""Test adapter that outputs invalid JSON. Used for error handling testing."""

from __future__ import annotations

def main() -> int:
    print("this is not json")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
