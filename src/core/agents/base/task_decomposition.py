# -*- coding: utf-8 -*-
"""
任务分解框架 - 基于 tech.txt 策略三：将复杂任务分解为简单的子任务
提供智能任务分解、执行计划和质量控制功能
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """任务复杂度枚举"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class TaskType(Enum):
    """任务类型枚举"""
    RESEARCH = "research"
    ANALYSIS = "analysis"
    WRITING = "writing"
    CODING = "coding"
    PLANNING = "planning"
    CREATIVE = "creative"
    MIXED = "mixed"


@dataclass
class SubTask:
    """子任务定义"""
    id: str
    title: str
    description: str
    task_type: TaskType
    estimated_time: int  # 预估时间（分钟）
    dependencies: List[str] = field(default_factory=list)  # 依赖的子任务ID
    required_tools: List[str] = field(default_factory=list)
    expected_output: str = ""
    priority: int = 1  # 优先级 1-5
    status: str = "pending"  # pending, in_progress, completed, failed
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskDecomposition:
    """任务分解结果"""
    original_task: str
    task_type: TaskType
    complexity: TaskComplexity
    total_subtasks: int
    estimated_total_time: int
    subtasks: List[SubTask]
    execution_strategy: str
    quality_checkpoints: List[str]
    created_at: datetime = field(default_factory=datetime.now)


