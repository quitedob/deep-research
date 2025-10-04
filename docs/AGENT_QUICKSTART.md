# Agent 系统快速开始

## 5 分钟上手

### 1. 创建你的第一个 Agent

```python
from src.agents import ResearchAgent, AgentConfig
from src.message import Msg
import asyncio

async def main():
    # 创建 Agent
    agent = ResearchAgent(AgentConfig(
        name="我的研究员",
        role="researcher",
        system_prompt="你是一个专业的研究员，擅长分析和总结。",
        capabilities=["research", "analysis"]
    ))
    
    # 创建消息
    msg = Msg(
        name="user",
        content="请介绍一下量子计算",
        role="user"
    )
    
    # 调用 Agent
    response = await agent(msg)
    print(f"Agent: {response.content}")

asyncio.run(main())
```

### 2. 使用 Agent 管理器

```python
from src.service.agent_manager_v2 import get_agent_manager_v2

async def main():
    # 获取管理器
    manager = get_agent_manager_v2()
    
    # 列出可用 Agent
    agents = manager.list_agents()
    print("可用的 Agents:")
    for agent in agents:
        print(f"  - {agent['config']['name']}")
    
    # 调用 Agent
    result = await manager.call_agent(
        agent_id="general_researcher",
        message="什么是深度学习？"
    )
    
    if result["success"]:
        print(f"\n{result['agent_name']}: {result['response']}")

asyncio.run(main())
```

### 3. Agent 协作

```python
from src.service.agent_manager_v2 import get_agent_manager_v2

async def main():
    manager = get_agent_manager_v2()
    
    # 顺序协作
    result = await manager.collaborate_agents(
        agent_ids=["general_researcher", "academic_researcher"],
        task="研究人工智能的伦理问题",
        collaboration_type="sequential"
    )
    
    if result["success"]:
        print(result["result"]["final_output"])

asyncio.run(main())
```

## 常用模式

### 模式 1: 简单问答

```python
async def simple_qa(question: str):
    manager = get_agent_manager_v2()
    result = await manager.call_agent(
        agent_id="general_researcher",
        message=question
    )
    return result["response"]
```

### 模式 2: 研究任务

```python
async def research_task(topic: str):
    from src.agents.research_agent import create_research_agents
    
    agents = create_research_agents()
    researcher = agents["general_researcher"]
    
    result = await researcher.conduct_research(
        topic=topic,
        requirements={"depth": "deep"}
    )
    return result
```

### 模式 3: 多步骤工作流

```python
async def multi_step_workflow(task: str):
    manager = get_agent_manager_v2()
    
    # 步骤 1: 规划
    plan = await manager.call_agent(
        agent_id="research_planner",
        message=f"为以下任务制定计划: {task}"
    )
    
    # 步骤 2: 执行
    execution = await manager.call_agent(
        agent_id="information_searcher",
        message=f"根据计划执行: {plan['response']}"
    )
    
    # 步骤 3: 总结
    summary = await manager.call_agent(
        agent_id="report_writer",
        message=f"总结结果: {execution['response']}"
    )
    
    return summary["response"]
```

### 模式 4: 使用 Hook 监控

```python
async def monitored_agent():
    from src.agents import ResearchAgent, AgentConfig
    
    agent = ResearchAgent(AgentConfig(
        name="监控研究员",
        role="researcher",
        system_prompt="你是一个研究员"
    ))
    
    # 添加日志 Hook
    async def log_hook(agent, msg):
        print(f"[LOG] Agent {agent.name} 收到消息: {msg.content[:50]}...")
        return msg
    
    agent.register_hook("pre_reply", "logger", log_hook)
    
    # 执行任务
    msg = Msg(name="user", content="研究任务", role="user")
    response = await agent(msg)
    return response.content
```

## 实用工具函数

### 批量调用 Agent

```python
async def batch_call_agents(questions: list[str], agent_id: str):
    manager = get_agent_manager_v2()
    results = []
    
    for question in questions:
        result = await manager.call_agent(
            agent_id=agent_id,
            message=question
        )
        results.append(result)
    
    return results
```

### 带重试的 Agent 调用

```python
async def call_agent_with_retry(
    agent_id: str,
    message: str,
    max_retries: int = 3
):
    manager = get_agent_manager_v2()
    
    for attempt in range(max_retries):
        try:
            result = await manager.call_agent(
                agent_id=agent_id,
                message=message
            )
            if result["success"]:
                return result
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # 指数退避
    
    return {"success": False, "error": "Max retries exceeded"}
```

