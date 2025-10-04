# Agent 系统改进总结

## 改进概述

参考 AgentScope 的架构，我们对 Deep Research 项目的 Agent 系统进行了全面升级。

## 新增文件

### 核心组件

1. **`src/message.py`** - 消息系统
   - `Msg` 类：统一的消息格式
   - `TextBlock`, `ToolUseBlock`, `ToolResultBlock`：内容块类型
   - 支持多模态内容和元数据

2. **`src/agents/base_agent.py`** - Agent 基础类
   - `AgentBase`：所有 Agent 的基类
   - `AgentConfig`：Agent 配置类
   - Hook 系统支持
   - 记忆管理
   - 状态跟踪

3. **`src/agents/react_agent.py`** - ReAct Agent
   - 实现 Reasoning + Acting 模式
   - 支持工具调用
   - 迭代式问题解决
   - 与 LLM 路由器集成

4. **`src/agents/research_agent.py`** - 研究 Agent
   - 专门用于研究任务
   - 预定义研究 Agent（通用、学术、市场）
   - 研究能力：搜索、分析、综合

5. **`src/agents/user_agent.py`** - 用户 Agent
   - 处理用户输入
   - 用户交互接口

6. **`src/agents/__init__.py`** - Agent 模块导出

7. **`src/tools/tool_registry.py`** - 工具注册表
   - 统一管理所有工具
   - 工具注册和查询
   - 工具 schema 管理

8. **`src/service/agent_manager_v2.py`** - Agent 管理器 V2
   - 完整的 Agent 生命周期管理
   - 三种协作模式：顺序、并行、层次化
   - 会话管理
   - Agent 注册和查询

### 文档和测试

9. **`docs/AGENT_SYSTEM.md`** - 完整的系统文档
   - 架构说明
   - 使用示例
   - 最佳实践
   - 故障排查

10. **`test_agent_system.py`** - 测试脚本
    - 基础功能测试
    - 管理器测试
    - 协作测试
    - 记忆测试

## 核心特性

### 1. 统一的消息系统

```python
# 创建消息
msg = Msg(
    name="user",
    content="研究任务",
    role="user",
    metadata={"priority": "high"}
)

# 获取内容
text = msg.get_text_content()
blocks = msg.get_content_blocks("tool_use")
```

### 2. Hook 系统

```python
# 注册 Hook
agent.register_hook("pre_reply", "logger", log_hook)
agent.register_hook("post_reply", "monitor", monitor_hook)

# 移除 Hook
agent.remove_hook("pre_reply", "logger")
```

支持的 Hook 类型：
- `pre_reply`: 回复前
- `post_reply`: 回复后
- `pre_observe`: 观察前
- `post_observe`: 观察后

### 3. ReAct 模式

```python
# ReAct 循环
while iteration < max_iterations:
    # 1. 推理
    reasoning = await agent._reasoning(context)
    
    # 2. 行动
    if reasoning.use_tool:
        action = await agent._acting(reasoning)
        
        # 3. 观察
        observation = await agent._observing(action)
        
        # 更新上下文
        context = update_context(reasoning, action, observation)
```

### 4. 多 Agent 协作

#### 顺序协作
```python
result = await manager.collaborate_agents(
    agent_ids=["planner", "researcher", "writer"],
    task="撰写报告",
    collaboration_type="sequential"
)
```

#### 并行协作
```python
result = await manager.collaborate_agents(
    agent_ids=["agent1", "agent2", "agent3"],
    task="多角度分析",
    collaboration_type="parallel"
)
```

#### 层次化协作
```python
result = await manager.collaborate_agents(
    agent_ids=["coordinator", "worker1", "worker2"],
    task="复杂任务",
    collaboration_type="hierarchical"
)
```

### 5. 记忆管理

```python
# 自动记忆管理
agent.memory.add_message("user", "消息内容")

# 获取记忆
summary = agent.get_memory_summary()
messages = agent.memory.get_messages(limit=10)

# 清空记忆
agent.clear_memory()
```

### 6. 工具系统

```python
# 注册工具
registry = get_tool_registry()
registry.register_tool(my_tool)

# Agent 使用工具
agent = ReActAgent(AgentConfig(
    name="助手",
    tools=["search", "analyze"]
))
```

