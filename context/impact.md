---
name: java-impact-analysis
description: >
  Combines Java code graph and semantic retrieval evidence into affected scope,
  risk signals, missing context, and required follow-up confirmations. Use after
  Java graph and Java semantic retrieval discovery or when a Java backend change
  needs impact analysis.
---

# java-impact-analysis

Combined Java impact analysis.

This is an internal workflow contract skill, not a support-* capability wrapper.
When local V1 graph and semantic artifacts are available, use
`graph/java-impact-analysis.response.json` from `scripts/java_context_engine.py`
as the first impact-analysis evidence source.

## Mandatory Rules

- Require evidence references for every affected file, module, or symbol.
- Keep impact analysis provider-neutral; do not assume a specific graph or vector backend.
- Do not start graph databases, vector databases, or any external service from this skill.
- Do not edit source code from this skill.
- Flag synchronized query risks such as list/count drift, DTO/VO mapping drift, cache invalidation, async side effects, and contract ownership.
- Do not authorize code edits; write candidate scope for `main-flow` to confirm.
- Missing graph or RAG data must be visible in output.
- Local V1 impact is a merge of heuristic source graph and lexical semantic evidence; do not present it as production-grade dependency analysis.

## Output

```text
JAVA_IMPACT_ANALYSIS_STATUS: ready|blocked|manual|failed
ENTRYPOINT_CONFIDENCE: high|medium|low|unknown
CANDIDATE_SCOPE:
- <file, module, or symbol>
RISK_SIGNALS:
- <risk>
REQUIRED_FOLLOWUPS:
- <question or decision>
EVIDENCE_REFS:
- <artifact ref>
```
