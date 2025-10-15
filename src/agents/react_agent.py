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
from .prompt_templates import get_prompt_engine

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

        # 初始化提示词模板引擎
        self.prompt_engine = get_prompt_engine()

        # 思维链历史记录
        self.reasoning_history = []

        # 任务分解结果
        self.task_substeps = []

        logger.info(f"ReAct Agent {self.name} initialized with tools: {config.tools}")
    
    async def reply(self, msg: Msg, **kwargs) -> Msg:
        """ReAct 循环：推理 -> 行动 -> 观察 (增强版)"""
        self.current_iteration = 0
        self.reasoning_history = []

        # 检查是否需要任务分解 (策略三：将复杂任务分解为简单的子任务)
        task_content = msg.content
        if self._is_complex_task(task_content):
            self.task_substeps = self.decompose_complex_task(task_content)
            logger.info(f"Task decomposed into {len(self.task_substeps)} substeps")

        # 构建初始上下文
        context = await self._build_enhanced_context(msg)

        # ReAct 循环
        while self.current_iteration < self.max_iterations:
            self.current_iteration += 1

            # 推理阶段 (增强版 - 包含思维链)
            reasoning_result = await self._enhanced_reasoning(context)

            # 记录推理历史
            self.reasoning_history.append({
                "iteration": self.current_iteration,
                "reasoning": reasoning_result.get("reasoning", ""),
                "use_tool": reasoning_result.get("use_tool", False),
                "tool_name": reasoning_result.get("tool_name", ""),
                "confidence": reasoning_result.get("confidence", 0.0)
            })

            # 检查是否需要使用工具
            if reasoning_result.get("use_tool"):
                # 行动阶段
                action_result = await self._acting(reasoning_result)

                # 观察阶段
                observation = await self._observing(action_result)

                # 更新上下文
                context = await self._update_enhanced_context(
                    context, reasoning_result, action_result, observation
                )

                # 检查是否完成
                if action_result.get("finished"):
                    break
            else:
                # 直接返回推理结果
                break

        # 生成最终回复 (使用思维链总结)
        final_response = await self._generate_final_response(reasoning_result)

        return Msg(
            name=self.name,
            content=final_response,
            role="assistant",
            metadata={
                "iterations": self.current_iteration,
                "reasoning": reasoning_result.get("reasoning", ""),
                "tools_used": reasoning_result.get("tools_used", []),
                "reasoning_history": self.reasoning_history,
                "task_substeps": self.task_substeps,
                "confidence_score": self._calculate_confidence_score()
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

    # === 增强推理方法 (基于 tech.txt 策略) ===

    def _is_complex_task(self, task_content: str) -> bool:
        """判断是否为复杂任务 (策略三：任务分解)"""
        # 简单的复杂任务检测逻辑
        complexity_indicators = [
            "研究", "分析", "设计", "实现", "创建", "开发", "计划", "规划",
            "search", "research", "analyze", "design", "implement", "create", "develop"
        ]

        # 长度检查
        if len(task_content) > 200:
            return True

        # 关键词检查
        task_lower = task_content.lower()
        return any(indicator in task_lower for indicator in complexity_indicators)

    async def _enhanced_reasoning(self, context: str) -> Dict[str, Any]:
        """增强推理阶段 (策略一：思维链提示)"""
        # 构建增强推理提示
        reasoning_prompt = self._build_enhanced_reasoning_prompt(context)

        # 调用 LLM
        messages = [
            {"role": "system", "content": self.build_enhanced_system_prompt()},
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
            logger.error(f"Enhanced reasoning error: {e}")
            return {
                "use_tool": False,
                "response": f"推理过程中发生错误: {str(e)}",
                "reasoning": "推理失败",
                "confidence": 0.0
            }

    def _build_enhanced_reasoning_prompt(self, context: str) -> str:
        """构建增强推理提示 (策略一：思维链提示)"""
        reasoning_guidance = self._get_reasoning_guidance()

        return f"""
{context}

{reasoning_guidance}

请按照以下格式进行推理和决策:

## 推理过程 (思维链)
1. **理解问题**: 明确当前任务的核心目标和要求
2. **分析信息**: 识别可用的信息、工具和约束条件
3. **制定计划**: 确定具体的执行步骤和方法
4. **评估选项**: 考虑不同的可能性和其后果
5. **做出决策**: 选择最佳行动方案

## 输出格式
请以 JSON 格式返回结果:
{{
    "reasoning": "详细的推理过程，包含上述5个步骤",
    "use_tool": true/false,
    "tool_name": "工具名称（如果需要）",
    "tool_args": {{"参数": "值"}},
    "response": "最终回答或行动说明",
    "finished": true/false,
    "confidence": 0.9
}}

请确保推理过程详细、逻辑清晰、决策合理。
"""

    def _get_reasoning_guidance(self) -> str:
        """获取推理指导 (基于配置的推理模式)"""
        if self.config.reasoning_mode == "chain_of_thought":
            return """
## 思维链推理指导
作为{self.config.role}，请按照以下步骤进行详细推理：

对于每个推理步骤，请说明：
- 你在思考什么
- 为什么这样思考
- 如何得出下一步行动
- 可能的风险和应对措施

请确保推理链条完整、逻辑严密、可追溯。
"""
        elif self.config.reasoning_mode == "step_by_step":
            return """
## 分步骤推理指导
请按照清晰的步骤进行推理：

1. 明确当前任务
2. 分析可用资源
3. 制定执行计划
4. 逐步实施
5. 验证结果

每个步骤应该简洁明确，逻辑清晰。
"""
        else:  # direct
            return """
## 直接推理指导
请直接给出推理结果和行动决策，保持简洁高效。
"""

    async def _build_enhanced_context(self, msg: Msg) -> str:
        """构建增强上下文 (策略二：提供参考资料)"""
        # 获取历史对话
        history = self.memory.get_conversation_text(limit=5)

        # 获取可用工具
        available_tools = self._get_available_tools()

        # 任务分解信息
        task_info = ""
        if self.task_substeps:
            task_info = f"""
## 任务分解 (策略三)
当前任务已分解为 {len(self.task_substeps)} 个子任务:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(self.task_substeps))}

当前正在执行的子任务: {self.task_substeps[min(self.current_iteration-1, len(self.task_substeps)-1)] if self.current_iteration > 0 else "准备开始"}
"""

        # 使用分隔符标示不同部分 (策略一)
        context = f"""
## 当前任务
{msg.content}

{task_info}

## 历史对话
{history}

## 可用工具
{available_tools}

## 推理模式
{self.config.reasoning_mode}

---

请使用 ReAct 模式进行推理和行动，遵循上述推理指导。
"""
        return context

    async def _update_enhanced_context(
        self,
        context: str,
        reasoning: Dict,
        action: Dict,
        observation: str
    ) -> str:
        """更新增强上下文"""
        # 更新任务进度
        progress_info = ""
        if self.task_substeps and self.current_iteration <= len(self.task_substeps):
            current_step = self.task_substeps[self.current_iteration - 1]
            progress_info = f"## 任务进度\\n当前步骤: {current_step} (第 {self.current_iteration}/{len(self.task_substeps)} 步)\\n"

        update = f"""
---

## 第 {self.current_iteration} 轮推理

### 推理过程
{reasoning.get('reasoning', '')}

### 行动执行
{f"使用工具: {action.get('tool_name', '')}" if action.get('tool_name') else "无需使用工具"}

### 观察结果
{observation}

{progress_info}
"""
        return context + update

    async def _generate_final_response(self, reasoning_result: Dict[str, Any]) -> str:
        """生成最终回复 (使用思维链总结)"""
        # 构建总结提示
        summary_prompt = f"""
请基于以下推理历史生成最终的综合回复：

## 推理历史
{json.dumps(self.reasoning_history, ensure_ascii=False, indent=2)}

## 任务分解步骤
{json.dumps(self.task_substeps, ensure_ascii=False, indent=2)}

## 最新推理结果
{json.dumps(reasoning_result, ensure_ascii=False, indent=2)}

请生成一个清晰、完整、有逻辑的最终回复，包括：
1. 任务完成情况总结
2. 主要发现和结果
3. 如有必要，下一步建议

回复应该体现 {self.config.role} 的专业水准，使用 {self.config.language_style} 风格。
"""

        try:
            messages = [
                {"role": "system", "content": self.build_enhanced_system_prompt()},
                {"role": "user", "content": summary_prompt}
            ]

            response = await self.llm_router.route_and_chat(
                task_type="summary",
                messages=messages,
                temperature=0.3,  # 低温度确保总结稳定
                max_tokens=self.config.max_tokens
            )

            return response.get("content", "生成回复失败")

        except Exception as e:
            logger.error(f"Final response generation error: {e}")
            # 回退到原始推理结果
            return reasoning_result.get("response", "处理完成，但生成总结时遇到问题。")

    def _calculate_confidence_score(self) -> float:
        """计算置信度分数"""
        if not self.reasoning_history:
            return 0.0

        # 基于多个因素计算置信度
        confidence_factors = []

        # 1. 推理轮数（适中的轮数通常更好）
        if self.current_iteration <= 3:
            confidence_factors.append(0.8)
        elif self.current_iteration <= 6:
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.7)

        # 2. 工具使用成功率
        successful_steps = sum(1 for step in self.reasoning_history if step.get("use_tool") == False or step.get("confidence", 0) > 0.7)
        if self.reasoning_history:
            success_rate = successful_steps / len(self.reasoning_history)
            confidence_factors.append(success_rate)

        # 3. 任务完成度
        if self.task_substeps:
            completion_rate = min(self.current_iteration, len(self.task_substeps)) / len(self.task_substeps)
            confidence_factors.append(completion_rate)

        # 4. 最新推理的置信度
        if self.reasoning_history:
            latest_confidence = self.reasoning_history[-1].get("confidence", 0.5)
            confidence_factors.append(latest_confidence)

        # 计算加权平均
        if confidence_factors:
            return sum(confidence_factors) / len(confidence_factors)
        return 0.5
