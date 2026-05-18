---
name: coding-standards
description: >
  Project coding standards catalog. Use after modifying code, during review,
  or before implementing language/framework-sensitive changes. The default
  catalog is language-neutral with a Java example reference that teams can
  replace.
---

# coding-standards

Read only the relevant standard reference for the current language or concern.

## Mandatory Rules

- Check standards after code generation or modification when matching references exist.
- Do not invent organization rules. Use repository context or references.
- Treat references as examples unless the project context marks them mandatory.

## Reference Index

| Scenario | Read |
|---|---|
| General code style, naming, errors, logging, null safety | `references/general.md` |
| Java backend example standards | `references/java-example.md` |

## Review Output

Prioritize concrete findings:

```text
STANDARD_STATUS: pass|findings|not_configured
FINDINGS:
- <severity> <file:line> <rule> <fix>
```
