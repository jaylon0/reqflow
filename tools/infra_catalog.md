---
name: infra-components
description: >
  Infrastructure component catalog for storage, cache, messaging, RPC,
  configuration, rate limiting, logging, and observability. Use when a
  requirement touches infrastructure choices or implementation patterns.
---

# infra-components

Map infrastructure needs to the relevant project reference.

## Mandatory Rules

- Read only the relevant reference files.
- If no matching reference exists, inspect the codebase for existing patterns before creating a new one.
- Do not hardcode platform names, credentials, or environment-specific endpoints.

## Reference Index

| Scenario | Read |
|---|---|
| Storage, database, migrations, query behavior | `references/storage.md` |
| Cache, TTL, invalidation, consistency | `references/cache.md` |
| Messages, events, jobs, async processing | `references/messaging.md` |
| HTTP/RPC/service-to-service calls | `references/service-calls.md` |
| Configuration, feature flags, rollout controls | `references/configuration.md` |

## Output

```text
INFRA_REFERENCE_STATUS: matched|not_configured
REFERENCES_READ:
- <file>
IMPLEMENTATION_NOTES:
- <note>
```
