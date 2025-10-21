# -*- coding: utf-8 -*-
"""
Agent 基础类 - 参考 AgentScope 的 AgentBase
"""
import asyncio
import logging
try:
    import shortuuid
    SHORTUUID_AVAILABLE = True
except ImportError:
    SHORTUUID_AVAILABLE = False
    import uuid
    shortuuid = None
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import OrderedDict

from ..message import Msg
from ..memory.conversation_buffer import ConversationBuffer

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Agent 配置类 - 基于 tech.txt Prompt 工程"""
    name: str
    role: str
    system_prompt: str
    model_name: str = "kimi"
    max_tokens: int = 4000
    temperature: float = 0.7
    capabilities: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    memory_type: str = "conversation"
    max_memory_size: int = 100

    # Prompt 工程字段 (基于 tech.txt)
    role_definition: str = ""  # 角色设定
    language_style: str = "professional"  # 语言风格
    task_mode: str = "analysis"  # 任务模式
    behavior_guidance: List[str] = field(default_factory=list)  # 具体行为指导
    few_shot_examples: List[Dict[str, Any]] = field(default_factory=list)  # 少样本学习示例
    output_format: str = "natural"  # 输出格式: natural, json, markdown
    reasoning_mode: str = "step_by_step"  # 推理模式: direct, step_by_step, chain_of_thought
    context_requirements: List[str] = field(default_factory=list)  # 上下文要求
    quality_criteria: List[str] = field(default_factory=list)  # 质量标准


class AgentBase(ABC):
    """Agent 基础类 - 参考 AgentScope 设计"""
    
    supported_hook_types: list[str] = [
        "pre_reply",
        "post_reply",
        "pre_observe",
        "post_observe",
    ]
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.id = shortuuid.uuid() if SHORTUUID_AVAILABLE else str(uuid.uuid4())
        self.name = config.name
        self.role = config.role
        
        # 初始化记忆系统
        self.memory = ConversationBuffer(max_messages=config.max_memory_size)
        
        # Hook 系统
        self._instance_pre_reply_hooks: Dict[str, Callable] = OrderedDict()
        self._instance_post_reply_hooks: Dict[str, Callable] = OrderedDict()
        self._instance_pre_observe_hooks: Dict[str, Callable] = OrderedDict()
        self._instance_post_observe_hooks: Dict[str, Callable] = OrderedDict()
        
        # 状态管理
        self._is_active = True
        self._last_activity = datetime.now()
        self._disable_console_output = False
        
        logger.info(f"Agent {self.name} ({self.id}) initialized")
    
    @abstractmethod
    async def reply(self, msg: Msg, **kwargs) -> Msg:
        """生成回复"""
        pass
    
    async def observe(self, msg: Msg | list[Msg] | None) -> None:
        """观察消息"""
        # 执行 pre-observe hooks
        for hook in self._instance_pre_observe_hooks.values():
            try:
                await hook(self, msg)
            except Exception as e:
                logger.error(f"Pre-observe hook error: {e}")
        
        # 添加到记忆
        if isinstance(msg, list):
            for m in msg:
                await self.memory.add_message(m.role, m.content)
        elif msg:
            await self.memory.add_message(msg.role, msg.content)
        
        self._last_activity = datetime.now()
        
        # 执行 post-observe hooks
        for hook in self._instance_post_observe_hooks.values():
            try:
                await hook(self, msg)
            except Exception as e:
                logger.error(f"Post-observe hook error: {e}")
    
    async def __call__(self, msg: Msg, **kwargs) -> Msg:
        """调用 Agent"""
        # 执行 pre-reply hooks
        for hook in self._instance_pre_reply_hooks.values():
            try:
                msg = await hook(self, msg) or msg
            except Exception as e:
                logger.error(f"Pre-reply hook error: {e}")
        
        # 观察输入消息
        await self.observe(msg)
        
        # 生成回复
        reply_msg = await self.reply(msg, **kwargs)
        
        # 执行 post-reply hooks
        for hook in self._instance_post_reply_hooks.values():
            try:
                reply_msg = await hook(self, reply_msg) or reply_msg
            except Exception as e:
                logger.error(f"Post-reply hook error: {e}")
        
        # 观察回复消息
        await self.observe(reply_msg)
        
        return reply_msg
    
    def register_hook(self, hook_type: str, name: str, hook: Callable):
        """注册 Hook"""
        if hook_type not in self.supported_hook_types:
            raise ValueError(f"Invalid hook type: {hook_type}")
        
        hook_dict = getattr(self, f"_instance_{hook_type}_hooks")
        hook_dict[name] = hook
        logger.info(f"Registered {hook_type} hook: {name}")
    
    def remove_hook(self, hook_type: str, name: str):
        """移除 Hook"""
        hook_dict = getattr(self, f"_instance_{hook_type}_hooks")
        if name in hook_dict:
            del hook_dict[name]
            logger.info(f"Removed {hook_type} hook: {name}")
    
    def get_memory_summary(self) -> str:
        """获取记忆摘要"""
        return self.memory.get_conversation_text()
    
    def clear_memory(self):
        """清空记忆"""
        self.memory.clear()
        logger.info(f"Cleared memory for agent {self.name}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取 Agent 状态"""
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "is_active": self._is_active,
            "last_activity": self._last_activity.isoformat(),
            "memory_size": self.memory.get_message_count(),
            "capabilities": self.config.capabilities,
            "tools": self.config.tools
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "config": {
                "name": self.config.name,
                "role": self.config.role,
                "system_prompt": self.config.system_prompt,
                "model_name": self.config.model_name,
                "capabilities": self.config.capabilities,
                "tools": self.config.tools
            },
            "status": self.get_status()
        }
    
    def set_console_output_enabled(self, enabled: bool) -> None:
        """启用或禁用控制台输出"""
        self._disable_console_output = not enabled

    def build_enhanced_system_prompt(self) -> str:
        """构建增强的系统提示词 (基于 tech.txt 策略)"""
        prompt_parts = []

        # 1. 角色定义 (策略一：让 GLM 进行角色扮演)
        if self.config.role_definition:
            prompt_parts.append(f"角色定义: {self.config.role_definition}")

        # 2. 基础系统提示
        if self.config.system_prompt:
            prompt_parts.append(f"核心任务: {self.config.system_prompt}")

        # 3. 语言风格 (策略一：提供具体的细节要求)
        style_guidance = {
            "professional": "专业、客观、数据驱动",
            "casual": "友好、自然、易于理解",
            "academic": "学术严谨、引用准确、逻辑清晰",
            "creative": "创新、生动、富有想象力",
            "technical": "技术精确、术语准确、实用导向"
        }
        if self.config.language_style in style_guidance:
            prompt_parts.append(f"语言风格: {style_guidance[self.config.language_style]}")

        # 4. 行为指导 (策略一：具体行为指导)
        if self.config.behavior_guidance:
            guidance_text = "行为指导:\n" + "\n".join(f"- {guidance}" for guidance in self.config.behavior_guidance)
            prompt_parts.append(guidance_text)

        # 5. 推理模式 (策略一：思维链提示)
        reasoning_guidance = {
            "direct": "直接给出答案，无需详细推理过程",
            "step_by_step": "分步骤解答问题，展示推理过程",
            "chain_of_thought": "详细展示思考链条，包括每个推理步骤和决策依据"
        }
        if self.config.reasoning_mode in reasoning_guidance:
            prompt_parts.append(f"推理要求: {reasoning_guidance[self.config.reasoning_mode]}")

        # 6. 输出格式
        format_guidance = {
            "natural": "自然语言回答",
            "json": "JSON格式结构化回答",
            "markdown": "Markdown格式，使用标题、列表等结构化元素"
        }
        if self.config.output_format in format_guidance:
            prompt_parts.append(f"输出格式: {format_guidance[self.config.output_format]}")

        # 7. 上下文要求
        if self.config.context_requirements:
            context_text = "上下文要求:\n" + "\n".join(f"- {req}" for req in self.config.context_requirements)
            prompt_parts.append(context_text)

        # 8. 质量标准
        if self.config.quality_criteria:
            quality_text = "质量标准:\n" + "\n".join(f"- {criteria}" for criteria in self.config.quality_criteria)
            prompt_parts.append(quality_text)

        # 9. 少样本示例 (策略一：少样本学习)
        if self.config.few_shot_examples:
            examples_text = "示例参考:\n"
            for i, example in enumerate(self.config.few_shot_examples, 1):
                examples_text += f"\n示例 {i}:\n"
                if "input" in example and "output" in example:
                    examples_text += f"输入: {example['input']}\n"
                    examples_text += f"输出: {example['output']}\n"
                elif "example" in example:
                    examples_text += f"{example['example']}\n"
            prompt_parts.append(examples_text)

        # 使用分隔符标示不同部分 (策略一：使用分隔符)
        return "\n\n---\n\n".join(prompt_parts)

    def format_with_examples(self, content: str, examples: List[Dict] = None) -> str:
        """使用少样本学习格式化内容"""
        if not examples:
            examples = self.config.few_shot_examples

        if not examples:
            return content

        formatted_content = "请参考以下示例:\n\n"
        for i, example in enumerate(examples, 1):
            formatted_content += f"示例 {i}:\n"
            if "input" in example and "output" in example:
                formatted_content += f"输入: {example['input']}\n"
                formatted_content += f"输出: {example['output']}\n\n"
            elif "example" in example:
                formatted_content += f"{example['example']}\n\n"

        formatted_content += "---\n\n"
        formatted_content += f"现在请处理以下内容:\n\n{content}"

        return formatted_content

    def apply_reasoning_chain(self, task: str) -> str:
        """应用思维链推理 (策略一：思维链提示)"""
        if self.config.reasoning_mode != "chain_of_thought":
            return task

        reasoning_template = f"""
作为一个{self.config.role}，你需要对以下任务进行逐步推理：

任务: {task}

请按以下格式进行推理：

步骤1: [理解问题] - 明确任务要求和目标
步骤2: [分析信息] - 识别关键信息和约束条件
步骤3: [制定计划] - 确定解决步骤和方法
步骤4: [执行推理] - 逐步推导和计算
步骤5: [验证结果] - 检查答案的合理性和完整性
步骤6: [得出结论] - 总结最终答案

对于每个步骤，请详细说明你的思考过程，包括：
- 你在思考什么
- 为什么这样思考
- 如何得出下一步行动

最终请以清晰的格式给出答案。
"""
        return reasoning_template.strip()

    def integrate_reference_materials(self, query: str, materials: List[Dict]) -> str:
        """集成参考资料 (策略二：提供参考资料)"""
        if not materials:
            return query

        # 使用分隔符标示不同的输入部分 (策略一)
        formatted_materials = []
        for i, material in enumerate(materials, 1):
            material_text = f"参考资料 {i}:\n"
            if "title" in material:
                material_text += f"标题: {material['title']}\n"
            if "content" in material:
                material_text += f"内容: {material['content']}\n"
            if "source" in material:
                material_text += f"来源: {material['source']}\n"
            if "url" in material:
                material_text += f"链接: {material['url']}\n"
            formatted_materials.append(material_text)

        materials_section = "\n\n---\n\n" + "\n\n".join(formatted_materials)

        enhanced_query = f"""
请基于以下参考资料回答问题：

问题: {query}

{materials_section}

请根据提供的参考资料，准确、全面地回答问题。如果参考资料不足，请明确指出。
"""

        return enhanced_query.strip()

    def decompose_complex_task(self, task: str) -> List[str]:
        """将复杂任务分解为简单的子任务 (策略三：使用增强任务分解框架)"""
        try:
            # 导入任务分解器
            from .task_decomposition import get_task_decomposer

            # 使用任务分解器进行分解
            decomposer = get_task_decomposer()
            decomposition = decomposer.decompose_task(task)

            # 记录分解结果
            logger.info(f"Task '{task[:50]}...' decomposed into {len(decomposition.subtasks)} subtasks")
            logger.info(f"Task type: {decomposition.task_type.value}, Complexity: {decomposition.complexity.value}")

            # 返回子任务标题列表
            return [subtask.title for subtask in decomposition.subtasks]

        except Exception as e:
            logger.error(f"Enhanced task decomposition failed: {e}")
            # 回退到简单分解逻辑
            return self._simple_task_decomposition(task)

    def _simple_task_decomposition(self, task: str) -> List[str]:
        """简单任务分解 (回退方案)"""
        task_lower = task.lower()

        # 检测任务类型
        task_indicators = {
            "research": ["研究", "调查", "分析", "查找", "search", "research"],
            "analysis": ["分析", "比较", "评估", "calculate", "compute", "analyze"],
            "writing": ["写", "生成", "创建", "撰写", "write", "generate"],
            "coding": ["代码", "编程", "算法", "程序", "code", "program"],
            "planning": ["计划", "规划", "设计", "方案", "plan", "design"]
        }

        detected_tasks = []
        for task_type, keywords in task_indicators.items():
            if any(keyword in task_lower for keyword in keywords):
                detected_tasks.append(task_type)

        # 生成子任务
        subtasks = []

        if "research" in detected_tasks:
            subtasks.extend([
                "明确研究目标和范围",
                "收集相关信息和数据",
                "分析和验证信息来源",
                "整理研究发现"
            ])

        if "analysis" in detected_tasks:
            subtasks.extend([
                "理解分析目标和要求",
                "收集分析所需数据",
                "执行数据分析或计算",
                "验证分析结果",
                "生成分析报告"
            ])

        if "writing" in detected_tasks:
            subtasks.extend([
                "确定写作目标和受众",
                "收集和组织写作材料",
                "创建大纲和结构",
                "撰写初稿",
                "完善和编辑内容"
            ])

        if "coding" in detected_tasks:
            subtasks.extend([
                "理解编程需求",
                "设计算法和架构",
                "编写代码实现",
                "测试和调试代码",
                "优化和完善代码"
            ])

        # 如果没有检测到特定任务类型，使用通用分解
        if not subtasks:
            subtasks = [
                "理解任务要求和目标",
                "制定执行计划",
                "执行核心任务",
                "验证和检查结果",
                "完善最终输出"
            ]

        return subtasks

    def get_enhanced_task_decomposition(self, task: str, requirements: Optional[Dict] = None):
        """获取增强的任务分解结果"""
        try:
            from .task_decomposition import get_task_decomposer

            decomposer = get_task_decomposer()
            decomposition = decomposer.decompose_task(task, requirements)
            execution_plan = decomposer.get_execution_plan(decomposition)

            return {
                "decomposition": decomposition,
                "execution_plan": execution_plan,
                "success": True
            }

        except Exception as e:
            logger.error(f"Enhanced task decomposition failed: {e}")
            return {
                "simple_subtasks": self._simple_task_decomposition(task),
                "success": False,
                "error": str(e)
            }
