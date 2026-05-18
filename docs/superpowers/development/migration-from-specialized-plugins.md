# Migration From Specialized Plugins

This document describes how specialized workflow plugins map to Requirement Flow.

## Mapping

| Specialized concept | Requirement Flow concept |
|---|---|
| End-to-end development runner | `workflow-run` |
| Build/deploy/verify agents | `build-agent`, `deploy-agent`, `verify-agent` |
| Platform-specific deployment APIs | Provider adapters |
| Structured test plan | Acceptance plan |
| Coding standards skill | `coding-standards` |
| Infrastructure component references | `infra-components` |
| Business component reuse skill | `domain-components` |
| Internal auth scripts | Provider auth checks |
| Internal log/database/message/RPC tools | Custom providers |
| Code graph / system dependency map | `java-code-graph` provider contract |
| Semantic code retrieval / RAG | `java-semantic-index` provider contract |
| PRD-to-spec workflow | `spec-governance` and `spec-delta` |
| Project constitution / hard rules | `constitution-check` |
| Superpowers design/TDD/completion discipline | `quality-gates`, `design-gate`, `tdd-gate`, `completion-gate` |

## What To Keep

- Clear orchestration boundaries.
- Agent isolation for noisy or long-running work.
- Structured status output.
- Failure repair loops with loop detection.
- Reference catalogs that are read only when relevant.
- Project context caching.

## What To Remove

- Company-specific platform names.
- Internal domains and URLs.
- Internal account, SSO, or credential assumptions.
- Business-specific component names.
- Environment-specific default data.
- Any secrets or personal author metadata.

## Migration Steps

1. Create project context from `templates/context.template.yaml`.
2. Create provider configuration from `templates/providers.template.yaml`.
3. Move coding rules into `coding-standards/references/`.
4. Move infrastructure usage rules into `infra-components/references/`.
5. Convert reusable business patterns into `domain-components/references/`.
6. Implement custom provider adapters only for platforms needed by the project.
7. Validate with L0, L1, L2, and L3 example requirements.