### Agent 性能监控

```python
import time

async def monitored_call(agent_id: str, message: str):
    manager = get_agent_manager_v2()
    
    start_time = time.time()
    result = await manager.call_agent(agent_id, message)
    duration = time.time() - start_time
    
    print(f"调用耗时: {duration:.2f}秒")
    print(f"响应长度: {len(result.get('response', ''))}")
    
    return result
```

## 配置示例

### 创建自定义 Agent

```python
from src.agents import ReActAgent, AgentConfig

# 创建专门的代码分析 Agent
code_analyzer = ReActAgent(AgentConfig(
    name="代码分析师",
    role="code_analyzer",
    system_prompt="""你是一个专业的代码分析师。
你的职责是:
1. 分析代码结构和质量
2. 识别潜在问题
3. 提供改进建议
4. 评估代码复杂度

请提供详细、专业的分析。""",
    capabilities=["code_analysis", "bug_detection", "optimization"],
    tools=["code_parser", "static_analyzer"],
    temperature=0.3,  # 更低的温度以保持客观
    max_tokens=4000
))

# 注册到管理器
manager = get_agent_manager_v2()
manager.register_agent(code_analyzer)
```

### 配置协作工作流

```python
async def setup_research_workflow():
    manager = get_agent_manager_v2()
    
    # 定义工作流
    workflow = {
        "name": "深度研究工作流",
        "agents": [
            "research_planner",      # 1. 制定计划
            "information_searcher",  # 2. 搜索信息
            "content_analyzer",      # 3. 分析内容
            "report_writer",         # 4. 撰写报告
            "quality_reviewer"       # 5. 质量审查
        ],
        "type": "sequential"
    }
    
    return workflow

# 使用工作流
async def execute_workflow(task: str):
    workflow = await setup_research_workflow()
    manager = get_agent_manager_v2()
    
    result = await manager.collaborate_agents(
        agent_ids=workflow["agents"],
        task=task,
        collaboration_type=workflow["type"]
    )
    
    return result
```

## 调试技巧

### 1. 启用详细日志

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 2. 检查 Agent 状态

```python
agent = manager.get_agent("general_researcher")
status = agent.get_status()
print(f"Agent 状态: {status}")
```

### 3. 查看记忆内容

```python
agent = manager.get_agent("general_researcher")
memory_summary = agent.get_memory_summary()
print(f"记忆摘要:\n{memory_summary}")
```

### 4. 测试工具调用

```python
from src.tools.tool_registry import get_tool_registry

registry = get_tool_registry()
tools = registry.list_tools()
print(f"可用工具: {tools}")

# 测试单个工具
tool = registry.get_tool("search")
if tool:
    result = await tool.aexecute(query="测试查询")
    print(f"工具结果: {result}")
```

## 常见问题

### Q: Agent 不响应怎么办？

```python
# 检查 Agent 是否存在
agent = manager.get_agent("agent_id")
if not agent:
    print("Agent 不存在")

# 检查 LLM 配置
from src.llms.router import SmartModelRouter
router = SmartModelRouter.from_conf("conf.yaml")
health = await router.health()
print(f"LLM 健康状态: {health}")
```

### Q: 如何限制响应长度？

```python
agent = ResearchAgent(AgentConfig(
    name="简洁研究员",
    role="researcher",
    system_prompt="请用简洁的语言回答，不超过 200 字。",
    max_tokens=500  # 限制最大 token 数
))
```

### Q: 如何保存和加载 Agent 状态？

```python
# 保存状态
agent_dict = agent.to_dict()
import json
with open("agent_state.json", "w") as f:
    json.dump(agent_dict, f)

# 加载状态（需要自己实现反序列化）
with open("agent_state.json", "r") as f:
    agent_dict = json.load(f)
# 根据配置重新创建 Agent
```

## 下一步

- 阅读完整文档: [AGENT_SYSTEM.md](./AGENT_SYSTEM.md)
- 查看改进总结: [AGENT_IMPROVEMENTS.md](./AGENT_IMPROVEMENTS.md)
- 运行测试: `python test_agent_system.py`
- 探索示例代码

## 获取帮助

- 查看日志输出
- 检查 Agent 状态
- 阅读错误信息
- 参考文档和示例

祝你使用愉快！🚀
