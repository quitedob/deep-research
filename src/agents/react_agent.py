# -*- coding: utf-8 -*-
"""
ReAct Agent 实现 - 参考 AgentScope 的 ReAct 模式
"""
import json
import logging
from typing import Any, Dict, List, Optional

from .base_agent import AgentBase, AgentConfig
from ..message import Msg, ToolUseBlock, ToolResultBlock, TextBlock
from ..llms.router import SmartModelRouter
from ..tools.tool_registry import ToolRegistry
from ..config.config_loader import get_settings

logger = logging.getLogger(__name__)


class ReActAgent(AgentBase):
    """ReAct (Reasoning + Acting) Agent - 参考 AgentScope"""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # 初始化 LLM 路由器
        settings = get_settings()
        self.llm_router = SmartModelRouter.from_conf(settings.BASE_DIR / "conf.yaml")
        
        # 工具注册表
        self.tool_registry = ToolRegistry()
        
        # ReAct 配置
        self.max_iterations = 10
        self.current_iteration = 0
        
        logger.info(f"ReAct Agent {self.name} initialized with tools: {config.tools}")
    
    async def reply(self, msg: Msg, **kwargs) -> Msg:
        """ReAct 循环：推理 -> 行动 -> 观察"""
        self.current_iteration = 0
        
        # 构建初始上下文
        context = await self._build_context(msg)
        
        # ReAct 循环
        while self.current_iteration < self.max_iterations:
            self.current_iteration += 1
            
            # 推理阶段
            reasoning_result = await self._reasoning(context)
            
            # 检查是否需要使用工具
            if reasoning_result.get("use_tool"):
                # 行动阶段
                action_result = await self._acting(reasoning_result)
                
                # 观察阶段
                observation = await self._observing(action_result)
                
                # 更新上下文
                context = await self._update_context(
                    context, reasoning_result, action_result, observation
                )
                
                # 检查是否完成
                if action_result.get("finished"):
                    break
            else:
                # 直接返回推理结果
                break
        
        # 生成最终回复
        final_response = reasoning_result.get("response", "抱歉，我无法完成这个任务。")
        
        return Msg(
            name=self.name,
            content=final_response,
            role="assistant",
            metadata={
                "iterations": self.current_iteration,
                "reasoning": reasoning_result.get("reasoning", ""),
                "tools_used": reasoning_result.get("tools_used", [])
            }
        )
    
    async def _reasoning(self, context: str) -> Dict[str, Any]:
        """推理阶段"""
        # 构建推理提示
        reasoning_prompt = self._build_reasoning_prompt(context)
        
        # 调用 LLM
        messages = [
            {"role": "system", "content": self.config.system_prompt},
            {"role": "user", "content": reasoning_prompt}
        ]
        
        try:
            response = await self.llm_router.route_and_chat(
                task_type="reasoning",
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            # 解析推理结果
            return self._parse_reasoning_response(response.get("content", ""))
        
        except Exception as e:
            logger.error(f"Reasoning error: {e}")
            return {
                "use_tool": False,
                "response": f"推理过程中发生错误: {str(e)}",
                "reasoning": "推理失败"
            }
    
    async def _acting(self, reasoning_result: Dict[str, Any]) -> Dict[str, Any]:
        """行动阶段"""
        tool_name = reasoning_result.get("tool_name")
        tool_args = reasoning_result.get("tool_args", {})
        
        if not tool_name:
            return {"finished": True, "result": "没有指定工具"}
        
        # 获取工具
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            return {
                "finished": True,
                "result": f"工具 {tool_name} 不存在",
                "error": f"Tool {tool_name} not found"
            }
        
        try:
            # 执行工具
            result = await tool.aexecute(**tool_args)
            return {
                "finished": reasoning_result.get("finished", False),
                "result": result.data if result.success else result.error,
                "tool_name": tool_name,
                "tool_args": tool_args,
                "success": result.success
            }
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {
                "finished": True,
                "result": f"工具执行失败: {str(e)}",
                "error": str(e)
            }
    
    async def _observing(self, action_result: Dict[str, Any]) -> str:
        """观察阶段"""
        if action_result.get("success"):
            observation = f"工具 {action_result.get('tool_name')} 执行成功。结果: {action_result.get('result')}"
        else:
            observation = f"工具 {action_result.get('tool_name')} 执行失败。错误: {action_result.get('result')}"
        
        return observation
    
    async def _build_context(self, msg: Msg) -> str:
        """构建上下文"""
        # 获取历史对话
        history = self.memory.get_conversation_text(limit=5)
        
        # 获取可用工具
        available_tools = self._get_available_tools()
        
        context = f"""
当前任务: {msg.content}

历史对话:
{history}

可用工具:
{available_tools}

请使用 ReAct 模式进行推理和行动。
"""
        return context
    
    async def _update_context(
        self, 
        context: str, 
        reasoning: Dict, 
        action: Dict, 
        observation: str
    ) -> str:
        """更新上下文"""
        update = f"""
推理: {reasoning.get('reasoning', '')}
行动: 使用工具 {action.get('tool_name', '')}
观察: {observation}
"""
        return context + update
    
    def _build_reasoning_prompt(self, context: str) -> str:
        """构建推理提示"""
        return f"""
{context}

请按照以下格式进行推理:
思考: [你的推理过程]
行动: [是否需要使用工具，如果需要，指定工具名称和参数]
回答: [如果不需要工具，直接给出最终回答]

请以 JSON 格式返回结果:
{{
    "reasoning": "你的推理过程",
    "use_tool": true/false,
    "tool_name": "工具名称",
    "tool_args": {{"参数": "值"}},
    "response": "最终回答",
    "finished": true/false
}}
"""
    
    def _parse_reasoning_response(self, response: str) -> Dict[str, Any]:
        """解析推理响应"""
        try:
            # 尝试解析 JSON
            if response.strip().startswith("{"):
                return json.loads(response)
            
            # 如果不是 JSON，尝试提取信息
            result = {
                "use_tool": False,
                "response": response,
                "reasoning": response,
                "finished": True
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to parse reasoning response: {e}")
            return {
                "use_tool": False,
                "response": response,
                "reasoning": "解析失败",
                "finished": True
            }
    
    def _get_available_tools(self) -> str:
        """获取可用工具描述"""
        tools_info = []
        for tool_name in self.config.tools:
            tool = self.tool_registry.get_tool(tool_name)
            if tool:
                schema = tool.get_schema()
                tools_info.append(f"- {tool_name}: {schema.get('description', '无描述')}")
        
        return "\n".join(tools_info) if tools_info else "无可用工具"
