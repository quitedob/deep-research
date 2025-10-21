# -*- coding: utf-8 -*-
"""
Prompt 模板系统 - 基于 tech.txt Prompt 工程策略
提供各种任务类型的标准提示词模板
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class PromptTemplate:
    """提示词模板"""
    name: str
    template: str
    variables: List[str]
    description: str
    examples: List[Dict[str, Any]] = None
    reasoning_mode: str = "step_by_step"
    output_format: str = "natural"


class PromptTemplateEngine:
    """提示词模板引擎 - 基于 tech.txt 策略"""

    def __init__(self):
        self.templates = {}
        self._initialize_templates()

    def _initialize_templates(self):
        """初始化预定义模板"""

        # 1. 系统提示词模板 (策略一：定义 System Prompt)
        self.templates["system_prompt"] = PromptTemplate(
            name="system_prompt",
            template="""角色定义: {role_definition}
核心任务: {core_task}
语言风格: {language_style}
行为指导:
{behavior_guidance}
推理要求: {reasoning_mode}
输出格式: {output_format}
质量标准:
{quality_criteria}""",
            variables=["role_definition", "core_task", "language_style", "behavior_guidance", "reasoning_mode", "output_format", "quality_criteria"],
            description="标准系统提示词模板"
        )

        # 2. 研究任务模板
        self.templates["research_task"] = PromptTemplate(
            name="research_task",
            template="""作为一个专业的研究员，请对以下主题进行深度研究：

研究主题: {topic}

研究要求:
- 收集多源信息并进行交叉验证
- 分析信息的可靠性和权威性
- 提供客观、准确的研究结果
- 按逻辑结构组织研究内容

研究步骤:
1. 理解研究需求和目标
2. 制定搜索策略
3. 收集相关信息和数据
4. 分析和验证信息
5. 综合生成研究报告

