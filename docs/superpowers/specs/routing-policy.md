# Routing Policy

Requirement Flow classifies work into four levels.

## L0 Analyze Only

Use when the user asks for analysis, impact assessment, explanation, or explicitly forbids edits.

## L1 Light Change

Use for local low-risk edits with small blast radius.

Examples:

- text changes
- simple bug fixes
- test fixes
- missing imports
- local configuration tweaks

## L2 Planned Change

Use for design-sensitive or multi-file work that can be verified locally.

The agent should present an implementation and acceptance plan before editing.

## L3 Delivery Loop

Use for externally observable changes:

- API behavior or contract
- database or persistence behavior
- messages, jobs, events
- service-to-service calls
- authentication or authorization
- deployment, release, package publishing
- user-visible production behavior

If automated providers are missing, use manual provider mode.