## 与现有系统的集成

### 1. 保留现有 Agent Manager

原有的 `src/service/agent_manager.py` 保持不变，新系统在 `agent_manager_v2.py` 中实现，可以逐步迁移。

### 2. API 集成

```python
# 在 API 中使用新系统
from src.service.agent_manager_v2 import get_agent_manager_v2

@router.post("/agent/call")
async def call_agent(agent_id: str, message: str):
    manager = get_agent_manager_v2()
    return await manager.call_agent(agent_id, message)
```

### 3. 与 LLM 路由器集成

ReAct Agent 已经集成了 `SmartModelRouter`，可以自动选择最佳模型。

### 4. 与工具系统集成

通过 `ToolRegistry` 统一管理所有工具，Agent 可以动态调用。

## 优势

### 1. 模块化设计
- 清晰的职责分离
- 易于扩展和维护
- 可复用的组件

### 2. 灵活的协作
- 三种协作模式
- 支持复杂工作流
- 动态 Agent 组合

### 3. 强大的扩展性
- Hook 系统
- 工具注册表
- 自定义 Agent 类型

### 4. 完善的记忆
- 自动记忆管理
- 会话隔离
- 记忆摘要

### 5. 易用性
- 简洁的 API
- 丰富的文档
- 完整的示例

## 使用场景

### 1. 简单研究任务
```python
agent = ResearchAgent(config)
result = await agent.conduct_research("AI 发展")
```

### 2. 复杂研究流程
```python
manager = get_agent_manager_v2()
result = await manager.collaborate_agents(
    agent_ids=["planner", "searcher", "analyzer", "writer"],
    task="深度研究报告",
    collaboration_type="sequential"
)
```

### 3. 多角度分析
```python
result = await manager.collaborate_agents(
    agent_ids=["expert1", "expert2", "expert3"],
    task="技术评估",
    collaboration_type="parallel"
)
```

### 4. 复杂任务分解
```python
result = await manager.collaborate_agents(
    agent_ids=["coordinator", "worker1", "worker2", "worker3"],
    task="大型项目",
    collaboration_type="hierarchical"
)
```

## 下一步计划

### 短期（1-2 周）
- [ ] 完善工具系统
- [ ] 添加更多预定义 Agent
- [ ] 编写单元测试
- [ ] 性能优化

### 中期（1 个月）
- [ ] 实现 Agent 学习能力
- [ ] 添加可视化界面
- [ ] 支持更多协作模式
- [ ] 集成到主 API

### 长期（3 个月）
- [ ] 分布式 Agent 支持
- [ ] Agent 市场
- [ ] 自动化工作流
- [ ] 高级监控和分析

## 迁移指南

### 从旧系统迁移

1. **导入新模块**
```python
from src.service.agent_manager_v2 import get_agent_manager_v2
```

2. **创建 Agent**
```python
# 旧方式
agent_config = AgentConfig(id="...", name="...", ...)
manager.register_agent(agent_config)

# 新方式
from src.agents import ResearchAgent, AgentConfig
agent = ResearchAgent(AgentConfig(name="...", ...))
manager.register_agent(agent)
```

3. **调用 Agent**
```python
# 旧方式
result = await manager.call_agent(agent_id, prompt, session_id)

# 新方式（API 相同）
result = await manager.call_agent(agent_id, prompt, session_id)
```

### 兼容性

- 新系统完全独立，不影响现有功能
- API 接口保持兼容
- 可以逐步迁移

## 性能对比

| 特性 | 旧系统 | 新系统 |
|------|--------|--------|
| Agent 类型 | 配置驱动 | 类继承 |
| 协作模式 | 顺序 | 顺序/并行/层次化 |
| 记忆管理 | 手动 | 自动 |
| Hook 支持 | 无 | 完整 |
| 工具系统 | 分散 | 统一 |
| 扩展性 | 中等 | 高 |

## 总结

通过参考 AgentScope 的设计，我们构建了一个：
- ✅ 模块化的 Agent 系统
- ✅ 灵活的协作框架
- ✅ 强大的扩展能力
- ✅ 完善的文档和示例
- ✅ 与现有系统兼容

这为 Deep Research 项目提供了坚实的 Agent 基础架构，支持更复杂的研究任务和工作流。
