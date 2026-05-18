# Support Skills

Requirement Flow support skills are auxiliary capabilities. They are explicit-invocation only and do not change the default L0-L3 delivery flow.

| Support skill | Source skill | Category | Status |
|---|---|---|---|
| `support-auth-session` | specialized auth/login skills | legacy-generic | stable |
| `support-local-build` | specialized build skill | legacy-generic | stable |
| `support-pipeline-provider` | specialized pipeline provider skill | legacy-generic | stable |
| `support-pipeline-deploy` | specialized deploy skill | legacy-generic | stable |
| `support-delivery-run` | specialized dev-run orchestrator | legacy-generic | stable |
| `support-hot-reload` | specialized hot reload skill | legacy-generic | stable |
| `support-log-query` | specialized log query skill | legacy-generic | stable |
| `support-database-query` | specialized database query skill | legacy-generic | stable |
| `support-cache-query` | specialized cache query skill | legacy-generic | stable |
| `support-search-query` | specialized search query skill | legacy-generic | stable |
| `support-test-plan` | specialized test plan skill | legacy-generic | stable |
| `support-http-verify` | specialized API verification skill | legacy-generic | stable |
| `support-message-verify` | specialized message verification skill | legacy-generic | stable |
| `support-rpc-verify` | specialized RPC verification skill | legacy-generic | stable |
| `support-task-verify` | specialized task verification skill | legacy-generic | stable |
| `support-ui-verify` | specialized UI verification skill | legacy-generic | stable |
| `support-language-standards` | specialized language standards skill | legacy-generic | stable |
| `support-infra-catalog` | specialized infrastructure catalog skill | legacy-generic | stable |
| `support-domain-rules` | specialized business rules skill | legacy-generic | stable |
| `support-domain-components` | specialized domain component skill | legacy-generic | stable |
| `support-design-an-interface` | `design-an-interface` | `deprecated` | `deprecated` |
| `support-qa` | `qa` | `deprecated` | `deprecated` |
| `support-request-refactor-plan` | `request-refactor-plan` | `deprecated` | `deprecated` |
| `support-ubiquitous-language` | `ubiquitous-language` | `deprecated` | `deprecated` |
| `support-diagnose` | `diagnose` | `engineering` | `stable` |
| `support-grill-with-docs` | `grill-with-docs` | `engineering` | `stable` |
| `support-improve-codebase-architecture` | `improve-codebase-architecture` | `engineering` | `stable` |
| `support-prototype` | `prototype` | `engineering` | `stable` |
| `support-setup-matt-pocock-skills` | `setup-matt-pocock-skills` | `engineering` | `stable` |
| `support-tdd` | `tdd` | `engineering` | `stable` |
| `support-to-issues` | `to-issues` | `engineering` | `stable` |
| `support-to-prd` | `to-prd` | `engineering` | `stable` |
| `support-triage` | `triage` | `engineering` | `stable` |
| `support-zoom-out` | `zoom-out` | `engineering` | `stable` |
| `support-review` | `review` | `in-progress` | `experimental` |
| `support-writing-beats` | `writing-beats` | `in-progress` | `experimental` |
| `support-writing-fragments` | `writing-fragments` | `in-progress` | `experimental` |
| `support-writing-shape` | `writing-shape` | `in-progress` | `experimental` |
| `support-git-guardrails-claude-code` | `git-guardrails-claude-code` | `misc` | `stable` |
| `support-migrate-to-shoehorn` | `migrate-to-shoehorn` | `misc` | `stable` |
| `support-scaffold-exercises` | `scaffold-exercises` | `misc` | `stable` |
| `support-setup-pre-commit` | `setup-pre-commit` | `misc` | `stable` |
| `support-edit-article` | `edit-article` | `personal` | `stable` |
| `support-obsidian-vault` | `obsidian-vault` | `personal` | `stable` |
| `support-caveman` | `caveman` | `productivity` | `stable` |
| `support-grill-me` | `grill-me` | `productivity` | `stable` |
| `support-handoff` | `handoff` | `productivity` | `stable` |
| `support-write-a-skill` | `write-a-skill` | `productivity` | `stable` |

Use the aggregate entry when the exact support skill is unclear:

```text
使用 requirement-flow-plugin:support-router 选择一个辅助能力
```

Use a direct entry when the capability is known:

```text
使用 requirement-flow-plugin:support-diagnose 诊断这个失败
```

See [legacy-skill-mapping.md](legacy-skill-mapping.md) for how specialized plugin capabilities map to generic support skills.
