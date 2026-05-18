# Memory System

三层记忆系统，参考 CrewAI 的多层记忆设计。

## 三层结构

### Short-term Memory（短期记忆）
当前 run 的上下文，替代单一的 state.json。

### Long-term Memory（长期记忆）
跨 run 的经验教训积累，替代单一的 lessons_learned 字段。

### Entity Memory（实体记忆）
项目级知识图谱：类、模块、接口的关系。

## 记忆格式

```yaml
memory:
  short_term:
    - key: "current-work-item"
      value: "implement user auth"
      timestamp: "2025-05-14T10:00:00"
  long_term:
    - lesson: "JWT token 过期时间不要超过 24h"
      source: "run-2025-05-10"
      category: "security"
  entity:
    - name: "UserService"
      type: "class"
      location: "src/main/java/service/UserService.java"
      dependencies: ["UserRepository", "JwtProvider"]
```
