---
name: tdd-gate
description: >
  Decides whether behavior-changing work should use a red-green-refactor loop.
  Use before module implementation when local tests, API checks, integration
  checks, or focused reproduction are practical.
---

# tdd-gate

TDD applicability gate.

This gate decides and records test-first expectations. It does not replace the actual test or verification skills.

## Mandatory Rules

- Require a failing check first when behavior can be expressed locally.
- If TDD is not practical, record the reason and the alternative verification.
- Keep the proving check focused on the requirement.
- Do not create broad test suites unrelated to the change.
- Do not mark TDD as not practical only to avoid writing a reasonable focused check.

## Output

```text
TDD_GATE_STATUS: required|not_practical|blocked
FAILING_CHECK:
- <command or case>
ALTERNATIVE_VERIFICATION:
- <verification or empty>
REASON:
- <reason when not practical>
```