class TaskDecomposer:
    """任务分解器 - 基于 tech.txt 策略三"""

    def __init__(self):
        self.complexity_indicators = {
            TaskComplexity.SIMPLE: [
                "简单", "基础", "单一", "直接", "simple", "basic", "single", "direct"
            ],
            TaskComplexity.MEDIUM: [
                "分析", "比较", "总结", "规划", "analyze", "compare", "summarize", "plan"
            ],
            TaskComplexity.COMPLEX: [
                "研究", "设计", "开发", "创建", "复杂", "research", "design", "develop", "create", "complex"
            ],
            TaskComplexity.VERY_COMPLEX: [
                "综合", "系统", "架构", "战略", "深度", "comprehensive", "system", "architecture", "strategy", "deep"
            ]
        }

        self.task_type_patterns = {
            TaskType.RESEARCH: [
                "研究", "调查", "查找", "搜索", "分析", "research", "investigate", "search", "analyze"
            ],
            TaskType.ANALYSIS: [
                "分析", "评估", "比较", "计算", "测试", "analyze", "evaluate", "compare", "calculate", "test"
            ],
            TaskType.WRITING: [
                "写", "创作", "编写", "撰写", "生成", "write", "create", "compose", "generate"
            ],
            TaskType.CODING: [
                "代码", "编程", "开发", "实现", "算法", "code", "program", "develop", "implement", "algorithm"
            ],
            TaskType.PLANNING: [
                "计划", "规划", "设计", "安排", "策略", "plan", "design", "schedule", "strategy"
            ],
            TaskType.CREATIVE: [
                "创意", "设计", "创作", "想象", "创新", "creative", "design", "imagine", "innovate"
            ]
        }

    def analyze_task(self, task_description: str) -> Tuple[TaskType, TaskComplexity]:
        """分析任务类型和复杂度"""
        task_lower = task_description.lower()

        # 分析任务类型
        type_scores = {}
        for task_type, patterns in self.task_type_patterns.items():
            score = sum(1 for pattern in patterns if pattern in task_lower)
            if score > 0:
                type_scores[task_type] = score

        task_type = max(type_scores.items(), key=lambda x: x[1])[0] if type_scores else TaskType.MIXED

        # 分析复杂度
        complexity_scores = {}
        for complexity, indicators in self.complexity_indicators.items():
            score = sum(1 for indicator in indicators if indicator in task_lower)
            if score > 0:
                complexity_scores[complexity] = score

        # 长度因素
        if len(task_description) > 500:
            complexity_scores[TaskComplexity.VERY_COMPLEX] = complexity_scores.get(TaskComplexity.VERY_COMPLEX, 0) + 2
        elif len(task_description) > 200:
            complexity_scores[TaskComplexity.COMPLEX] = complexity_scores.get(TaskComplexity.COMPLEX, 0) + 1

        complexity = max(complexity_scores.items(), key=lambda x: x[1])[0] if complexity_scores else TaskComplexity.MEDIUM

        return task_type, complexity

    def decompose_task(self, task_description: str, requirements: Optional[Dict] = None) -> TaskDecomposition:
        """分解任务 (策略三：将复杂任务分解为简单的子任务)"""
        requirements = requirements or {}

        # 分析任务
        task_type, complexity = self.analyze_task(task_description)

        # 根据任务类型和复杂度生成子任务
        subtasks = self._generate_subtasks(task_description, task_type, complexity, requirements)

        # 估算总时间
        total_time = sum(task.estimated_time for task in subtasks)

        # 确定执行策略
        execution_strategy = self._determine_execution_strategy(task_type, complexity, subtasks)

        # 设置质量检查点
        quality_checkpoints = self._set_quality_checkpoints(task_type, complexity, subtasks)

        logger.info(f"Task decomposed: {task_type.value} {complexity.value} -> {len(subtasks)} subtasks")

        return TaskDecomposition(
            original_task=task_description,
            task_type=task_type,
            complexity=complexity,
            total_subtasks=len(subtasks),
            estimated_total_time=total_time,
            subtasks=subtasks,
            execution_strategy=execution_strategy,
            quality_checkpoints=quality_checkpoints
        )

    def _generate_subtasks(
        self,
        task_description: str,
        task_type: TaskType,
        complexity: TaskComplexity,
        requirements: Dict
    ) -> List[SubTask]:
        """生成子任务列表"""

        if task_type == TaskType.RESEARCH:
            return self._generate_research_subtasks(task_description, complexity, requirements)
        elif task_type == TaskType.ANALYSIS:
            return self._generate_analysis_subtasks(task_description, complexity, requirements)
        elif task_type == TaskType.WRITING:
            return self._generate_writing_subtasks(task_description, complexity, requirements)
        elif task_type == TaskType.CODING:
            return self._generate_coding_subtasks(task_description, complexity, requirements)
        elif task_type == TaskType.PLANNING:
            return self._generate_planning_subtasks(task_description, complexity, requirements)
        elif task_type == TaskType.CREATIVE:
            return self._generate_creative_subtasks(task_description, complexity, requirements)
        else:  # MIXED
            return self._generate_mixed_subtasks(task_description, complexity, requirements)

    def _generate_research_subtasks(self, task_description: str, complexity: TaskComplexity, requirements: Dict) -> List[SubTask]:
        """生成研究类子任务"""
        subtasks = []

        # 基础研究子任务
        base_subtasks = [
            SubTask(
                id="research_01",
                title="明确研究目标和范围",
                description="分析研究需求，确定研究边界和关键问题",
                task_type=TaskType.PLANNING,
                estimated_time=15,
                expected_output="研究目标和范围文档",
                priority=5
            ),
            SubTask(
                id="research_02",
                title="制定搜索策略",
                description="确定关键词、数据库和搜索方法",
                task_type=TaskType.PLANNING,
                estimated_time=20,
                expected_output="搜索策略文档",
                dependencies=["research_01"],
                priority=4
            ),
            SubTask(
                id="research_03",
                title="收集初步信息",
                description="执行搜索，收集相关的初步信息",
                task_type=TaskType.RESEARCH,
                estimated_time=30,
                expected_output="初步信息收集结果",
                dependencies=["research_02"],
                required_tools=["search_tool"],
                priority=4
            )
        ]

        # 根据复杂度添加更多子任务
        if complexity in [TaskComplexity.COMPLEX, TaskComplexity.VERY_COMPLEX]:
            base_subtasks.extend([
                SubTask(
                    id="research_04",
                    title="深入信息收集",
                    description="进行深度搜索，收集专业和权威信息",
                    task_type=TaskType.RESEARCH,
                    estimated_time=45,
                    expected_output="深度信息收集结果",
                    dependencies=["research_03"],
                    required_tools=["academic_search", "web_search"],
                    priority=3
                ),
                SubTask(
                    id="research_05",
                    title="信息源验证",
                    description="评估信息源的可信度和权威性",
                    task_type=TaskType.ANALYSIS,
                    estimated_time=25,
                    expected_output="信息源评估报告",
                    dependencies=["research_04"],
                    priority=4
                )
            ])

        # 分析和总结子任务
        analysis_subtasks = [
            SubTask(
                id="research_06",
                title="信息分析和整理",
                description="分析收集的信息，识别关键发现",
                task_type=TaskType.ANALYSIS,
                estimated_time=40,
                expected_output="信息分析报告",
                dependencies=base_subtasks[-1].id if base_subtasks else "research_03",
                priority=3
            ),
            SubTask(
                id="research_07",
                title="综合研究发现",
                description="整合所有信息，形成完整的结论",
                task_type=TaskType.WRITING,
                estimated_time=35,
                expected_output="研究总结报告",
                dependencies=["research_06"],
                priority=2
            )
        ]

        subtasks.extend(base_subtasks)
        subtasks.extend(analysis_subtasks)

        return subtasks

    def _generate_analysis_subtasks(self, task_description: str, complexity: TaskComplexity, requirements: Dict) -> List[SubTask]:
        """生成分析类子任务"""
        return [
            SubTask(
                id="analysis_01",
                title="理解分析需求",
                description="明确分析目标、范围和约束条件",
                task_type=TaskType.PLANNING,
                estimated_time=15,
                expected_output="分析需求文档",
                priority=5
            ),
            SubTask(
                id="analysis_02",
                title="数据收集和准备",
                description="收集分析所需的数据和信息",
                task_type=TaskType.RESEARCH,
                estimated_time=25,
                expected_output="准备好的数据集",
                dependencies=["analysis_01"],
                required_tools=["data_collection"],
                priority=4
            ),
            SubTask(
                id="analysis_03",
                title="执行分析",
                description="使用适当的方法进行数据分析",
                task_type=TaskType.ANALYSIS,
                estimated_time=40,
                expected_output="分析结果",
                dependencies=["analysis_02"],
                priority=3
            ),
            SubTask(
                id="analysis_04",
                title="结果验证",
                description="验证分析结果的准确性和可靠性",
                task_type=TaskType.ANALYSIS,
                estimated_time=20,
                expected_output="验证报告",
                dependencies=["analysis_03"],
                priority=4
            ),
            SubTask(
                id="analysis_05",
                title="生成分析报告",
                description="创建详细的分析报告和建议",
                task_type=TaskType.WRITING,
                estimated_time=30,
                expected_output="完整分析报告",
                dependencies=["analysis_04"],
                priority=2
            )
        ]

    def _generate_writing_subtasks(self, task_description: str, complexity: TaskComplexity, requirements: Dict) -> List[SubTask]:
        """生成写作类子任务"""
        base_subtasks = [
            SubTask(
                id="writing_01",
                title="确定写作目标和受众",
                description="明确写作目的、目标读者和核心信息",
                task_type=TaskType.PLANNING,
                estimated_time=20,
                expected_output="写作目标和受众分析",
                priority=5
            ),
            SubTask(
                id="writing_02",
                title="收集和组织素材",
                description="收集写作所需的资料和信息",
                task_type=TaskType.RESEARCH,
                estimated_time=30,
                expected_output="写作素材库",
                dependencies=["writing_01"],
                required_tools=["search_tool"],
                priority=4
            ),
            SubTask(
                id="writing_03",
                title="创建大纲",
                description="设计内容结构和逻辑框架",
                task_type=TaskType.PLANNING,
                estimated_time=25,
                expected_output="详细内容大纲",
                dependencies=["writing_02"],
                priority=4
            ),
            SubTask(
                id="writing_04",
                title="撰写初稿",
                description="根据大纲撰写内容初稿",
                task_type=TaskType.WRITING,
                estimated_time=60,
                expected_output="内容初稿",
                dependencies=["writing_03"],
                priority=3
            ),
            SubTask(
                id="writing_05",
                title="修改和润色",
                description="改进内容质量，优化表达方式",
                task_type=TaskType.WRITING,
                estimated_time=40,
                expected_output="修改后的稿件",
                dependencies=["writing_04"],
                priority=2
            )
        ]

        if complexity in [TaskComplexity.COMPLEX, TaskComplexity.VERY_COMPLEX]:
            base_subtasks.extend([
                SubTask(
                    id="writing_06",
                    title="专家评审",
                    description="邀请专家进行内容评审",
                    task_type=TaskType.ANALYSIS,
                    estimated_time=30,
                    expected_output="专家评审意见",
                    dependencies=["writing_05"],
                    priority=2
                ),
                SubTask(
                    id="writing_07",
                    title="最终完善",
                    description="根据评审意见进行最终修改",
                    task_type=TaskType.WRITING,
                    estimated_time=35,
                    expected_output="最终稿件",
                    dependencies=["writing_06"],
                    priority=1
                )
            ])

        return base_subtasks

    def _generate_coding_subtasks(self, task_description: str, complexity: TaskComplexity, requirements: Dict) -> List[SubTask]:
        """生成编程类子任务"""
        return [
            SubTask(
                id="coding_01",
                title="需求分析",
                description="理解功能需求和技术约束",
                task_type=TaskType.ANALYSIS,
                estimated_time=20,
                expected_output="需求分析文档",
                priority=5
            ),
            SubTask(
                id="coding_02",
                title="设计架构",
                description="设计系统架构和数据结构",
                task_type=TaskType.PLANNING,
                estimated_time=30,
                expected_output="技术设计文档",
                dependencies=["coding_01"],
                priority=4
            ),
            SubTask(
                id="coding_03",
                title="编写核心代码",
                description="实现核心功能和算法",
                task_type=TaskType.CODING,
                estimated_time=60,
                expected_output="核心代码实现",
                dependencies=["coding_02"],
                priority=3
            ),
            SubTask(
                id="coding_04",
                title="编写测试用例",
                description="创建单元测试和集成测试",
                task_type=TaskType.CODING,
                estimated_time=30,
                expected_output="测试套件",
                dependencies=["coding_03"],
                priority=4
            ),
            SubTask(
                id="coding_05",
                title="调试和优化",
                description="修复bug，优化性能",
                task_type=TaskType.CODING,
                estimated_time=40,
                expected_output="优化后的代码",
                dependencies=["coding_04"],
                priority=3
            ),
            SubTask(
                id="coding_06",
                title="文档编写",
                description="编写技术文档和使用说明",
                task_type=TaskType.WRITING,
                estimated_time=25,
                expected_output="技术文档",
                dependencies=["coding_05"],
                priority=2
            )
        ]

    def _generate_planning_subtasks(self, task_description: str, complexity: TaskComplexity, requirements: Dict) -> List[SubTask]:
        """生成规划类子任务"""
        return [
            SubTask(
                id="planning_01",
                title="目标定义",
                description="明确规划目标和成功标准",
                task_type=TaskType.ANALYSIS,
                estimated_time=20,
                expected_output="目标定义文档",
                priority=5
            ),
            SubTask(
                id="planning_02",
                title="现状分析",
                description="分析当前状况和可用资源",
                task_type=TaskType.ANALYSIS,
                estimated_time=25,
                expected_output="现状分析报告",
                dependencies=["planning_01"],
                priority=4
            ),
            SubTask(
                id="planning_03",
                title="方案设计",
                description="设计多个可能的解决方案",
                task_type=TaskType.CREATIVE,
                estimated_time=35,
                expected_output="备选方案",
                dependencies=["planning_02"],
                priority=3
            ),
            SubTask(
                id="planning_04",
                title="方案评估",
                description="评估各方案的可行性和优缺点",
                task_type=TaskType.ANALYSIS,
                estimated_time=30,
                expected_output="方案评估报告",
                dependencies=["planning_03"],
                priority=3
            ),
            SubTask(
                id="planning_05",
                title="制定实施计划",
                description="创建详细的实施时间表和里程碑",
                task_type=TaskType.PLANNING,
                estimated_time=40,
                expected_output="实施计划",
                dependencies=["planning_04"],
                priority=2
            )
        ]

    def _generate_creative_subtasks(self, task_description: str, complexity: TaskComplexity, requirements: Dict) -> List[SubTask]:
        """生成创意类子任务"""
        return [
            SubTask(
                id="creative_01",
                title="理解创意需求",
                description="明确创意目标、风格和约束",
                task_type=TaskType.ANALYSIS,
                estimated_time=15,
                expected_output="创意需求分析",
                priority=5
            ),
            SubTask(
                id="creative_02",
                title="灵感收集",
                description="收集相关案例和参考资料",
                task_type=TaskType.RESEARCH,
                estimated_time=25,
                expected_output="灵感素材库",
                dependencies=["creative_01"],
                required_tools=["search_tool"],
                priority=4
            ),
            SubTask(
                id="creative_03",
                title="概念构思",
                description="进行头脑风暴，产生创意概念",
                task_type=TaskType.CREATIVE,
                estimated_time=40,
                expected_output="创意概念集",
                dependencies=["creative_02"],
                priority=3
            ),
            SubTask(
                id="creative_04",
                title="概念筛选和发展",
                description="筛选最佳概念并进一步发展",
                task_type=TaskType.CREATIVE,
                estimated_time=35,
                expected_output="发展成熟的创意概念",
                dependencies=["creative_03"],
                priority=2
            ),
            SubTask(
                id="creative_05",
                title="创意实现",
                description="将创意概念转化为具体作品",
                task_type=TaskType.CREATIVE,
                estimated_time=50,
                expected_output="创意作品",
                dependencies=["creative_04"],
                priority=1
            )
        ]

    def _generate_mixed_subtasks(self, task_description: str, complexity: TaskComplexity, requirements: Dict) -> List[SubTask]:
        """生成混合类子任务"""
        # 混合任务使用通用的分解策略
        return [
            SubTask(
                id="mixed_01",
                title="任务理解和分析",
                description="全面理解任务需求和分析复杂性",
                task_type=TaskType.ANALYSIS,
                estimated_time=25,
                expected_output="任务分析报告",
                priority=5
            ),
            SubTask(
                id="mixed_02",
                title="制定执行策略",
                description="确定最佳执行方法和步骤",
                task_type=TaskType.PLANNING,
                estimated_time=30,
                expected_output="执行策略文档",
                dependencies=["mixed_01"],
                priority=4
            ),
            SubTask(
                id="mixed_03",
                title="分步执行",
                description="按照策略逐步执行任务",
                task_type=TaskType.MIXED,
                estimated_time=60,
                expected_output="阶段性成果",
                dependencies=["mixed_02"],
                priority=3
            ),
            SubTask(
                id="mixed_04",
                title="质量检查和优化",
                description="检查执行质量并进行优化",
                task_type=TaskType.ANALYSIS,
                estimated_time=30,
                expected_output="质量检查报告",
                dependencies=["mixed_03"],
                priority=2
            ),
            SubTask(
                id="mixed_05",
                title="最终整合",
                description="整合所有成果并完成最终交付",
                task_type=TaskType.WRITING,
                estimated_time=35,
                expected_output="最终交付成果",
                dependencies=["mixed_04"],
                priority=1
            )
        ]

    def _determine_execution_strategy(self, task_type: TaskType, complexity: TaskComplexity, subtasks: List[SubTask]) -> str:
        """确定执行策略"""
        if complexity == TaskComplexity.SIMPLE:
            return "sequential_linear"
        elif complexity == TaskComplexity.MEDIUM:
            return "sequential_with_validation"
        elif complexity == TaskComplexity.COMPLEX:
            return "iterative_with_feedback"
        else:  # VERY_COMPLEX
            return "agile_with_parallel_execution"

    def _set_quality_checkpoints(self, task_type: TaskType, complexity: TaskComplexity, subtasks: List[SubTask]) -> List[str]:
        """设置质量检查点"""
        checkpoints = []

        # 基础检查点
        checkpoints.append("需求理解确认")
        checkpoints.append("执行进度检查")

        # 根据复杂度添加检查点
        if complexity in [TaskComplexity.COMPLEX, TaskComplexity.VERY_COMPLEX]:
            checkpoints.append("中期质量评审")
            checkpoints.append("专家意见征询")

        # 根据任务类型添加检查点
        if task_type == TaskType.RESEARCH:
            checkpoints.append("信息源可靠性验证")
        elif task_type == TaskType.CODING:
            checkpoints.append("代码质量检查")
        elif task_type == TaskType.WRITING:
            checkpoints.append("内容质量审核")

        checkpoints.append("最终交付验证")

        return checkpoints

    def get_execution_plan(self, decomposition: TaskDecomposition) -> Dict[str, Any]:
        """获取执行计划"""
        # 计算关键路径
        critical_path = self._calculate_critical_path(decomposition.subtasks)

        # 建议执行顺序
        execution_order = self._suggest_execution_order(decomposition.subtasks)

        return {
            "decomposition": decomposition,
            "critical_path": critical_path,
            "execution_order": execution_order,
            "estimated_duration": decomposition.estimated_total_time,
            "parallel_opportunities": self._identify_parallel_tasks(decomposition.subtasks)
        }

    def _calculate_critical_path(self, subtasks: List[SubTask]) -> List[str]:
        """计算关键路径"""
        # 简化的关键路径计算
        task_dict = {task.id: task for task in subtasks}
        visited = set()
        path = []

        def visit(task_id: str):
            if task_id in visited:
                return
            visited.add(task_id)

            if task_id in task_dict:
                task = task_dict[task_id]
                for dep in task.dependencies:
                    visit(dep)
                path.append(task_id)

        # 访问所有任务
        for task_id in task_dict:
            visit(task_id)

        return path

    def _suggest_execution_order(self, subtasks: List[SubTask]) -> List[str]:
        """建议执行顺序"""
        # 按优先级和依赖关系排序
        sorted_tasks = sorted(subtasks, key=lambda x: (-x.priority, x.estimated_time))
        return [task.id for task in sorted_tasks]

    def _identify_parallel_tasks(self, subtasks: List[SubTask]) -> List[List[str]]:
        """识别可并行执行的任务"""
        parallel_groups = []
        remaining_tasks = subtasks.copy()

        while remaining_tasks:
            current_group = []
            for task in remaining_tasks[:]:
                # 检查依赖是否都已完成
                dependencies_met = all(
                    dep not in [t.id for t in remaining_tasks]
                    for dep in task.dependencies
                )

                if dependencies_met and not task.dependencies:
                    current_group.append(task.id)

            if current_group:
                parallel_groups.append(current_group)
                # 移除已分组的任务
                remaining_tasks = [t for t in remaining_tasks if t.id not in current_group]
            else:
                # 如果没有可并行的任务，按顺序执行
                if remaining_tasks:
                    parallel_groups.append([remaining_tasks[0].id])
                    remaining_tasks = remaining_tasks[1:]

        return parallel_groups


# 全局任务分解器实例
_task_decomposer = None


def get_task_decomposer() -> TaskDecomposer:
    """获取全局任务分解器"""
    global _task_decomposer
    if _task_decomposer is None:
        _task_decomposer = TaskDecomposer()
    return _task_decomposer