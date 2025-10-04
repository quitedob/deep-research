# Agent 系统架构文档

## 概述

本项目的 Agent 系统参考了 [AgentScope](https://github.com/modelscope/agentscope) 的设计理念，实现了一个完整的多 Agent 协作框架。

## 核心组件

### 1. 消息系统 (`src/message.py`)

消息系统是 Agent 之间通信的基础。

```python
from src.message import Msg, TextBlock, ToolUseBlock, ToolResultBlock

# 创建消息
msg = Msg(
    name="user",
    content="请帮我研究人工智能",
    role="user",
    metadata={"priority": "high"}
)

# 获取文本内容
text = msg.get_text_content()

# 获取特定类型的内容块
tool_blocks = msg.get_content_blocks("tool_use")
```

**主要特性:**
- 支持多种内容类型（文本、工具调用、工具结果等）
- 自动生成唯一 ID 和时间戳
- 支持元数据附加
- 可序列化为字典

### 2. Agent 基础类 (`src/agents/base_agent.py`)

所有 Agent 的基类，提供核心功能。

```python
from src.agents import AgentBase, AgentConfig

# 创建 Agent 配置
config = AgentConfig(
    name="研究员",
    role="researcher",
    system_prompt="你是一个专业的研究员",
    capabilities=["research", "analysis"],
    tools=["search", "summarize"]
)

# 创建自定义 Agent
class MyAgent(AgentBase):
    async def reply(self, msg: Msg, **kwargs) -> Msg:
        # 实现你的逻辑
        return Msg(
            name=self.name,
            content="这是我的回复",
            role="assistant"
        )
```

**主要特性:**
- Hook 系统（pre_reply, post_reply, pre_observe, post_observe）
- 记忆管理
- 状态跟踪
- 可扩展的配置系统

### 3. ReAct Agent (`src/agents/react_agent.py`)

实现了 ReAct (Reasoning + Acting) 模式的 Agent。

```python
from src.agents import ReActAgent, AgentConfig

agent = ReActAgent(AgentConfig(
    name="ReAct 研究员",
    role="researcher",
    system_prompt="你是一个使用 ReAct 模式的研究员",
    tools=["search", "analyze"]
))

# 调用 Agent
msg = Msg(name="user", content="研究量子计算", role="user")
response = await agent(msg)
```

**ReAct 循环:**
1. **推理 (Reasoning)**: 分析任务，决定下一步行动
2. **行动 (Acting)**: 执行工具调用
3. **观察 (Observing)**: 观察工具执行结果
4. 重复直到任务完成或达到最大迭代次数

### 4. 研究 Agent (`src/agents/research_agent.py`)

专门用于研究任务的 Agent。

```python
from src.agents import ResearchAgent

agent = ResearchAgent(config)

# 执行研究
result = await agent.conduct_research(
    topic="人工智能的发展",
    requirements={"depth": "deep", "sources": 10}
)

# 分析信息源
analysis = await agent.analyze_sources(sources)

# 生成报告
report = await agent.synthesize_report(research_data)
```

**预定义的研究 Agents:**
- `general_researcher`: 通用研究员
- `academic_researcher`: 学术研究员
- `market_researcher`: 市场研究员

### 5. Agent 管理器 (`src/service/agent_manager_v2.py`)

管理多个 Agent 的生命周期和协作。

```python
from src.service.agent_manager_v2 import get_agent_manager_v2

manager = get_agent_manager_v2()

# 列出所有 Agent
agents = manager.list_agents()

# 调用单个 Agent
result = await manager.call_agent(
    agent_id="general_researcher",
    message="研究深度学习",
    session_id="session_1"
)

# Agent 协作
result = await manager.collaborate_agents(
    agent_ids=["planner", "researcher", "writer"],
    task="撰写一份关于 AI 的报告",
    collaboration_type="sequential"  # 或 "parallel", "hierarchical"
)
```

**协作模式:**

1. **顺序协作 (Sequential)**
   - Agent 按顺序执行
   - 每个 Agent 的输出作为下一个的输入
   - 适合流水线式任务

2. **并行协作 (Parallel)**
   - 所有 Agent 同时执行相同任务
   - 各自独立工作
   - 适合需要多角度分析的任务

3. **层次化协作 (Hierarchical)**
   - 第一个 Agent 作为协调者
   - 其他 Agent 作为工作者
   - 协调者分配任务并综合结果
   - 适合复杂的多步骤任务

## Hook 系统

Hook 系统允许在 Agent 执行的关键点插入自定义逻辑。

```python
# 定义 Hook 函数
async def my_pre_reply_hook(agent, msg):
    print(f"Agent {agent.name} 即将回复")
    # 可以修改消息
    return msg

async def my_post_reply_hook(agent, kwargs, response):
    print(f"Agent {agent.name} 已回复: {response.content}")
    # 可以修改响应
    return response

# 注册 Hook
agent.register_hook("pre_reply", "my_hook", my_pre_reply_hook)
agent.register_hook("post_reply", "my_hook", my_post_reply_hook)

# 移除 Hook
agent.remove_hook("pre_reply", "my_hook")
```

**支持的 Hook 类型:**
- `pre_reply`: 在生成回复之前
- `post_reply`: 在生成回复之后
- `pre_observe`: 在观察消息之前
- `post_observe`: 在观察消息之后

## 记忆系统

每个 Agent 都有内置的记忆系统。

```python
# 获取记忆摘要
summary = agent.get_memory_summary()

# 清空记忆
agent.clear_memory()

# 获取消息数量
count = agent.memory.get_message_count()

# 获取最近的消息
messages = agent.memory.get_messages(limit=5)
```

## 工具系统

Agent 可以使用工具来扩展能力。

```python
from src.tools.tool_registry import get_tool_registry
from src.tools.base_tool import BaseTool

# 创建自定义工具
class MyTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="my_tool",
            description="我的自定义工具"
        )
    
    async def aexecute(self, query: str, **kwargs):
        # 实现工具逻辑
        return ToolResult(
            success=True,
            data="工具执行结果"
        )

# 注册工具
registry = get_tool_registry()
registry.register_tool(MyTool())

# Agent 使用工具
agent = ReActAgent(AgentConfig(
    name="工具使用者",
    role="assistant",
    system_prompt="你可以使用工具",
    tools=["my_tool"]
))
```

## 使用示例

### 示例 1: 简单的研究任务

```python
import asyncio
from src.agents import ResearchAgent, AgentConfig
from src.message import Msg

async def simple_research():
    # 创建研究 Agent
    agent = ResearchAgent(AgentConfig(
        name="研究员",
        role="researcher",
        system_prompt="你是一个专业的研究员",
        capabilities=["research", "analysis"]
    ))
    
    # 创建研究任务
    msg = Msg(
        name="user",
        content="请研究量子计算的最新进展",
        role="user"
    )
    
    # 执行研究
    response = await agent(msg)
    print(response.content)

asyncio.run(simple_research())
```

### 示例 2: 多 Agent 协作

```python
from src.service.agent_manager_v2 import get_agent_manager_v2

async def collaborative_research():
    manager = get_agent_manager_v2()
    
    # 顺序协作：规划 -> 研究 -> 撰写
    result = await manager.collaborate_agents(
        agent_ids=[
            "research_planner",      # 制定研究计划
            "information_searcher",  # 搜索信息
            "report_writer"          # 撰写报告
        ],
        task="撰写一份关于人工智能伦理的研究报告",
        collaboration_type="sequential"
    )
    
    print(result["result"]["final_output"])

asyncio.run(collaborative_research())
```

### 示例 3: 使用 Hook 监控

```python
async def monitored_agent():
    agent = ResearchAgent(config)
    
    # 添加性能监控 Hook
    async def performance_hook(agent, kwargs, response):
        print(f"响应长度: {len(response.content)}")
        print(f"迭代次数: {response.metadata.get('iterations', 0)}")
        return response
    
    agent.register_hook("post_reply", "performance", performance_hook)
    
    # 执行任务
    msg = Msg(name="user", content="研究任务", role="user")
    response = await agent(msg)

asyncio.run(monitored_agent())
```

## 与现有系统集成

新的 Agent 系统可以与现有的 API 集成：

```python
# 在 API 端点中使用
from fastapi import APIRouter
from src.service.agent_manager_v2 import get_agent_manager_v2

router = APIRouter()

@router.post("/agent/call")
async def call_agent_endpoint(
    agent_id: str,
    message: str,
    session_id: str = None
):
    manager = get_agent_manager_v2()
    result = await manager.call_agent(
        agent_id=agent_id,
        message=message,
        session_id=session_id
    )
    return result
```

## 最佳实践

1. **选择合适的 Agent 类型**
   - 简单任务：使用基础 Agent
   - 需要工具：使用 ReAct Agent
   - 研究任务：使用 Research Agent

2. **合理使用协作模式**
   - 流水线任务：顺序协作
   - 多角度分析：并行协作
   - 复杂任务：层次化协作

3. **管理记忆**
   - 定期清理不需要的记忆
   - 使用会话 ID 隔离不同对话
   - 设置合理的记忆大小限制

4. **使用 Hook 扩展功能**
   - 日志记录
   - 性能监控
   - 内容过滤
   - 错误处理

5. **工具设计**
   - 保持工具功能单一
   - 提供清晰的描述
   - 处理异常情况
   - 返回结构化结果

## 性能优化

1. **并行执行**
   - 使用并行协作模式
   - 异步工具调用
   - 批量处理消息

2. **缓存策略**
   - 缓存工具结果
   - 缓存 LLM 响应
   - 使用记忆摘要

3. **资源管理**
   - 限制最大迭代次数
   - 设置超时时间
   - 清理过期会话

## 故障排查

### 常见问题

1. **Agent 不响应**
   - 检查 LLM 配置
   - 验证工具注册
   - 查看日志输出

2. **记忆溢出**
   - 减小 max_memory_size
   - 定期清理记忆
   - 使用记忆摘要

3. **协作失败**
   - 验证所有 Agent 存在
   - 检查协作类型
   - 查看错误日志

## 未来计划

- [ ] 支持更多协作模式
- [ ] 增强工具系统
- [ ] 添加 Agent 学习能力
- [ ] 实现 Agent 间直接通信
- [ ] 支持分布式 Agent
- [ ] 添加可视化界面

## 参考资料

- [AgentScope 官方文档](https://modelscope.github.io/agentscope/)
- [ReAct 论文](https://arxiv.org/abs/2210.03629)
- [Multi-Agent 系统设计模式](https://www.patterns.dev/posts/multi-agent-systems)
