import asyncio
from reqflow.core.guardrails import Guardrails, Constraint, Severity, check_file_boundary

def test_guardrails_no_constraints():
    g = Guardrails()
    violations = asyncio.run(g.check({"file_path": "/any/file.java"}))
    assert violations == []

def test_guardrails_file_boundary_allowed():
    g = Guardrails()
    g.add_constraint(Constraint(
        name="file_boundary",
        description="scope check",
        severity=Severity.FATAL,
        check_fn=check_file_boundary,
    ))
    violations = asyncio.run(g.check({
        "file_path": "/project/common/src/Main.java",
        "authorized_scope": ["/project/common/*"],
    }))
    fatal = [v for v in violations if v.severity == Severity.FATAL]
    assert len(fatal) == 0

def test_guardrails_file_boundary_denied():
    g = Guardrails()
    g.add_constraint(Constraint(
        name="file_boundary",
        description="scope check",
        severity=Severity.ERROR,
        check_fn=check_file_boundary,
    ))
    violations = asyncio.run(g.check({
        "file_path": "/project/web/src/Controller.java",
        "authorized_scope": ["/project/common/*"],
    }))
    errors = [v for v in violations if v.severity in (Severity.ERROR, Severity.FATAL)]
    assert len(errors) > 0

def test_is_fatal():
    g = Guardrails()
    assert g.is_fatal([]) is False
