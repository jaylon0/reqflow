---
name: compliance-report
description: >
  Produces the V1 workflow compliance report from work-item checklists,
  verification evidence, review reports, guideline profile, risk signals, and
  low-quality pass decisions.
---

# compliance-report

Compliance reporting turns V1 artifacts into a completion gate. It is evidence,
not a success claim.

## Mandatory Rules

- Do not report `PASS` without fresh verification evidence or explicit manual
  checklist evidence.
- Include guideline adherence, rule coverage, checklist completion, quality
  grade, and risk level.
- Mark missing mandatory checklist items as `FAIL`.
- Mark low-quality pass work items as at least `CONDITIONAL PASS`.
- Link report findings to work-item report paths, not copied long logs.
- Feed unresolved failures to `loop-engine`.

## Status Values

```text
PASS | CONDITIONAL PASS | FAIL | BLOCKED
```

## Outputs

```text
COMPLIANCE_REPORT_STATUS: pass|conditional-pass|fail|blocked
QUALITY_GRADE: A|B|C|D|F
RISK_LEVEL: low|medium|high
ARTIFACTS:
- agent/compliance-report.md
BLOCKERS:
- <blocker or empty>
```
