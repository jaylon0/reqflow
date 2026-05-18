#!/usr/bin/env python3
"""Validate Requirement Flow plugin structure and optional installed copies."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


STATE_KEYS = [
    "planned_modules",
    "authorized_scope",
    "max_retries",
    "failure_fingerprints",
    "current_loop_id",
    "pending_confirmations",
    "last_stable_step",
    "last_stable_artifact",
]

LOOP_PHRASES = [
    "Previous attempts for fingerprint",
    "Authorized files",
    "Scope changed",
    "Files changed",
    "Verification result",
    "Human decision required",
]

DOC_REQUIREMENTS = {
    "skills/main-flow/SKILL.md": [
        "{pluginRoot}/templates/run-state.example.json",
        "{pluginRoot}/templates/run-artifacts/",
        "Do not look for shared templates under `{baseDir}/templates`",
    ],
    "skills/loop-engine/SKILL.md": [
        "{pluginRoot}/templates/loop-record.template.md",
        "Do not look for shared templates under `{baseDir}/templates`",
    ],
    "skills/adapter-factory/SKILL.md": [
        "{pluginRoot}/templates/adapters/<capability>/<platform>.py",
        "{pluginRoot}/templates/adapters/<capability>/generic.py",
        "{pluginRoot}/scripts/provider_adapter_stub.py",
    ],
}


def load_json(path: Path, errors: list[str]) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        errors.append(f"invalid json {path}: {exc}")
        return {}


def validate_root(root: Path) -> dict:
    errors: list[str] = []
    if not root.exists():
        return {"root": str(root), "status": "missing", "errors": [f"missing root {root}"]}

    for rel in [
        ".codex-plugin/plugin.json",
        ".claude-plugin/plugin.json",
        ".cursor-plugin/plugin.json",
        "templates/run-state.example.json",
    ]:
        load_json(root / rel, errors)

    skills = sorted(root.glob("skills/*/SKILL.md"))
    commands = sorted(root.glob("commands/*.md"))
    skill_names = {path.parent.name for path in skills}

    for skill in skills:
        text = skill.read_text()
        if not text.startswith("---") or "\n---" not in text[3:]:
            errors.append(f"missing frontmatter {skill}")
            continue
        frontmatter = text[3 : text.find("\n---", 3)]
        if "name:" not in frontmatter or "description:" not in frontmatter:
            errors.append(f"missing name or description {skill}")

    for command in commands:
        for name in re.findall(r"requirement-flow-plugin:([a-z0-9-]+)", command.read_text()):
            if name not in skill_names:
                errors.append(f"command {command.name} references missing skill {name}")

    state = load_json(root / "templates/run-state.example.json", errors)
    for key in STATE_KEYS:
        if key not in state:
            errors.append(f"missing state key {key}")
    if state.get("max_retries") != 3:
        errors.append("max_retries default must be 3")

    loop_template = root / "templates/loop-record.template.md"
    loop_text = loop_template.read_text() if loop_template.exists() else ""
    for phrase in LOOP_PHRASES:
        if phrase not in loop_text:
            errors.append(f"missing loop template phrase {phrase}")

    for rel, phrases in DOC_REQUIREMENTS.items():
        path = root / rel
        text = path.read_text() if path.exists() else ""
        for phrase in phrases:
            if phrase not in text:
                errors.append(f"missing path guidance {rel}: {phrase}")

    return {
        "root": str(root),
        "status": "success" if not errors else "failed",
        "skills": len(skills),
        "commands": len(commands),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--install-root", action="append", default=[])
    args = parser.parse_args()

    roots = [Path(args.root).resolve()]
    roots.extend(Path(path).resolve() for path in args.install_root)
    results = [validate_root(root) for root in roots]
    status = "success" if all(item["status"] == "success" for item in results) else "failed"
    print(json.dumps({"status": status, "results": results}, indent=2))
    return 0 if status == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
