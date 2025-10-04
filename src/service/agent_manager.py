# -*- coding: utf-8 -*-
"""
Agent管理器服务
支持动态Agent注册、会话管理和智能调度
"""

import time
import logging
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

from ..llms.router import SmartModelRouter
from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class AgentConfig:
    """Agent配置类"""
    id: str
    name: str
    base_name: str
    system_prompt: str
    max_output_tokens: int = 4000
    temperature: float = 0.7
    description: str = ""
    model_provider: str = "kimi"
    capabilities: List[str] = field(default_factory=list)


@dataclass
class AgentSession:
    """Agent会话类"""
    timestamp: float = field(default_factory=time.time)
    history: List[Dict[str, str]] = field(default_factory=list)
    session_id: str = "default_session"
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentManager:
    """Agent管理器 - 支持多Agent协作和智能调度"""
    
    def __init__(self):
        self.agents: Dict[str, AgentConfig] = {}
        self.agent_sessions: Dict[str, Dict[str, AgentSession]] = {}
        self.max_history_rounds = 10
        self.context_ttl_hours = 24
        self.llm_router = None
        
        # 初始化默认agents
        self._init_default_agents()
        
        # 启动清理任务
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self._periodic_cleanup())
        except RuntimeError:
            pass
    
    def _init_default_agents(self):
        """初始化默认的研究agents"""
        # 研究规划agent
        self.register_agent(AgentConfig(
            id="research_planner",
            name="研究规划师",
            base_name="planner",
            system_prompt="""你是一个专业的研究规划师。你的职责是：
1. 分析用户的研究需求
2. 制定详细的研究计划
3. 分解任务为可执行的步骤
4. 评估研究的可行性和所需资源

请以结构化的方式输出研究计划。""",
            description="负责制定研究计划和任务分解",
            capabilities=["planning", "task_decomposition", "feasibility_analysis"]
        ))
        
        # 信息搜索agent
        self.register_agent(AgentConfig(
            id="information_searcher",
            name="信息搜索专家",
            base_name="searcher",
            system_prompt="""你是一个专业的信息搜索专家。你的职责是：
1. 根据研究主题搜索相关信息
2. 评估信息来源的可靠性
3. 提取关键信息和数据
4. 整理和分类搜索结果

请提供高质量、相关性强的搜索结果。""",
            description="负责信息检索和来源评估",
            capabilities=["search", "information_extraction", "source_evaluation"]
        ))
        
        # 内容分析agent
        self.register_agent(AgentConfig(
            id="content_analyzer",
            name="内容分析师",
            base_name="analyzer",
            system_prompt="""你是一个专业的内容分析师。你的职责是：
1. 深入分析收集到的信息
2. 识别关键模式和趋势
3. 提取核心观点和论据
4. 评估信息的质量和相关性

请提供深入、客观的分析结果。""",
            description="负责内容深度分析和洞察提取",
            capabilities=["analysis", "pattern_recognition", "insight_extraction"]
        ))
        
        # 报告撰写agent
        self.register_agent(AgentConfig(
            id="report_writer",
            name="报告撰写专家",
            base_name="writer",
            system_prompt="""你是一个专业的报告撰写专家。你的职责是：
1. 将分析结果整合成连贯的报告
2. 确保报告结构清晰、逻辑严密
3. 使用专业的学术语言
4. 提供准确的引用和参考文献

请生成高质量、专业的研究报告。""",
            description="负责报告撰写和内容整合",
            capabilities=["writing", "synthesis", "formatting"]
        ))
        
        # 质量审查agent
        self.register_agent(AgentConfig(
            id="quality_reviewer",
            name="质量审查员",
            base_name="reviewer",
            system_prompt="""你是一个严格的质量审查员。你的职责是：
1. 审查报告的准确性和完整性
2. 检查逻辑一致性和论证质量
3. 验证引用和数据的准确性
4. 提供具体的改进建议

请提供客观、建设性的审查意见。""",
            description="负责质量审查和改进建议",
            capabilities=["review", "fact_checking", "quality_assessment"],
            temperature=0.3  # 更低的温度以保持客观
        ))
        
        logger.info(f"已初始化 {len(self.agents)} 个默认Agent")
    
    def register_agent(self, agent_config: AgentConfig):
        """注册新的Agent"""
        self.agents[agent_config.id] = agent_config
        logger.info(f"已注册Agent: {agent_config.id} ({agent_config.name})")
    
    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """获取Agent配置"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有可用的Agents"""
        return [
            {
                "id": agent.id,
                "name": agent.name,
                "base_name": agent.base_name,
                "description": agent.description,
                "capabilities": agent.capabilities
            }
            for agent in self.agents.values()
        ]
    
    def get_agent_session_history(
        self,
        agent_id: str,
        session_id: str = "default_session"
    ) -> List[Dict[str, str]]:
        """获取Agent会话历史"""
        if agent_id not in self.agent_sessions:
            self.agent_sessions[agent_id] = {}
        
        agent_sessions = self.agent_sessions[agent_id]
        if session_id not in agent_sessions or self._is_context_expired(
            agent_sessions[session_id].timestamp
        ):
            agent_sessions[session_id] = AgentSession(session_id=session_id)
        
        return agent_sessions[session_id].history
    
    def update_agent_session_history(
        self,
        agent_id: str,
        user_message: str,
        assistant_message: str,
        session_id: str = "default_session"
    ):
        """更新Agent会话历史"""
        if agent_id not in self.agent_sessions:
            self.agent_sessions[agent_id] = {}
        
        agent_sessions = self.agent_sessions[agent_id]
        if session_id not in agent_sessions or self._is_context_expired(
            agent_sessions[session_id].timestamp
        ):
            agent_sessions[session_id] = AgentSession(session_id=session_id)
        
        session_data = agent_sessions[session_id]
        session_data.history.extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_message}
        ])
        session_data.timestamp = time.time()
        
        # 限制历史消息数量
        max_messages = self.max_history_rounds * 2
        if len(session_data.history) > max_messages:
            session_data.history = session_data.history[-max_messages:]
    
    def _is_context_expired(self, timestamp: float) -> bool:
        """检查上下文是否过期"""
        return (time.time() - timestamp) > (self.context_ttl_hours * 3600)
    
    async def _periodic_cleanup(self):
        """定期清理过期的会话上下文"""
        while True:
            try:
                await asyncio.sleep(3600)  # 每小时清理一次
                
                for agent_id, sessions in list(self.agent_sessions.items()):
                    for session_id, session_data in list(sessions.items()):
                        if self._is_context_expired(session_data.timestamp):
                            sessions.pop(session_id, None)
                            logger.debug(f"清理过期上下文: {agent_id}, session {session_id}")
                    
                    if not sessions:
                        self.agent_sessions.pop(agent_id, None)
                        
            except Exception as e:
                logger.error(f"定期清理任务出错: {e}")
    
    async def call_agent(
        self,
        agent_id: str,
        prompt: str,
        session_id: str = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        调用指定的Agent
        
        Args:
            agent_id: Agent ID
            prompt: 用户提示词
            session_id: 会话ID
            context: 额外的上下文信息
            
        Returns:
            Dict[str, Any]: 调用结果
        """
        # 检查Agent是否存在
        if agent_id not in self.agents:
            return {
                "status": "error",
                "error": f"Agent '{agent_id}' 不存在"
            }
        
        agent_config = self.agents[agent_id]
        
        # 生成会话ID
        if not session_id:
            session_id = f"agent_{agent_config.base_name}_default"
        
        try:
            # 获取会话历史
            history = self.get_agent_session_history(agent_id, session_id)
            
            # 构建消息序列
            messages = []
            
            # 系统消息
            messages.append({
                "role": "system",
                "content": agent_config.system_prompt
            })
            
            # 添加上下文信息
            if context:
                context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
                messages.append({
                    "role": "system",
                    "content": f"上下文信息:\n{context_str}"
                })
            
            # 历史消息
            messages.extend(history)
            
            # 当前用户输入
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # 初始化LLM路由器
            if not self.llm_router:
                from pathlib import Path
                self.llm_router = SmartModelRouter.from_conf(
                    settings.BASE_DIR / "conf.yaml"
                )
            
            # 调用LLM
            response = await self.llm_router.route_and_chat(
                task_type="agent_task",
                messages=messages,
                estimated_input_tokens=sum(len(m["content"]) for m in messages) // 4,
                estimated_output_tokens=agent_config.max_output_tokens // 4,
                temperature=agent_config.temperature,
                max_tokens=agent_config.max_output_tokens
            )
            
            if response.get("content"):
                assistant_response = response["content"]
                
                # 更新会话历史
                self.update_agent_session_history(
                    agent_id, prompt, assistant_response, session_id
                )
                
                return {
                    "status": "success",
                    "result": assistant_response,
                    "agent_id": agent_id,
                    "agent_name": agent_config.name
                }
            else:
                return {
                    "status": "error",
                    "error": "LLM返回空响应"
                }
                
        except Exception as e:
            logger.error(f"调用Agent '{agent_id}' 时发生错误: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def collaborate_agents(
        self,
        task: str,
        agent_ids: List[str],
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        多Agent协作完成任务
        
        Args:
            task: 任务描述
            agent_ids: 参与的Agent IDs
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 协作结果
        """
        if not session_id:
            session_id = f"collab_{int(time.time())}"
        
        results = []
        context = {"task": task}
        
        for agent_id in agent_ids:
            # 调用每个Agent
            result = await self.call_agent(
                agent_id=agent_id,
                prompt=task,
                session_id=session_id,
                context=context
            )
            
            if result.get("status") == "success":
                results.append({
                    "agent_id": agent_id,
                    "agent_name": result.get("agent_name"),
                    "result": result.get("result")
                })
                
                # 更新上下文，供后续Agent使用
                context[f"{agent_id}_output"] = result.get("result")
            else:
                results.append({
                    "agent_id": agent_id,
                    "error": result.get("error")
                })
        
        return {
            "status": "success",
            "task": task,
            "results": results,
            "session_id": session_id
        }


# 全局Agent管理器实例
_agent_manager = None


def get_agent_manager() -> AgentManager:
    """获取全局Agent管理器实例"""
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager()
    return _agent_manager
