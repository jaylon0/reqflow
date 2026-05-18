# Requirement Flow Capability Evaluation

This is development-only material for auditing Requirement Flow while the plugin
is being built. It is not a plugin skill and should not be installed into Codex,
CodeFlicker, or Claude as user-facing plugin functionality.

## Purpose

Use this checklist to evaluate whether ideas from KStack, Superpowers, Ralph,
project-context-extractor/PCE, gstack, or project-local conventions are covered
by concrete Requirement Flow plugin artifacts.

## Review Rules

- Evaluate against artifacts, skills, templates, docs, or provider results. Do
  not mark a capability integrated from naming similarity alone.
- Distinguish `integrated`, `partial`, `deferred`, `missing`, and
  `not-applicable`.
- Distinguish V1 contracts from executable implementations. A contract is not
  proof that a backend, index, agent loop, or provider is already implemented.
- Every `partial`, `deferred`, or `missing` capability needs a concrete gap and
  next action.
- Keep source families separate before summarizing: KStack PDFs, Superpowers,
  Ralph, PCE/project-context-extractor, gstack, and project-local additions.
- Do not update plugin skills, templates, specs, or persistent memory directly
  from this evaluation. Convert approved gaps into normal implementation tasks.

## Coverage Buckets

- Code graph and dynamic context evidence.
- Semantic indexing and requirement-to-spec traceability.
- PRD clarification, issue decomposition, and work-item shaping.
- Main workflow orchestration, checkpoints, resumable state, and repair loops.
- Superpowers-style design, TDD, review, and verification discipline.
- Dual memory: global preferences plus project-local lessons.
- Continuous evolution: proposal, review, and approved application path.
- Coding standards, domain rules, and reusable component guidance.
- Multi-agent coordination contract and handoff/report boundaries.
- Delivery verification for build, API, UI, RPC, message, task, data, cache,
  search, logs, deployment, and release.

## Evaluation Template

| Source | Capability | Status | Evidence Artifact | Gap | Next Action |
|---|---|---|---|---|---|
| KStack | Code graph and dynamic context evidence |  |  |  |  |
| KStack | Semantic indexing and requirement-to-spec traceability |  |  |  |  |
| KStack | Workflow orchestration, checkpointing, state recovery |  |  |  |  |
| KStack | Delivery verification and auto-repair |  |  |  |  |
| Superpowers | Brainstorming, design, TDD, review, and verification discipline |  |  |  |  |
| Ralph | PRD clarification, issue shaping, task decomposition |  |  |  |  |
| PCE | Scenario detection, guideline profile, dynamic checklist |  |  |  |  |
| PCE | Dual memory and continuous evolution proposal path |  |  |  |  |
| gstack | Browser/tool execution, handoff, learning, skill evolution signals |  |  |  |  |
| Project local | Coding standards, domain rules, reusable components |  |  |  |  |
