# -*- coding: utf-8 -*-
"""
AgentScope 智能体服务
负责管理和协调 AgentScope v1.0 智能体
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from src.core.agents import AgentBase, AgentConfig, ReActAgent, ResearchAgent
from src.core.memory import InMemoryMemory, Mem0LongTermMemory
from src.core.llms.router import SmartModelRouter
from src.config import get_settings

logger = logging.getLogger(__name__)


class AgentScopeService:
    """AgentScope 智能体服务"""

    def __init__(self):
        """初始化服务"""
        self.settings = get_settings()
        self.agents: Dict[str, AgentBase] = {}
        self.llm_router = None
        self._initialized = False

    async def initialize(self):
        """初始化服务"""
        if self._initialized:
            return

        try:
            # 初始化 LLM 路由器
            conf_path = self.settings.BASE_DIR / "conf.yaml"
            self.llm_router = SmartModelRouter.from_conf(conf_path)

            # 创建默认智能体
            await self._create_default_agents()

            self._initialized = True
            logger.info("AgentScope service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize AgentScope service: {e}")
            raise

    async def _create_default_agents(self):
        """创建默认智能体"""
        # 1. 协调器智能体
        coordinator_config = AgentConfig(
            name="Coordinator",
            role="coordinator",
            system_prompt="你是一个智能协调器，负责理解用户需求、澄清问题、规划任务。",
            model_name="qwen-max",
            capabilities=["clarification", "planning", "coordination"],
            tools=["web_search", "wikipedia"],
            use_react=True,
            enable_async=True,
            enable_parallel_tools=True,
            enable_long_term_memory=True,
            long_term_memory_type="mem0_agent_control",
            reasoning_mode="step_by_step",
            language_style="professional"
        )
        self.agents["coordinator"] = await self._create_agent(coordinator_config)

        # 2. 研究员智能体
        researcher_config = AgentConfig(
            name="Researcher",
            role="researcher",
            system_prompt="你是一个专业研究员，负责信息收集、数据分析、证据链构建。",
            model_name="qwen-max",
            capabilities=["research", "analysis", "evidence_collection"],
            tools=["web_search", "arxiv", "wikipedia"],
            use_react=True,
            enable_async=True,
            enable_parallel_tools=True,
            enable_long_term_memory=True,
            reasoning_mode="chain_of_thought",
            language_style="academic"
        )
        self.agents["researcher"] = await self._create_agent(researcher_config)

        # 3. 编码员智能体
        coder_config = AgentConfig(
            name="Coder",
            role="coder",
            system_prompt="你是一个专业编码员，负责代码执行、数据处理、技术实现。",
            model_name="deepseek-v3",
            capabilities=["coding", "execution", "data_processing"],
            tools=["code_executor", "python_repl"],
            use_react=True,
            enable_async=True,
            enable_parallel_tools=False,  # 代码执行不并行
            enable_long_term_memory=True,
            reasoning_mode="step_by_step",
            language_style="technical"
        )
        self.agents["coder"] = await self._create_agent(coder_config)

        # 4. 报告员智能体
        reporter_config = AgentConfig(
            name="Reporter",
            role="reporter",
            system_prompt="你是一个专业报告员，负责内容生成、结构化写作、结果总结。",
            model_name="qwen-max",
            capabilities=["writing", "summarization", "reporting"],
            tools=[],
            use_react=False,  # 报告员不需要 ReAct
            enable_async=True,
            enable_parallel_tools=False,
            enable_long_term_memory=True,
            reasoning_mode="direct",
            language_style="professional",
            output_format="markdown"
        )
        self.agents["reporter"] = await self._create_agent(reporter_config)

        logger.info(f"Created {len(self.agents)} default agents")

    async def _create_agent(self, config: AgentConfig) -> AgentBase:
        """创建智能体实例"""
        try:
            # 创建记忆
            memory = InMemoryMemory()

            # 创建长期记忆
            long_term_memory = None
            if config.enable_long_term_memory:
                try:
                    long_term_memory = Mem0LongTermMemory(
                        agent_name=config.name,
                        user_name="system"
                    )
                except Exception as e:
                    logger.warning(f"Failed to create long-term memory for {config.name}: {e}")

            # 根据配置创建不同类型的智能体
            if config.role == "researcher":
                agent = ResearchAgent(
                    name=config.name,
                    config=config,
                    memory=memory,
                    long_term_memory=long_term_memory
                )
            elif config.use_react:
                agent = ReActAgent(
                    name=config.name,
                    config=config,
                    memory=memory,
                    long_term_memory=long_term_memory
                )
            else:
                # 基础智能体
                agent = AgentBase(
                    name=config.name,
                    config=config,
                    memory=memory,
                    long_term_memory=long_term_memory
                )

            logger.info(f"Created agent: {config.name} ({config.role})")
            return agent

        except Exception as e:
            logger.error(f"Failed to create agent {config.name}: {e}")
            raise

    async def get_agent(self, agent_id: str) -> Optional[AgentBase]:
        """获取智能体"""
        if not self._initialized:
            await self.initialize()

        return self.agents.get(agent_id)

    async def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有智能体"""
        if not self._initialized:
            await self.initialize()

        return [agent.to_dict() for agent in self.agents.values()]

    async def call_agent(
        self,
        agent_id: str,
        message: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """调用智能体"""
        if not self._initialized:
            await self.initialize()

        agent = self.agents.get(agent_id)
        if not agent:
            return {
                "success": False,
                "error": f"Agent {agent_id} not found",
                "agent_id": agent_id
            }

        try:
            # 创建消息
            from agentscope.message import Msg
            msg = Msg(name="user", content=message, role="user")

            # 调用智能体
            response_msg = await agent.reply(msg)

            return {
                "success": True,
                "response": response_msg.content if hasattr(response_msg, 'content') else str(response_msg),
                "agent_id": agent_id,
                "agent_name": agent.name,
                "metadata": response_msg.metadata if hasattr(response_msg, 'metadata') else {}
            }

        except Exception as e:
            logger.error(f"Error calling agent {agent_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": agent_id,
                "agent_name": agent.name if agent else None
            }

    async def collaborate_agents(
        self,
        task: str,
        agent_ids: List[str],
        collaboration_type: str = "sequential",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """智能体协作"""
        if not self._initialized:
            await self.initialize()

        # 验证智能体存在
        agents = []
        for agent_id in agent_ids:
            agent = self.agents.get(agent_id)
            if not agent:
                return {
                    "success": False,
                    "error": f"Agent {agent_id} not found"
                }
            agents.append(agent)

        try:
            from agentscope.message import Msg

            if collaboration_type == "sequential":
                # 顺序执行
                results = []
                current_msg = Msg(name="user", content=task, role="user")

                for agent in agents:
                    response_msg = await agent.reply(current_msg)
                    results.append({
                        "agent_id": agent.name,
                        "agent_name": agent.name,
                        "response": response_msg.content if hasattr(response_msg, 'content') else str(response_msg)
                    })
                    # 下一个智能体接收上一个的输出
                    current_msg = response_msg

                return {
                    "success": True,
                    "task": task,
                    "collaboration_type": collaboration_type,
                    "results": results,
                    "session_id": session_id
                }

            elif collaboration_type == "parallel":
                # 并行执行
                msg = Msg(name="user", content=task, role="user")
                tasks = [agent.reply(msg) for agent in agents]
                responses = await asyncio.gather(*tasks, return_exceptions=True)

                results = []
                for agent, response in zip(agents, responses):
                    if isinstance(response, Exception):
                        results.append({
                            "agent_id": agent.name,
                            "agent_name": agent.name,
                            "error": str(response)
                        })
                    else:
                        results.append({
                            "agent_id": agent.name,
                            "agent_name": agent.name,
                            "response": response.content if hasattr(response, 'content') else str(response)
                        })

                return {
                    "success": True,
                    "task": task,
                    "collaboration_type": collaboration_type,
                    "results": results,
                    "session_id": session_id
                }

            elif collaboration_type == "hierarchical":
                # 层级执行：第一个智能体作为协调器
                coordinator = agents[0]
                workers = agents[1:]

                # 协调器分析任务
                msg = Msg(name="user", content=task, role="user")
                coordinator_response = await coordinator.reply(msg)

                # 工作智能体并行执行
                worker_tasks = [worker.reply(coordinator_response) for worker in workers]
                worker_responses = await asyncio.gather(*worker_tasks, return_exceptions=True)

                # 协调器总结结果
                summary_content = f"任务: {task}\n\n工作结果:\n"
                for worker, response in zip(workers, worker_responses):
                    if not isinstance(response, Exception):
                        summary_content += f"\n{worker.name}: {response.content if hasattr(response, 'content') else str(response)}\n"

                summary_msg = Msg(name="system", content=summary_content, role="system")
                final_response = await coordinator.reply(summary_msg)

                return {
                    "success": True,
                    "task": task,
                    "collaboration_type": collaboration_type,
                    "coordinator_analysis": coordinator_response.content if hasattr(coordinator_response, 'content') else str(coordinator_response),
                    "worker_results": [
                        {
                            "agent_id": worker.name,
                            "agent_name": worker.name,
                            "response": response.content if hasattr(response, 'content') and not isinstance(response, Exception) else str(response)
                        }
                        for worker, response in zip(workers, worker_responses)
                    ],
                    "final_summary": final_response.content if hasattr(final_response, 'content') else str(final_response),
                    "session_id": session_id
                }

            else:
                return {
                    "success": False,
                    "error": f"Unknown collaboration type: {collaboration_type}"
                }

        except Exception as e:
            logger.error(f"Error in agent collaboration: {e}")
            return {
                "success": False,
                "error": str(e),
                "task": task
            }

    async def create_custom_agent(
        self,
        name: str,
        role: str,
        system_prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """创建自定义智能体"""
        if not self._initialized:
            await self.initialize()

        try:
            config = AgentConfig(
                name=name,
                role=role,
                system_prompt=system_prompt,
                **kwargs
            )

            agent = await self._create_agent(config)
            self.agents[name] = agent

            return {
                "success": True,
                "agent_id": name,
                "agent": agent.to_dict()
            }

        except Exception as e:
            logger.error(f"Failed to create custom agent: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def remove_agent(self, agent_id: str) -> bool:
        """移除智能体"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Removed agent: {agent_id}")
            return True
        return False

    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取智能体状态"""
        agent = self.agents.get(agent_id)
        if agent:
            return agent.get_status()
        return None

    async def shutdown(self):
        """关闭服务"""
        logger.info("Shutting down AgentScope service")
        self.agents.clear()
        self._initialized = False


# 全局服务实例
_agentscope_service: Optional[AgentScopeService] = None


def get_agentscope_service() -> AgentScopeService:
    """获取 AgentScope 服务实例"""
    global _agentscope_service
    if _agentscope_service is None:
        _agentscope_service = AgentScopeService()
    return _agentscope_service
