#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangGraph工作流实现 - 基于AgentScope的StateGraph
研究工作流：researcher → writer → supervisor
"""
import logging
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import operator

from agentscope.message import Msg

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict):
    """工作流状态定义"""
    query: str
    research_results: List[Dict[str, Any]]
    draft_content: str
    final_content: str
    feedback: List[str]
    iteration: int
    max_iterations: int
    status: str
    metadata: Dict[str, Any]


class NodeStatus(str, Enum):
    """节点状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowDecision(str, Enum):
    """工作流决策"""
    CONTINUE = "continue"
    REVISE = "revise"
    FINISH = "finish"


@dataclass
class ResearchWorkflowConfig:
    """研究工作流配置"""
    max_iterations: int = 3
    min_research_sources: int = 3
    quality_threshold: float = 0.7
    enable_parallel_research: bool = True
    enable_supervisor_feedback: bool = True


class LangGraphWorkflow:
    """LangGraph工作流编排器"""
    
    def __init__(self, config: Optional[ResearchWorkflowConfig] = None):
        self.config = config or ResearchWorkflowConfig()
        self.state: Optional[WorkflowState] = None
        self.execution_history: List[Dict[str, Any]] = []
        
    def initialize_state(self, query: str, **kwargs) -> WorkflowState:
        """初始化工作流状态"""
        self.state = WorkflowState(
            query=query,
            research_results=[],
            draft_content="",
            final_content="",
            feedback=[],
            iteration=0,
            max_iterations=self.config.max_iterations,
            status="initialized",
            metadata={
                "start_time": datetime.now().isoformat(),
                "config": {
                    "max_iterations": self.config.max_iterations,
                    "min_research_sources": self.config.min_research_sources,
                    "quality_threshold": self.config.quality_threshold
                },
                **kwargs
            }
        )
        return self.state
    
    async def run(self, query: str, **kwargs) -> Dict[str, Any]:
        """运行完整工作流"""
        try:
            # 初始化状态
            state = self.initialize_state(query, **kwargs)
            
            logger.info(f"Starting research workflow for query: {query[:50]}...")
            
            # 工作流循环
            while state["iteration"] < state["max_iterations"]:
                state["iteration"] += 1
                logger.info(f"Workflow iteration {state['iteration']}/{state['max_iterations']}")
                
                # 1. 研究节点
                state = await self.researcher_node(state)
                if state["status"] == "failed":
                    break
                
                # 2. 写作节点
                state = await self.writer_node(state)
                if state["status"] == "failed":
                    break
                
                # 3. 监督节点
                decision = await self.supervisor_node(state)
                
                # 4. 条件路由
                if decision == WorkflowDecision.FINISH:
                    state["status"] = "completed"
                    break
                elif decision == WorkflowDecision.REVISE:
                    logger.info("Supervisor requested revision, continuing...")
                    continue
                else:
                    state["status"] = "completed"
                    break
            
            # 完成工作流
            state["metadata"]["end_time"] = datetime.now().isoformat()
            
            return {
                "success": True,
                "state": state,
                "final_content": state["final_content"],
                "research_results": state["research_results"],
                "iterations": state["iteration"],
                "execution_history": self.execution_history
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "state": self.state,
                "execution_history": self.execution_history
            }
    
    async def researcher_node(self, state: WorkflowState) -> WorkflowState:
        """研究节点 - 信息收集和分析"""
        try:
            logger.info("Executing researcher node...")
            
            node_start = datetime.now()
            
            # 获取研究智能体
            from src.services.agentscope_service import get_agentscope_service
            agentscope_service = get_agentscope_service()
            await agentscope_service.initialize()
            
            # 调用研究员智能体
            result = await agentscope_service.call_agent(
                agent_id="researcher",
                message=f"请研究以下主题并收集相关信息：{state['query']}",
                context={
                    "iteration": state["iteration"],
                    "previous_results": state["research_results"]
                }
            )
            
            if result["success"]:
                # 添加研究结果
                research_item = {
                    "iteration": state["iteration"],
                    "content": result["response"],
                    "metadata": result.get("metadata", {}),
                    "timestamp": datetime.now().isoformat()
                }
                state["research_results"].append(research_item)
                
                # 记录执行历史
                self.execution_history.append({
                    "node": "researcher",
                    "iteration": state["iteration"],
                    "status": "completed",
                    "duration": (datetime.now() - node_start).total_seconds(),
                    "result_summary": result["response"][:200]
                })
            else:
                state["status"] = "failed"
                state["metadata"]["error"] = f"Researcher node failed: {result.get('error')}"
            
            return state
            
        except Exception as e:
            logger.error(f"Researcher node failed: {e}")
            state["status"] = "failed"
            state["metadata"]["error"] = str(e)
            return state
    
    async def writer_node(self, state: WorkflowState) -> WorkflowState:
        """写作节点 - 内容生成和结构化"""
        try:
            logger.info("Executing writer node...")
            
            node_start = datetime.now()
            
            # 获取报告员智能体
            from src.services.agentscope_service import get_agentscope_service
            agentscope_service = get_agentscope_service()
            
            # 构建写作提示
            research_summary = "\n\n".join([
                f"研究结果 {i+1}:\n{item['content']}"
                for i, item in enumerate(state["research_results"])
            ])
            
            feedback_text = ""
            if state["feedback"]:
                feedback_text = f"\n\n反馈意见:\n" + "\n".join(state["feedback"])
            
            writing_prompt = f"""
请基于以下研究结果撰写一份完整的报告：

主题: {state['query']}

{research_summary}
{feedback_text}

请生成结构化的报告内容，包括：
1. 摘要
2. 主要发现
3. 详细分析
4. 结论和建议
"""
            
            # 调用报告员智能体
            result = await agentscope_service.call_agent(
                agent_id="reporter",
                message=writing_prompt,
                context={
                    "iteration": state["iteration"],
                    "draft_content": state["draft_content"]
                }
            )
            
            if result["success"]:
                state["draft_content"] = result["response"]
                
                # 记录执行历史
                self.execution_history.append({
                    "node": "writer",
                    "iteration": state["iteration"],
                    "status": "completed",
                    "duration": (datetime.now() - node_start).total_seconds(),
                    "content_length": len(result["response"])
                })
            else:
                state["status"] = "failed"
                state["metadata"]["error"] = f"Writer node failed: {result.get('error')}"
            
            return state
            
        except Exception as e:
            logger.error(f"Writer node failed: {e}")
            state["status"] = "failed"
            state["metadata"]["error"] = str(e)
            return state
    
    async def supervisor_node(self, state: WorkflowState) -> WorkflowDecision:
        """监督节点 - 质量评估和决策"""
        try:
            logger.info("Executing supervisor node...")
            
            if not self.config.enable_supervisor_feedback:
                # 如果禁用监督反馈，直接完成
                state["final_content"] = state["draft_content"]
                return WorkflowDecision.FINISH
            
            # 获取协调器智能体作为监督者
            from src.services.agentscope_service import get_agentscope_service
            agentscope_service = get_agentscope_service()
            
            # 构建评估提示
            evaluation_prompt = f"""
请评估以下报告的质量：

主题: {state['query']}

报告内容:
{state['draft_content']}

评估标准:
1. 内容完整性（是否充分回答了主题）
2. 逻辑清晰性（结构是否合理）
3. 信息准确性（是否基于研究结果）
4. 可读性（是否易于理解）

请给出评分（0-1）和具体反馈意见。如果评分低于{self.config.quality_threshold}，请提供改进建议。

请以JSON格式返回：
{{
    "score": 0.85,
    "feedback": "具体反馈意见",
    "decision": "finish" 或 "revise"
}}
"""
            
            result = await agentscope_service.call_agent(
                agent_id="coordinator",
                message=evaluation_prompt,
                context={
                    "iteration": state["iteration"],
                    "role": "supervisor"
                }
            )
            
            if result["success"]:
                # 解析评估结果
                import json
                try:
                    evaluation = json.loads(result["response"])
                    score = evaluation.get("score", 0.5)
                    feedback = evaluation.get("feedback", "")
                    decision_str = evaluation.get("decision", "finish")
                    
                    # 记录反馈
                    if feedback:
                        state["feedback"].append(f"迭代 {state['iteration']}: {feedback}")
                    
                    # 记录执行历史
                    self.execution_history.append({
                        "node": "supervisor",
                        "iteration": state["iteration"],
                        "status": "completed",
                        "score": score,
                        "decision": decision_str
                    })
                    
                    # 决策逻辑
                    if score >= self.config.quality_threshold or state["iteration"] >= state["max_iterations"]:
                        state["final_content"] = state["draft_content"]
                        return WorkflowDecision.FINISH
                    else:
                        return WorkflowDecision.REVISE
                        
                except json.JSONDecodeError:
                    # 如果无法解析JSON，使用简单逻辑
                    logger.warning("Failed to parse supervisor response as JSON")
                    if state["iteration"] >= state["max_iterations"]:
                        state["final_content"] = state["draft_content"]
                        return WorkflowDecision.FINISH
                    else:
                        return WorkflowDecision.CONTINUE
            else:
                # 监督失败，直接完成
                state["final_content"] = state["draft_content"]
                return WorkflowDecision.FINISH
            
        except Exception as e:
            logger.error(f"Supervisor node failed: {e}")
            # 出错时直接完成
            state["final_content"] = state["draft_content"]
            return WorkflowDecision.FINISH
    
    def get_state_dict(self) -> Dict[str, Any]:
        """获取状态字典（用于检查点）"""
        if self.state is None:
            return {}
        return dict(self.state)
    
    def load_state_dict(self, state_dict: Dict[str, Any]) -> None:
        """加载状态字典（用于恢复）"""
        self.state = WorkflowState(**state_dict)
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        if not self.state:
            return {"status": "not_started"}
        
        return {
            "query": self.state["query"],
            "status": self.state["status"],
            "iterations": self.state["iteration"],
            "research_count": len(self.state["research_results"]),
            "feedback_count": len(self.state["feedback"]),
            "has_final_content": bool(self.state["final_content"]),
            "execution_history": self.execution_history,
            "metadata": self.state["metadata"]
        }


# 全局工作流实例
_workflow_instances: Dict[str, LangGraphWorkflow] = {}


def get_langgraph_workflow(workflow_id: Optional[str] = None) -> LangGraphWorkflow:
    """获取LangGraph工作流实例"""
    if workflow_id is None:
        workflow_id = "default"
    
    if workflow_id not in _workflow_instances:
        _workflow_instances[workflow_id] = LangGraphWorkflow()
    
    return _workflow_instances[workflow_id]


def create_research_workflow(config: Optional[ResearchWorkflowConfig] = None) -> LangGraphWorkflow:
    """创建新的研究工作流"""
    return LangGraphWorkflow(config=config)
