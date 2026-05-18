# Context Schema

最小项目上下文：

```yaml
project:
  name: ""
  type: "backend-service"
  languages: []
  frameworks: []
  package_manager: ""
  build_commands: []
  test_commands: []
  lint_commands: []
  source_roots: []
  test_roots: []
workflow:
  default_level: "auto"
  max_retries: 3
```

仅在对当前项目有用时添加字段。
