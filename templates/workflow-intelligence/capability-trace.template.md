# Capability Trace Matrix

Use this matrix to prevent capability loss while integrating external workflow
ideas into Requirement Flow.

| Capability | Source | Problem Solved | V1/V2/V3/Deferred | Plugin Artifact | Acceptance Evidence |
|---|---|---|---|---|---|
| Requirement clarification and design-first planning | Superpowers, Ralph PRD | Turn natural-language requirements into durable intent | V1 | 01_prd_summary.md, 02_spec_delta.md | PRD summary and spec delta exist |
| Scenario detection | PCE | Route Java backend work to the right checklist and profile | V1 | agent/scenario.json | Scenario has confidence and alternatives |
| Dynamic checklist | PCE, Superpowers verification | Convert scenario and profile into verifiable checks | V1 | agent/checklists/<id>.json | Mandatory checklist exists per work item |
| Guideline profile | PCE, coding standards | Bind rule strength to task type | V1 | agent/profile.json | Profile, severity, and source recorded |
| Java context pack | KStack, PCE, java-context-engine | Give agents focused code and architecture context | V1 | agent/context-packs/<id>.md | Context pack exists per work item |
| Work item state | Ralph, main-flow state | Keep task progress resumable | V1 | agent/work_items.json | Work item states are valid |
| Multi-agent execution contract | prompt, Superpowers SDD | Separate coordinator, dev, verify, review responsibilities | V1 contract, V2 execution | agents/java-module-*.md | Agent templates exist |
| Loop repair | loop-engine, systematic debugging, prompt resume | Bound fix/verify cycles | V1 contract | loops/<id>.md, state.json | Fingerprints and repair rounds recorded |
| Dual memory | PCE, gstack/gbrain | Preserve global preferences and project-local lessons | V1 contract, V3 backend | memory.md, agent/lessons-learned.md | Memory contract paths recorded |
| Evolution proposal | PCE evolve, gstack learn/skillify | Improve future runs without unsafe auto-patching | V1 proposal, V3 write | agent/evolution-report.md | Proposals cite source artifacts |
| Compliance report | PCE, quality-gates | Produce evidence-based completion status | V1 | agent/compliance-report.md | Grade, risk, coverage recorded |