请按照以下格式输出：
## 研究概述
## 主要发现
## 详细分析
## 结论和建议
## 参考资料""",
            variables=["topic"],
            description="研究任务模板",
            reasoning_mode="step_by_step",
            output_format="markdown",
            examples=[
                {
                    "input": "研究人工智能在教育领域的应用",
                    "output": "详细的AI教育应用研究报告"
                }
            ]
        )

        # 3. 分析任务模板 (策略一：思维链提示)
        self.templates["analysis_task"] = PromptTemplate(
            name="analysis_task",
            template="""作为一个专业的分析师，请对以下问题进行逐步分析：

分析对象: {subject}

请按以下步骤进行分析：

步骤1: [理解问题] - 明确分析目标和要求
步骤2: [信息收集] - 识别关键数据和相关信息
步骤3: [数据处理] - 对数据进行整理和预处理
步骤4: [深入分析] - 运用分析方法和工具
步骤5: [结果验证] - 检查分析结果的合理性
步骤6: [得出结论] - 总结分析发现和洞察

对于每个步骤，请详细说明：
- 你在思考什么
- 为什么这样思考
- 如何得出下一步行动

最终请以清晰的格式给出分析结果。

分析要求:
- 数据驱动，基于事实进行分析
- 逻辑清晰，推理过程透明
- 结论明确，有充分依据
- 客观公正，避免主观偏见""",
            variables=["subject"],
            description="分析任务模板",
            reasoning_mode="chain_of_thought",
            output_format="structured"
        )

        # 4. 编程任务模板
        self.templates["coding_task"] = PromptTemplate(
            name="coding_task",
            template="""作为一个专业的程序员，请完成以下编程任务：

任务要求: {requirements}

请按以下步骤完成：

1. 需求分析 - 理解功能需求和约束条件
2. 算法设计 - 选择合适的数据结构和算法
3. 代码实现 - 编写高质量的代码
4. 测试验证 - 确保代码正确性
5. 优化完善 - 提高代码性能和可读性

代码要求:
- 代码清晰易读，有适当的注释
- 遵循编程最佳实践
- 考虑边界条件和异常处理
- 提供使用示例
- 包含必要的测试用例

请提供完整的代码实现，并附上使用说明。""",
            variables=["requirements"],
            description="编程任务模板",
            reasoning_mode="step_by_step",
            output_format="code"
        )

        # 5. 写作任务模板
        self.templates["writing_task"] = PromptTemplate(
            name="writing_task",
            template="""作为一个专业的内容创作者，请根据以下要求创建内容：

写作主题: {topic}
目标受众: {audience}
内容类型: {content_type}
字数要求: {word_count}

写作要求:
- 结构清晰，逻辑连贯
- 语言生动，表达准确
- 符合目标受众的理解水平
- 内容有价值，信息准确

请按照标准格式组织内容，包括标题、引言、正文和结论。

质量控制:
- 检查语法和拼写错误
- 确保事实准确性
- 提高表达流畅度
- 增强内容吸引力""",
            variables=["topic", "audience", "content_type", "word_count"],
            description="写作任务模板",
            reasoning_mode="direct",
            output_format="natural"
        )

        # 6. 问答任务模板 (策略二：提供参考资料)
        self.templates["qa_with_references"] = PromptTemplate(
            name="qa_with_references",
            template="""请基于以下参考资料回答问题：

问题: {question}

参考资料:
{reference_materials}

回答要求:
- 基于提供的参考资料进行回答
- 如果参考资料不足，请明确指出
- 标注信息来源，增强可信度
- 回答要准确、全面、有条理

请先分析参考资料的可靠性，然后给出有依据的回答。

回答格式：
## 答案概要
## 详细分析
## 信息来源
## 结论""",
            variables=["question", "reference_materials"],
            description="带参考资料的问答模板",
            reasoning_mode="step_by_step",
            output_format="structured"
        )

        # 7. 创意任务模板 (策略一：少样本学习)
        self.templates["creative_task"] = PromptTemplate(
            name="creative_task",
            template="""作为一个富有创意的内容创作者，请创作以下内容：

创作主题: {theme}
创作风格: {style}
目标效果: {goal}

示例参考:
{examples}

创作要求:
- 富有创意和想象力
- 语言生动有趣
- 符合指定的风格
- 能够达到预期效果

请发挥你的创造力，创作独特而精彩的内容。

创作流程:
1. 理解创作主题和要求
2. 构思创意方向和元素
3. 展开具体创作
4. 润色和完善内容
5. 最终质量检查""",
            variables=["theme", "style", "goal", "examples"],
            description="创意任务模板",
            reasoning_mode="direct",
            output_format="natural",
            examples=[
                {
                    "input": "创作关于春天的诗歌",
                    "example": "春天是希望的季节，花儿绽放，鸟儿歌唱"
                }
            ]
        )

        # 8. 总结任务模板 (策略一：分段归纳长文档)
        self.templates["summary_task"] = PromptTemplate(
            name="summary_task",
            template="""作为一个专业的信息整理专家，请对以下内容进行总结：

内容概要: {content_overview}
总结目标: {summary_goal}
总结长度: {length_constraint}

总结策略:
- 识别核心观点和关键信息
- 过滤次要和重复内容
- 保持逻辑结构清晰
- 突出重点和亮点

请按照以下格式进行总结：

## 核心观点
{core_points}

## 关键细节
{key_details}

## 重要结论
{conclusions}

## 建议行动
{recommendations}

请确保总结内容准确、完整、有价值。""",
            variables=["content_overview", "summary_goal", "length_constraint", "core_points", "key_details", "conclusions", "recommendations"],
            description="总结任务模板",
            reasoning_mode="step_by_step",
            output_format="structured"
        )

        # 9. 实体提取模板 (策略一：意图理解和实体提取)
        self.templates["entity_extraction"] = PromptTemplate(
            name="entity_extraction",
            template="""作为一个专业的信息提取专家，请从以下文本中提取关键信息：

提取目标: {extraction_goal}
文本内容: {text_content}

提取要求:
- 精确识别目标实体
- 保持信息完整性
- 结构化输出结果
- 避免遗漏重要信息

请以JSON格式输出提取结果：

{{
  "entities": [
    {{
      "type": "实体类型",
      "value": "实体值",
      "context": "上下文信息",
      "confidence": 0.9
    }}
  ],
  "relationships": [
    {{
      "source": "源实体",
      "target": "目标实体",
      "relationship": "关系类型"
    }}
  ]
}}

输出要求：
- 确保JSON格式正确
- 提供准确的实体识别
- 包含相关的上下文信息""",
            variables=["extraction_goal", "text_content"],
            description="实体提取模板",
            reasoning_mode="direct",
            output_format="json"
        )

        # 10. 复杂任务分解模板 (策略三：将复杂任务分解为简单的子任务)
        self.templates["task_decomposition"] = PromptTemplate(
            name="task_decomposition",
            template="""作为一个任务管理专家，请将以下复杂任务分解为简单的子任务：

原始任务: {complex_task}
时间约束: {time_constraint}
资源限制: {resource_constraints}

分解原则:
1. 将复杂任务拆分为独立、可执行的子任务
2. 确保每个子任务都有明确的目标和交付物
3. 考虑任务之间的依赖关系
4. 合理分配时间和资源
5. 设置可衡量的成功标准

请提供详细的任务分解方案：

## 任务分解概要
- 总任务数: [数字]
- 预计总时间: [时间]
- 关键里程碑: [里程碑列表]

## 子任务详情
{subtasks}

## 执行计划
- 任务优先级排序
- 并行执行方案
- 风险控制措施
- 质量检查点

请确保分解后的子任务易于管理和执行。""",
            variables=["complex_task", "time_constraint", "resource_constraints", "subtasks"],
            description="任务分解模板",
            reasoning_mode="step_by_step",
            output_format="structured"
        )

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """获取指定名称的模板"""
        return self.templates.get(name)

    def format_template(self, name: str, **kwargs) -> str:
        """格式化模板"""
        template = self.get_template(name)
        if not template:
            raise ValueError(f"Template '{name}' not found")

        try:
            # 检查必需变量
            missing_vars = []
            for var in template.variables:
                if var not in kwargs:
                    missing_vars.append(var)

            if missing_vars:
                raise ValueError(f"Missing required variables: {', '.join(missing_vars)}")

            # 格式化模板
            return template.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Error formatting template '{name}': {str(e)}")

    def get_enhanced_system_prompt(self, config: Dict[str, Any]) -> str:
        """生成增强的系统提示词"""
        # 使用默认值填充缺失的字段
        defaults = {
            "role_definition": config.get("role_definition", "专业的AI助手"),
            "core_task": config.get("core_task", "协助用户完成各种任务"),
            "language_style": config.get("language_style", "professional"),
            "behavior_guidance": "\n".join(f"- {guide}" for guide in config.get("behavior_guidance", [])),
            "reasoning_mode": config.get("reasoning_mode", "step_by_step"),
            "output_format": config.get("output_format", "natural"),
            "quality_criteria": "\n".join(f"- {criteria}" for criteria in config.get("quality_criteria", ["准确性", "完整性", "清晰度"]))
        }

        # 合并配置和默认值
        prompt_vars = {**defaults, **config}

        return self.format_template("system_prompt", **prompt_vars)

    def apply_task_specific_prompt(self, task_type: str, task_data: Dict[str, Any]) -> str:
        """应用任务特定的提示词"""
        task_templates = {
            "research": "research_task",
            "analysis": "analysis_task",
            "coding": "coding_task",
            "writing": "writing_task",
            "qa": "qa_with_references",
            "creative": "creative_task",
            "summary": "summary_task",
            "extraction": "entity_extraction",
            "decomposition": "task_decomposition"
        }

        template_name = task_templates.get(task_type)
        if not template_name:
            # 使用通用任务模板
            return task_data.get("content", "")

        return self.format_template(template_name, **task_data)

    def create_few_shot_prompt(self, base_prompt: str, examples: List[Dict[str, str]]) -> str:
        """创建少样本学习提示词 (策略一：少样本学习)"""
        if not examples:
            return base_prompt

        examples_text = "请参考以下示例:\n\n"
        for i, example in enumerate(examples, 1):
            examples_text += f"示例 {i}:\n"
            if "input" in example and "output" in example:
                examples_text += f"输入: {example['input']}\n"
                examples_text += f"输出: {example['output']}\n\n"
            elif "example" in example:
                examples_text += f"{example['example']}\n\n"

        examples_text += "---\n\n"
        examples_text += f"现在请处理以下内容:\n\n{base_prompt}"

        return examples_text

    def create_context_aware_prompt(self, base_prompt: str, context: str, separator: str = "---") -> str:
        """创建上下文感知的提示词 (策略一：使用分隔符标示不同的输入部分)"""
        return f"{base_prompt}\n\n{separator}\n\n上下文信息:\n{context}"

    def create_reasoning_chain_prompt(self, task: str, steps: List[str] = None) -> str:
        """创建思维链提示词 (策略一：思维链提示)"""
        if not steps:
            steps = [
                "理解问题",
                "分析信息",
                "制定计划",
                "执行推理",
                "验证结果",
                "得出结论"
            ]

        reasoning_text = f"请按以下步骤进行推理：\n\n"
        for i, step in enumerate(steps, 1):
            reasoning_text += f"步骤{i}: [{step}] - 详细说明你的思考过程\n"

        reasoning_text += f"\n任务: {task}\n\n"
        reasoning_text += "对于每个步骤，请说明：\n"
        reasoning_text += "- 你在思考什么\n"
        reasoning_text += "- 为什么这样思考\n"
        reasoning_text += "- 如何得出下一步\n\n"
        reasoning_text += "请以清晰的格式给出最终答案。"

        return reasoning_text


