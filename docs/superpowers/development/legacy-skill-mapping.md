# Legacy Skill Mapping

This file maps specialized workflow skills from the original plugin stack to provider-neutral Requirement Flow support capabilities.

The generic support skill names intentionally avoid company, platform, domain, and internal tool names. Concrete integrations belong in project context or provider adapters.

| Specialized capability | Generic Requirement Flow capability |
|---|---|
| internal auth or app login session | `support-auth-session` |
| local Maven, Make, or project build | `support-local-build` |
| pipeline metadata and trigger API | `support-pipeline-provider` |
| pipeline or staging deployment | `support-pipeline-deploy` |
| end-to-end build, deploy, verify runner | `support-delivery-run` or `main-flow` |
| hot reload or live patch tooling | `support-hot-reload` |
| log tailing and error search | `support-log-query` |
| read-only database validation | `support-database-query` |
| read-only cache validation | `support-cache-query` |
| read-only search index validation | `support-search-query` |
| structured test plan generation | `support-test-plan` |
| HTTP/API verification | `support-http-verify` |
| message or event verification | `support-message-verify` |
| RPC/service invocation verification | `support-rpc-verify` |
| scheduled task or batch job verification | `support-task-verify` |
| UI integration verification | `support-ui-verify` |
| language-level coding standards | `support-language-standards` |
| infrastructure component catalog | `support-infra-catalog` |
| business rule catalog | `support-domain-rules` |
| reusable domain component catalog | `support-domain-components` |

## Integration Rule

Use these support skills for capability routing and instructions. Use provider adapters for real platform access, authentication, deployment, query, and verification commands.
