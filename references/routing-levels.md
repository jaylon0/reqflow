# Routing Levels

ReqFlow 使用四级路由：

- **L0 analyze-only**: 仅检查和解释，不做修改。
- **L1 light-change**: 低风险的本地编辑和聚焦检查。
- **L2 planned-change**: 先计划，再实现并本地验证。
- **L3 delivery-loop**: 实现、构建、部署（如已配置）、验证、修复失败。

不确定时，选择更安全的更高级别并解释权衡。
