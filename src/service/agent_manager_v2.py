# -*- coding: utf-8 -*-
"""
Agent 管理器 V2 - 参考 AgentScope 架构的完整实现
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from ..agents import AgentBase, AgentConfig, ReActAgent, ResearchAgent, UserAgent
from ..agents.research_agent import create_research_agents
from ..message import Msg

logger = logging.getLogger(__name__)


class AgentManagerV2:
    """Agent 管理器 - 参考 AgentScope 的完整设计"""
    
    def __init__(self):
        self.agents: Dict[str, AgentBase] = {}
        self.agent_types: Dict[str, type] = {
            "react": ReActAgent,
            "research": ResearchAgent,
            "user": UserAgent
        }
        
        # 会话管理
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
        # 协作管理
        self.collaborations: Dict[str, Dict[str, Any]] = {}
        
        # 初始化预定义 Agent
        self._init_default_agents()
        
        logger.info("Agent Manager V2 initialized")
    
    def _init_default_agents(self):
        """初始化默认 Agent"""
        # 创建研究 Agent
        research_agents = create_research_agents()
        for agent_id, agent in research_agents.items():
            self.agents[agent_id] = agent
        
        # 创建用户 Agent
        user_agent = UserAgent(AgentConfig(
            name="用户代理",
            role="user",
            system_prompt="你是用户的代理，负责处理用户输入和交互。"
        ))
        self.agents["user_agent"] = user_agent
        
        logger.info(f"Initialized {len(self.agents)} default agents")
    
    def register_agent(self, agent: AgentBase) -> bool:
        """注册 Agent"""
        try:
            if agent.id in self.agents:
                logger.warning(f"Agent {agent.id} already exists, overwriting")
            
            self.agents[agent.id] = agent
            logger.info(f"Registered agent: {agent.id} ({agent.name})")
            return True
        
        except Exception as e:
            logger.error(f"Failed to register agent {agent.id}: {e}")
            return False
    
    def unregister_agent(self, agent_id: str) -> bool:
        """注销 Agent"""
        if agent_id in self.agents:
            agent = self.agents.pop(agent_id)
            logger.info(f"Unregistered agent: {agent_id} ({agent.name})")
            return True
        else:
            logger.warning(f"Agent {agent_id} not found")
            return False
    
    def get_agent(self, agent_id: str) -> Optional[AgentBase]:
        """获取 Agent"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有 Agent"""
        return [agent.to_dict() for agent in self.agents.values()]
    
    def get_agents_by_capability(self, capability: str) -> List[AgentBase]:
        """根据能力获取 Agent"""
        matching_agents = []
        for agent in self.agents.values():
            if capability in agent.config.capabilities:
                matching_agents.append(agent)
        return matching_agents
    
    def get_agents_by_role(self, role: str) -> List[AgentBase]:
        """根据角色获取 Agent"""
        matching_agents = []
        for agent in self.agents.values():
            if agent.role == role:
                matching_agents.append(agent)
        return matching_agents
    
    async def call_agent(
        self,
        agent_id: str,
        message: str,
        session_id: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """调用 Agent"""
        agent = self.get_agent(agent_id)
        if not agent:
            return {
                "success": False,
                "error": f"Agent {agent_id} not found"
            }
        
        try:
            # 创建消息
            msg = Msg(
                name="user",
                content=message,
                role="user",
                metadata=context or {}
            )
            
            # 调用 Agent
            response = await agent(msg)
            
            # 记录会话
            if session_id:
                self._update_session(session_id, agent_id, msg, response)
            
            return {
                "success": True,
                "response": response.content,
                "metadata": response.metadata,
                "agent_id": agent_id,
                "agent_name": agent.name
            }
        
        except Exception as e:
            logger.error(f"Error calling agent {agent_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": agent_id
            }
    
    async def collaborate_agents(
        self,
        agent_ids: List[str],
        task: str,
        collaboration_type: str = "sequential",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Agent 协作"""
        collaboration_id = f"collab_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 验证 Agent 存在
        agents = []
        for agent_id in agent_ids:
            agent = self.get_agent(agent_id)
            if not agent:
                return {
                    "success": False,
                    "error": f"Agent {agent_id} not found"
                }
            agents.append(agent)
        
        try:
            if collaboration_type == "sequential":
                result = await self._sequential_collaboration(agents, task, collaboration_id)
            elif collaboration_type == "parallel":
                result = await self._parallel_collaboration(agents, task, collaboration_id)
            elif collaboration_type == "hierarchical":
                result = await self._hierarchical_collaboration(agents, task, collaboration_id)
            else:
                return {
                    "success": False,
                    "error": f"Unknown collaboration type: {collaboration_type}"
                }
            
            # 记录协作
            self.collaborations[collaboration_id] = {
                "agent_ids": agent_ids,
                "task": task,
                "type": collaboration_type,
                "result": result,
                "timestamp": datetime.now(),
                "session_id": session_id
            }
            
            return {
                "success": True,
                "collaboration_id": collaboration_id,
                "result": result
            }
        
        except Exception as e:
            logger.error(f"Collaboration error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _sequential_collaboration(
        self,
        agents: List[AgentBase],
        task: str,
        collaboration_id: str
    ) -> Dict[str, Any]:
        """顺序协作"""
        results = []
        current_input = task
        
        for i, agent in enumerate(agents):
            msg = Msg(
                name="user",
                content=current_input,
                role="user",
                metadata={
                    "collaboration_id": collaboration_id,
                    "step": i + 1,
                    "total_steps": len(agents)
                }
            )
            
            response = await agent(msg)
            results.append({
                "agent_id": agent.id,
                "agent_name": agent.name,
                "input": current_input,
                "output": response.content,
                "metadata": response.metadata
            })
            
            # 下一个 Agent 的输入是当前 Agent 的输出
            current_input = response.content
        
        return {
            "type": "sequential",
            "steps": results,
            "final_output": current_input
        }
    
    async def _parallel_collaboration(
        self,
        agents: List[AgentBase],
        task: str,
        collaboration_id: str
    ) -> Dict[str, Any]:
        """并行协作"""
        # 创建所有任务
        tasks = []
        for i, agent in enumerate(agents):
            msg = Msg(
                name="user",
                content=task,
                role="user",
                metadata={
                    "collaboration_id": collaboration_id,
                    "agent_index": i
                }
            )
            tasks.append(agent(msg))
        
        # 并行执行
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 收集结果
        results = []
        for i, (agent, response) in enumerate(zip(agents, responses)):
            if isinstance(response, Exception):
                results.append({
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "error": str(response)
                })
            else:
                results.append({
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "output": response.content,
                    "metadata": response.metadata
                })
        
        return {
            "type": "parallel",
            "results": results
        }
    
    async def _hierarchical_collaboration(
        self,
        agents: List[AgentBase],
        task: str,
        collaboration_id: str
    ) -> Dict[str, Any]:
        """层次化协作 - 第一个 Agent 作为协调者"""
        if len(agents) < 2:
            return await self._sequential_collaboration(agents, task, collaboration_id)
        
        coordinator = agents[0]
        workers = agents[1:]
        
        # 协调者分析任务
        coordinator_msg = Msg(
            name="user",
            content=f"请分析以下任务并制定执行计划:\n{task}",
            role="user",
            metadata={
                "collaboration_id": collaboration_id,
                "role": "coordinator"
            }
        )
        
        plan_response = await coordinator(coordinator_msg)
        
        # 工作者并行执行
        worker_tasks = []
        for worker in workers:
            worker_msg = Msg(
                name="coordinator",
                content=f"执行计划:\n{plan_response.content}\n\n原始任务:\n{task}",
                role="user",
                metadata={
                    "collaboration_id": collaboration_id,
                    "role": "worker"
                }
            )
            worker_tasks.append(worker(worker_msg))
        
        worker_responses = await asyncio.gather(*worker_tasks, return_exceptions=True)
        
        # 协调者综合结果
        synthesis_content = f"原始任务:\n{task}\n\n执行计划:\n{plan_response.content}\n\n工作结果:\n"
        for i, (worker, response) in enumerate(zip(workers, worker_responses)):
            if isinstance(response, Exception):
                synthesis_content += f"\n{worker.name}: 执行失败 - {str(response)}"
            else:
                synthesis_content += f"\n{worker.name}: {response.content}"
        
        synthesis_msg = Msg(
            name="user",
            content=f"{synthesis_content}\n\n请综合以上结果，给出最终答案。",
            role="user",
            metadata={
                "collaboration_id": collaboration_id,
                "role": "synthesis"
            }
        )
        
        final_response = await coordinator(synthesis_msg)
        
        return {
            "type": "hierarchical",
            "coordinator": {
                "agent_id": coordinator.id,
                "agent_name": coordinator.name,
                "plan": plan_response.content,
                "final_output": final_response.content
            },
            "workers": [
                {
                    "agent_id": worker.id,
                    "agent_name": worker.name,
                    "output": response.content if not isinstance(response, Exception) else f"Error: {response}"
                }
                for worker, response in zip(workers, worker_responses)
            ]
        }
    
    def _update_session(
        self,
        session_id: str,
        agent_id: str,
        input_msg: Msg,
        output_msg: Msg
    ):
        """更新会话记录"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "created_at": datetime.now(),
                "messages": [],
                "agents_used": set()
            }
        
        session = self.sessions[session_id]
        session["messages"].extend([
            input_msg.to_dict(),
            output_msg.to_dict()
        ])
        session["agents_used"].add(agent_id)
        session["last_activity"] = datetime.now()


# 全局实例
_agent_manager_v2 = None


def get_agent_manager_v2() -> AgentManagerV2:
    """获取全局 Agent Manager V2 实例"""
    global _agent_manager_v2
    if _agent_manager_v2 is None:
        _agent_manager_v2 = AgentManagerV2()
    return _agent_manager_v2
