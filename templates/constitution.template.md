# Constitution

## Non-negotiable Rules

- Do not introduce write operations in verification adapters.
- Java backend changes must preserve controller, service, repository, and data transfer boundaries unless the technical plan explicitly approves a boundary change.
- External calls must define timeout, fallback, and observability behavior.
- API, message, RPC, database, cache, and search contract changes require explicit approval before coding.

## Project Rules

- Prefer existing project patterns and local examples over generic defaults.
- Treat missing product, data, or provider decisions as BLOCKER.
- Keep runtime secrets outside project files.
