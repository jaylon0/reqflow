# Adapter Lifecycle

Provider 适配器遵循相同生命周期：

1. 发现上下文。
2. 检查能力和认证。
3. 规范化输入 JSON。
4. 执行一个操作。
5. 如需要，轮询或检查状态。
6. 返回结构化 JSON。
7. 将缺失认证、缺失配置或不可用平台转换为 `blocked` 并附带 `action_required`。

适配器应在 dry-run 验证期间避免隐藏副作用。
