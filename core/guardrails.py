"""Guardrails - parallel constraint validation with fail-fast."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Awaitable


class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


@dataclass
class Violation:
    constraint_name: str
    severity: Severity
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class Constraint:
    name: str
    description: str
    severity: Severity = Severity.ERROR
    check_fn: Callable[[dict[str, Any]], Awaitable[Violation | None]] | None = None


class Guardrails:
    """Parallel constraint validation engine."""

    def __init__(self, constraints: list[Constraint] | None = None):
        self.constraints = constraints or []

    def add_constraint(self, constraint: Constraint):
        """Add a constraint to the guardrails."""
        self.constraints.append(constraint)

    async def check(self, context: dict[str, Any]) -> list[Violation]:
        """Run all constraints in parallel and return violations."""
        if not self.constraints:
            return []

        tasks = []
        for constraint in self.constraints:
            if constraint.check_fn is not None:
                tasks.append(self._run_constraint(constraint, context))

        if not tasks:
            return []

        results = await asyncio.gather(*tasks, return_exceptions=True)

        violations = []
        for result in results:
            if isinstance(result, Exception):
                violations.append(Violation(
                    constraint_name="unknown",
                    severity=Severity.ERROR,
                    message=f"Constraint check failed with exception: {result}",
                ))
            elif result is not None:
                violations.append(result)

        return violations

    async def _run_constraint(self, constraint: Constraint, context: dict[str, Any]) -> Violation | None:
        """Run a single constraint check."""
        try:
            if constraint.check_fn is None:
                return None
            return await constraint.check_fn(context)
        except Exception as e:
            return Violation(
                constraint_name=constraint.name,
                severity=Severity.ERROR,
                message=f"Constraint check raised exception: {e}",
            )

    def is_fatal(self, violations: list[Violation]) -> bool:
        """Check if any violation is fatal."""
        return any(v.severity == Severity.FATAL for v in violations)

    def has_errors(self, violations: list[Violation]) -> bool:
        """Check if any violation is error or fatal level."""
        return any(v.severity in (Severity.ERROR, Severity.FATAL) for v in violations)

    def filter_by_severity(self, violations: list[Violation], min_severity: Severity) -> list[Violation]:
        """Filter violations by minimum severity."""
        severity_order = {
            Severity.INFO: 0,
            Severity.WARNING: 1,
            Severity.ERROR: 2,
            Severity.FATAL: 3,
        }
        min_level = severity_order[min_severity]
        return [v for v in violations if severity_order[v.severity] >= min_level]

    def format_violations(self, violations: list[Violation]) -> str:
        """Format violations as a readable report."""
        if not violations:
            return "No violations found."

        lines = ["# Guardrail Violations\n"]
        for v in violations:
            icon = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "fatal": "🚫"}[v.severity.value]
            lines.append(f"{icon} **[{v.severity.value.upper()}]** {v.constraint_name}")
            lines.append(f"   {v.message}")
            if v.details:
                for key, val in v.details.items():
                    lines.append(f"   - {key}: {val}")
            lines.append("")

        return "\n".join(lines)


# Built-in constraint checkers

async def check_file_boundary(context: dict[str, Any]) -> Violation | None:
    """Check if file edits are within authorized scope."""
    file_path = context.get("file_path", "")
    authorized_scope = context.get("authorized_scope", [])
    denied_scope = context.get("denied_scope", [])

    if not file_path:
        return None

    import fnmatch
    for pattern in denied_scope:
        if fnmatch.fnmatch(file_path, pattern):
            return Violation(
                constraint_name="file_boundary",
                severity=Severity.FATAL,
                message=f"File '{file_path}' is in denied scope",
                details={"file": file_path, "pattern": pattern},
            )

    if authorized_scope:
        in_scope = any(fnmatch.fnmatch(file_path, p) for p in authorized_scope)
        if not in_scope:
            return Violation(
                constraint_name="file_boundary",
                severity=Severity.ERROR,
                message=f"File '{file_path}' is not in authorized scope",
                details={"file": file_path, "authorized_scope": authorized_scope},
            )

    return None


async def check_constitution(context: dict[str, Any]) -> Violation | None:
    """Check project-level non-negotiable rules."""
    rules = context.get("constitution_rules", [])
    action = context.get("action", "")

    for rule in rules:
        if rule.get("condition") and rule["condition"] in action:
            return Violation(
                constraint_name="constitution",
                severity=Severity.FATAL,
                message=f"Constitutional rule violated: {rule.get('message', rule['condition'])}",
                details={"rule": rule},
            )

    return None
