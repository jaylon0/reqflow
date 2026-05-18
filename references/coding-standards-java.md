# Java Backend Example Standards

这是示例目录条目，不是通用规则集。

## Checklist

- 使用清晰的类、方法和变量名。
- 避免宽泛的 catch 块隐藏失败。
- 使用参数化日志，记录异常时包含异常对象。
- 应用代码中避免 `System.out`。
- 避免 `new Thread`；使用项目批准的执行器。
- 按项目惯例一致使用集合和 map 的 null 检查。
- 限制批处理大小和外部调用。
- 保持 controller/service/repository 职责分离。

## Tests

- 为业务逻辑添加或更新单元测试。
- 当项目已有该模式时，为 API 或持久化行为添加集成测试。
