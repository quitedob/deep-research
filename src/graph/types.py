# -*- coding: utf-8 -*-
"""
AgentWork 工作流状态类型定义
定义多代理系统的状态结构
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

try:
    from langgraph.graph import MessagesState
except ImportError:
    # 如果没有安装langgraph，提供基础实现
    class MessagesState:
        def __init__(self):
            self.messages = []


class StepType(Enum):
    """执行步骤类型"""
    RESEARCH = "research"  # 研究步骤
    PROCESSING = "processing"  # 处理步骤
    ANALYSIS = "analysis"  # 分析步骤
    SYNTHESIS = "synthesis"  # 综合步骤


@dataclass
class Step:
    """执行步骤"""
    title: str
    description: str
    step_type: StepType
    execution_res: Optional[str] = None
    tools_needed: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class Plan:
    """研究计划"""
    title: str
    description: str
    steps: List[Step] = field(default_factory=list)
    has_enough_context: bool = False
    estimated_time: Optional[int] = None  # 预计执行时间（分钟）


@dataclass
class Resource:
    """资源定义"""
    name: str
    type: str  # "document", "url", "database" etc.
    path: Optional[str] = None
    url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class State(MessagesState):
    """AgentWork系统状态，扩展MessagesState"""
    
    def __init__(self):
        super().__init__()
        # 运行时变量
        self.locale: str = "zh-CN"
        self.research_topic: str = ""
        self.observations: List[str] = []
        self.resources: List[Resource] = []
        self.plan_iterations: int = 0
        self.current_plan: Optional[Union[Plan, str]] = None
        self.final_report: str = ""
        self.auto_accepted_plan: bool = False
        self.enable_background_investigation: bool = True
        self.background_investigation_results: Optional[str] = None
        
        # 会话管理
        self.session_id: Optional[str] = None
        self.user_id: Optional[str] = None
        
        # 执行状态
        self.current_step_index: int = 0
        self.execution_status: str = "pending"  # pending, running, completed, failed
        self.error_message: Optional[str] = None
        
        # 缓存和临时数据
        self.search_cache: Dict[str, Any] = {}
        self.tool_outputs: Dict[str, Any] = {}
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "messages": getattr(self, 'messages', []),
            "locale": self.locale,
            "research_topic": self.research_topic,
            "observations": self.observations,
            "resources": [
                {
                    "name": r.name,
                    "type": r.type,
                    "path": r.path,
                    "url": r.url,
                    "metadata": r.metadata
                } for r in self.resources
            ],
            "plan_iterations": self.plan_iterations,
            "current_plan": self.current_plan,
            "final_report": self.final_report,
            "auto_accepted_plan": self.auto_accepted_plan,
            "enable_background_investigation": self.enable_background_investigation,
            "background_investigation_results": self.background_investigation_results,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "current_step_index": self.current_step_index,
            "execution_status": self.execution_status,
            "error_message": self.error_message,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "State":
        """从字典创建状态对象"""
        state = cls()
        
        # 设置基础属性
        for key, value in data.items():
            if key == "resources":
                # 特殊处理resources
                state.resources = [
                    Resource(
                        name=r["name"],
                        type=r["type"],
                        path=r.get("path"),
                        url=r.get("url"),
                        metadata=r.get("metadata", {})
                    ) for r in value
                ]
            elif hasattr(state, key):
                setattr(state, key, value)
        
        return state
    
    def add_observation(self, observation: str):
        """添加观察记录"""
        self.observations.append(observation)
    
    def add_resource(self, resource: Resource):
        """添加资源"""
        self.resources.append(resource)
    
    def update_plan(self, plan: Union[Plan, str]):
        """更新当前计划"""
        self.current_plan = plan
        self.plan_iterations += 1
    
    def set_final_report(self, report: str):
        """设置最终报告"""
        self.final_report = report
        self.execution_status = "completed"
    
    def set_error(self, error_message: str):
        """设置错误状态"""
        self.error_message = error_message
        self.execution_status = "failed" 