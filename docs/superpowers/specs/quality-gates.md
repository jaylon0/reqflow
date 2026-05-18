# Quality Gates

Quality gates apply Superpowers-style discipline inside Requirement Flow.

## Gates

- `design-gate` blocks implementation until high-risk design decisions are approved.
- `tdd-gate` requires a focused failing check when behavior can be tested locally.
- `support-review` and `coding-standards` review implementation against spec and standards.
- `completion-gate` prevents premature completion claims without verification evidence.
- `dynamic-checklist` provides scenario/profile-specific checklist evidence.
- `compliance-report` converts checklist, verification, and review evidence into
  a final status.

## Policy

Quality gates are strict about evidence, but they do not force TDD when no local proving check is practical. In those cases the reason and alternative verification must be recorded.

V1 compliance statuses are `PASS`, `CONDITIONAL PASS`, `FAIL`, and `BLOCKED`.
Low-quality passes must remain visible in the compliance report.