# 全局提示词模板引擎实例
_prompt_engine = None


def get_prompt_engine() -> PromptTemplateEngine:
    """获取全局提示词模板引擎"""
    global _prompt_engine
    if _prompt_engine is None:
        _prompt_engine = PromptTemplateEngine()
    return _prompt_engine


# 预定义的配置模板
AGENT_CONFIG_TEMPLATES = {
    "researcher": {
        "role_definition": "专业的研究员，擅长信息收集、分析和综合",
        "language_style": "academic",
        "task_mode": "research",
        "behavior_guidance": [
            "保持客观中立的研究态度",
            "重视信息来源的可靠性",
            "提供有数据支持的结论",
            "引用权威来源和学术资料"
        ],
        "reasoning_mode": "step_by_step",
        "output_format": "markdown",
        "context_requirements": [
            "需要充分的搜索时间和资源",
            "优先考虑信息质量和准确性",
            "注意信息的时效性"
        ],
        "quality_criteria": [
            "信息准确性",
            "分析深度",
            "逻辑连贯性",
            "引用规范性"
        ]
    },
    "analyst": {
        "role_definition": "专业的数据分析师，擅长数据处理和趋势分析",
        "language_style": "professional",
        "task_mode": "analysis",
        "behavior_guidance": [
            "基于数据进行客观分析",
            "使用恰当的分析方法",
            "提供可验证的结论",
            "注重分析的实用性"
        ],
        "reasoning_mode": "chain_of_thought",
        "output_format": "structured",
        "context_requirements": [
            "需要详细的数据信息",
            "明确的分析目标和范围",
            "适当的分析工具"
        ],
        "quality_criteria": [
            "数据准确性",
            "方法科学性",
            "结论可靠性",
            "建议实用性"
        ]
    },
    "writer": {
        "role_definition": "专业的内容创作者，擅长各类文体写作",
        "language_style": "professional",
        "task_mode": "writing",
        "behavior_guidance": [
            "考虑目标受众的理解水平",
            "保持内容的准确性和价值",
            "注重语言的表达效果",
            "确保内容的逻辑结构"
        ],
        "reasoning_mode": "direct",
        "output_format": "natural",
        "context_requirements": [
            "明确写作目标和要求",
            "了解受众特征和需求",
            "收集相关的参考资料"
        ],
        "quality_criteria": [
            "内容准确性",
            "表达流畅性",
            "结构清晰性",
            "语言规范性"
        ]
    },
    "coder": {
        "role_definition": "经验丰富的程序员，精通多种编程语言",
        "language_style": "technical",
        "task_mode": "coding",
        "behavior_guidance": [
            "编写清晰可读的代码",
            "遵循编程最佳实践",
            "考虑代码的健壮性",
            "提供充分的注释和文档"
        ],
        "reasoning_mode": "step_by_step",
        "output_format": "code",
        "context_requirements": [
            "明确的功能需求",
            "适当的技术栈选择",
            "充分的测试环境"
        ],
        "quality_criteria": [
            "代码正确性",
            "性能优化",
            "可维护性",
            "安全性考虑"
        ]
    }
}