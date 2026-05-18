#!/usr/bin/env python3
"""Test adapter that sleeps forever. Used for timeout testing."""

from __future__ import annotations

import time

def main() -> int:
    time.sleep(999)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
