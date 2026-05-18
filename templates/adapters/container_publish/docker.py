#!/usr/bin/env python3
"""Docker build and push adapter template."""

import json
import subprocess
import sys


def run(args, cwd=None):
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def respond(payload):
    print(json.dumps(payload, indent=2))


def main():
    req = json.load(sys.stdin)
    action = req.get("action", "check")
    project_dir = req.get("project_dir", ".")
    ctx = req.get("context", {})
    if ctx.get("dry_run"):
        respond({"status": "success", "summary": "docker adapter structure is valid"})
        return 0
    docker = run(["docker", "version", "--format", "{{.Client.Version}}"])
    if docker.returncode != 0:
        respond({"status": "blocked", "action_required": "Install Docker and ensure the daemon is running"})
        return 2
    image = ctx.get("image")
    if action == "check":
        respond({"status": "success", "artifacts": {"docker_client": docker.stdout.strip()}})
        return 0
    if not image:
        respond({"status": "blocked", "action_required": "Provide context.image, for example registry.example.com/app:tag"})
        return 2
    if action == "build":
        proc = run(["docker", "build", "-t", image, "."], cwd=project_dir)
    elif action in {"push", "container_publish"}:
        proc = run(["docker", "push", image], cwd=project_dir)
    else:
        respond({"status": "skipped", "summary": f"unsupported docker action {action}"})
        return 0
    if proc.returncode == 0:
        respond({"status": "success", "artifacts": {"image": image, "output": proc.stdout[-1000:]}})
        return 0
    respond({"status": "failed", "errors": [{"stage": action, "message": proc.stderr or proc.stdout}]})
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
