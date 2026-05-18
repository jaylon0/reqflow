---
name: quality-gates
description: >
  Coordinates design approval, pre-coding checks, TDD applicability, review
  readiness, and completion verification gates. Use when main-flow reaches
  design approval, Java or backend module coding, review, or completion.
---

# quality-gates

Quality gate router.

This is an internal workflow gate skill, not a replacement for `support-review`, `coding-standards`, or provider verification skills.

## Mandatory Rules

- Do not allow coding before required design approval.
- Do not allow coding before pre-coding checks pass.
- Use `tdd-gate` before behavior-changing implementation.
- Use existing `support-review` and `coding-standards` during review.
- Use `completion-gate` before reporting completion.
- Do not claim a gate passed without recorded evidence or a manual checklist result.

## Pre-Coding Checks

After design-gate passes, before any coding begins, verify these 5 checks:

### Check 1: Version Constraints (HIGH blocker)

- [ ] Project Java/framework version documented
- [ ] All dependencies listed (pom.xml / build.gradle / package.json)
- [ ] Third-party library minimum versions documented
- [ ] Known incompatibilities documented

**Action if failed:** STOP — do not proceed until versions are documented.

### Check 2: Code Reuse (HIGH blocker)

- [ ] Similar functionality exists in codebase? (search call paths, existing services)
- [ ] Reuse decision documented (reuse existing / build new with reason)
- [ ] Module dependencies documented

**Action if failed:** STOP — evaluate reuse opportunities before starting.

### Check 3: Security CVE Scan (CRITICAL blocker)

- [ ] Dependencies scanned for known CVEs
- [ ] No critical/high CVEs blocking deployment
- [ ] No hardcoded secrets (passwords, API keys, tokens)

**Action if failed:** BLOCK — cannot proceed with critical/high CVEs.

### Check 4: Special Scene Recognition (HIGH blocker)

- [ ] Financial/payment feature? → Apply BigDecimal, audit trail rules
- [ ] Security/auth feature? → Apply rate limiting, input validation rules
- [ ] High-concurrency (>1000 QPS)? → Apply caching, connection pooling rules
- [ ] Applicable special rules identified and documented

**Action if failed:** REVIEW — ensure special scene rules are followed.

### Check 5: Testing Planning (HIGH blocker)

- [ ] Test cases planned before coding (TDD: write tests first)
- [ ] Coverage target >= 80%
- [ ] Happy path and exception paths covered
- [ ] Integration tests planned for external calls

**Action if failed:** WARNING — code review will reject insufficient tests.

Reference: `templates/coding-standards-template.md` for detailed standards.

## Flow

1. Use `design-gate` for design-sensitive work.
2. Run **pre-coding checks** (above) — all must pass before coding.
3. Use `tdd-gate` before module implementation.
4. Use `support-review` and `coding-standards` for review.
5. Use `completion-gate` before final status.

## Output

```text
QUALITY_GATES_STATUS: pass|blocked|failed
GATES:
- design-gate: pass|skip
- pre-coding-checks: pass|blocked
  - version-constraints: pass|fail
  - code-reuse: pass|fail
  - cve-scan: pass|fail
  - special-scenes: pass|fail|na
  - test-planning: pass|fail
- tdd-gate: pass|skip
- review: pass|failed
- completion-gate: pass|blocked
BLOCKERS:
- <blocker or empty>
```
