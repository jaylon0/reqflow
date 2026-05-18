# Tool Registry

工具注册机制，定义模型可用的工具集。

## 注册格式

```yaml
tools:
  registered:
    - name: build
      type: local_command
      command: "mvn clean test"
    - name: deploy
      type: provider_adapter
      adapter: ".dev-workflow/adapters/deploy-adapter.py"
    - name: verify-api
      type: manual_checklist
      template: "templates/verify-api-checklist.md"
```

## 工具类型

| type | 说明 |
|------|------|
| local_command | 本地shell命令 |
| provider_adapter | 外部provider适配器脚本 |
| manual_checklist | 人工执行checklist |
