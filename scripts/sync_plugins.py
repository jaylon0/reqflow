#!/usr/bin/env python3
"""Sync reqflow code to all plugin caches."""

import subprocess
import sys
from pathlib import Path

CACHE_PATHS = [
    Path.home() / ".claude/plugins/cache/local/reqflow/latest",
    Path.home() / ".claude/plugins/marketplaces/local/plugins/reqflow",
    Path.home() / ".codex/plugins/cache/local/reqflow/latest",
    Path.home() / ".codex/plugins/marketplaces/local/plugins/reqflow",
]

SRC = Path("core").parent  # project root
SYNC_DIRS = ["core", "runner", "skills", "workflows", "config"]

# Plugin metadata files to copy directly
PLUGIN_FILES = [
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
]


def sync():
    synced = 0
    for cache in CACHE_PATHS:
        if not cache.exists():
            print(f"⚠️  skip (not found): {cache}")
            continue
        for subdir in SYNC_DIRS:
            src = SRC / subdir
            if not src.exists():
                continue
            dst = cache / "python" / "reqflow" / subdir if subdir in ("core", "runner") else cache / subdir
            dst.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["rsync", "-a", "--delete", "--exclude=__pycache__", "--exclude=*.egg-info", "--exclude=.venv", f"{src}/", f"{dst}/"],
                check=True,
            )
        # Sync plugin metadata files
        for pf in PLUGIN_FILES:
            src_file = SRC / pf
            dst_file = cache / pf
            if src_file.exists() and dst_file.parent.exists():
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(["cp", str(src_file), str(dst_file)], check=True)
        synced += 1
        print(f"✅ synced: {cache}")

    print(f"\nDone: {synced}/{len(CACHE_PATHS)} caches synced")


if __name__ == "__main__":
    sync()
