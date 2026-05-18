#!/usr/bin/env python3
"""Scan a project and print Requirement Flow context as JSON."""

from __future__ import annotations

import json
import os
from pathlib import Path


def has(path: Path, name: str) -> bool:
    return (path / name).exists()


def read_package_json(root: Path) -> dict:
    package_file = root / "package.json"
    if not package_file.exists():
        return {}
    try:
        return json.loads(package_file.read_text())
    except Exception:
        return {}


def detect_project(root: Path) -> dict:
    package_json = read_package_json(root)
    scripts = package_json.get("scripts", {}) if isinstance(package_json, dict) else {}

    languages = []
    frameworks = []
    package_manager = ""
    commands = {"build": [], "test": [], "lint": [], "typecheck": []}

    if package_json:
        languages.append("javascript")
        if has(root, "tsconfig.json"):
            languages.append("typescript")
        if has(root, "pnpm-lock.yaml"):
            package_manager = "pnpm"
        elif has(root, "yarn.lock"):
            package_manager = "yarn"
        else:
            package_manager = "npm"
        for name in commands:
            if name in scripts:
                commands[name].append(f"{package_manager} run {name}")
        deps = {}
        deps.update(package_json.get("dependencies", {}) or {})
        deps.update(package_json.get("devDependencies", {}) or {})
        for framework in ["next", "react", "vue", "svelte", "vite", "express", "nestjs"]:
            if framework in deps or f"@{framework}/core" in deps:
                frameworks.append(framework)

    if has(root, "pom.xml"):
        languages.append("java")
        frameworks.append("maven")
        commands["build"].append("mvn package")
        commands["test"].append("mvn test")

    if has(root, "build.gradle") or has(root, "build.gradle.kts"):
        languages.append("java")
        frameworks.append("gradle")
        commands["build"].append("./gradlew build")
        commands["test"].append("./gradlew test")

    if has(root, "pyproject.toml") or has(root, "requirements.txt"):
        languages.append("python")
        if has(root, "pyproject.toml"):
            commands["test"].append("pytest")

    if has(root, "go.mod"):
        languages.append("go")
        commands["test"].append("go test ./...")

    if has(root, "Makefile"):
        frameworks.append("make")
        commands["build"].append("make build")
        commands["test"].append("make test")

    providers = []
    if has(root, ".github"):
        providers.append("github")
    for name, provider in [
        ("vercel.json", "vercel"),
        ("netlify.toml", "netlify"),
        ("render.yaml", "render"),
        ("fly.toml", "fly"),
        ("Dockerfile", "docker"),
    ]:
        if has(root, name):
            providers.append(provider)

    source_roots = [p for p in ["src", "app", "lib", "server", "packages"] if has(root, p)]
    test_roots = [p for p in ["test", "tests", "__tests__", "spec"] if has(root, p)]

    project_type = "backend-service"
    if any(f in frameworks for f in ["next", "react", "vue", "svelte", "vite"]):
        project_type = "frontend-app"
    if any(f in frameworks for f in ["express", "nestjs"]) and project_type == "frontend-app":
        project_type = "fullstack-app"

    return {
        "project": {
            "name": root.name,
            "type": project_type,
            "languages": sorted(set(languages)),
            "frameworks": sorted(set(frameworks)),
            "package_manager": package_manager,
            "source_roots": source_roots,
            "test_roots": test_roots,
        },
        "commands": commands,
        "providers_detected": sorted(set(providers)),
        "files_detected": sorted(
            name
            for name in [
                "README.md",
                "package.json",
                "pom.xml",
                "build.gradle",
                "pyproject.toml",
                "go.mod",
                "Makefile",
                "Dockerfile",
            ]
            if has(root, name)
        ),
    }


def main() -> int:
    root = Path(os.environ.get("PROJECT_DIR", ".")).resolve()
    print(json.dumps(detect_project(root), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
