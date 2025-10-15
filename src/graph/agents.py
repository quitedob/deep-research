# -*- coding: utf-8 -*-
"""
定义多智能体系统中的各个智能体节点。
"""

from pathlib import Path
from typing import List, Dict, Any

from .state import GraphState
from ..rag.retrieval import search_documents  # 假设已有检索服务
from ..rag.reranker import rerank_documents  # 需要创建的重排序服务


async def supervisor_node(state: GraphState) -> dict:
    """
    主管智能体：负责规划、路由和评估。
    基于LLM驱动的智能决策系统
    """
    print("---SUPERVISOR---")
    iteration_count = state.get("iteration_count", 0)

    # 首次运行时，生成详细计划
    if iteration_count == 0:
        plan = await generate_research_plan(state['original_query'])
        return {
            "research_plan": plan,
            "next_action": "researcher",
            "iteration_count": 1,
            "error_log": [],
            "planning_method": "llm_driven"  # 标记使用了LLM驱动规划
        }

    # 检查是否有错误
    error_log = state.get("error_log", [])
    if error_log and len(error_log) > 0:
        # 如果有太多错误，可能需要人类干预
        if len(error_log) > 3:
            return {
                "next_action": "finish",
                "error_log": error_log + ["Too many errors, workflow terminated"],
                "human_review_required": True,
                "feedback_request": "The research process encountered multiple errors. Please review and provide guidance."
            }

    # 评估当前状态并决定下一步行动
    next_action = await evaluate_and_route(state)

    # 处理特殊动作
    if next_action == "reflection":
        reflection_result = await reflection_node(state)
        return {
            "next_action": reflection_result["next_action"],
            "iteration_count": iteration_count + 1,
            "reflection_result": reflection_result.get("reflection_result"),
            "reflection_applied": True
        }

    return {
        "next_action": next_action,
        "iteration_count": iteration_count + 1
    }


async def generate_research_plan(query: str) -> list:
    """
    使用LLM生成智能的研究计划
    基于LangGraph的Plan-and-Execute架构
    """
    try:
        from ..llms.router import SmartModelRouter
        from ..config.config_loader import get_settings
        import json

        # 获取配置的路由器
        settings = get_settings()
        router = SmartModelRouter.from_conf(Path(settings.get('CONFIG_FILE', 'conf.yaml')))

        # 构造规划提示词
        planning_prompt = f"""
        你是一个专业的研究规划师。请为以下研究查询生成一个详细、可执行的研究计划。

        研究查询：{query}

        请生成一个JSON格式的研究计划，包含以下结构：
        {{
            "plan_summary": "对整个研究计划的简要总结",
            "estimated_steps": 3,
            "steps": [
                {{
                    "step": 1,
                    "agent": "researcher",
                    "task": "具体的任务描述",
                    "description": "详细的任务说明",
                    "tools_needed": ["工具1", "工具2"],
                    "expected_output": "预期的输出结果",
                    "success_criteria": "成功的标准"
                }}
            ]
        }}

        指导原则：
        1. 根据查询复杂度智能调整步骤数量（3-7步）
        2. 为技术类查询安排代码分析步骤
        3. 为分析类查询安排数据分析步骤
        4. 总是以综合报告生成作为最后一步
        5. 确保每个步骤都有明确的成功标准
        6. 选择合适的工具和智能体

        可用的智能体：
        - researcher: 信息检索和研究
        - coder: 代码分析和技术实现
        - writer: 报告撰写和总结
        - analyst: 数据分析和可视化

        可用的工具：
        - web_search: 网络搜索
        - arxiv_search: 学术论文搜索
        - rag_retrieval: 内部知识库检索
        - code_search: 代码搜索
        - github_search: GitHub代码库搜索
        - technical_docs: 技术文档分析
        - data_analysis: 数据分析
        - visualization: 数据可视化
        - statistics: 统计分析
        - markdown_writer: Markdown报告生成
        - evidence_synthesis: 证据综合分析

        请只返回JSON格式的计划，不要包含其他解释文本。
        """

        # 调用LLM生成计划
        messages = [{"role": "user", "content": planning_prompt}]
        result = await router.route_and_chat(
            task_type="research",
            messages=messages,
            temperature=0.3,  # 使用较低温度确保计划结构化
            max_tokens=2000,
            quality_requirement=0.8
        )

        # 解析LLM响应
        content = result.get("content", "")

        # 尝试提取JSON
        try:
            # 清理可能的markdown代码块标记
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            plan_data = json.loads(content)

            # 验证计划结构
            if not isinstance(plan_data, dict) or "steps" not in plan_data:
                raise ValueError("Invalid plan structure")

            steps = plan_data["steps"]
            if not isinstance(steps, list) or len(steps) == 0:
                raise ValueError("No steps found in plan")

            # 验证每个步骤的必需字段
            for i, step in enumerate(steps):
                if not all(key in step for key in ["step", "agent", "task", "description"]):
                    raise ValueError(f"Step {i+1} missing required fields")

            print(f"Generated intelligent research plan with {len(steps)} steps")
            print(f"Plan summary: {plan_data.get('plan_summary', 'No summary')}")

            return steps

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Failed to parse LLM plan: {e}")
            print("Falling back to adaptive plan generation")
            return await generate_adaptive_fallback_plan(query)

    except Exception as e:
        print(f"LLM plan generation failed: {e}")
        print("Using fallback plan generation")
        return await generate_adaptive_fallback_plan(query)


async def generate_adaptive_fallback_plan(query: str) -> list:
    """
    自适应回退计划生成（比原始关键词匹配更智能）
    """
    query_lower = query.lower()
    plan = []

    # 分析查询复杂度和类型
    complexity_indicators = {
        'technical': ['code', 'programming', 'algorithm', 'software', 'api', 'framework', 'implementation'],
        'analytical': ['analyze', 'compare', 'statistics', 'data', 'trend', 'performance', 'evaluation'],
        'research': ['research', 'study', 'investigate', 'review', 'survey', 'examination'],
        'comprehensive': ['comprehensive', 'detailed', 'in-depth', 'thorough', 'complete']
    }

    detected_types = []
    for type_name, keywords in complexity_indicators.items():
        if any(keyword in query_lower for keyword in keywords):
            detected_types.append(type_name)

    # 基础信息收集（总是第一步）
    plan.append({
        "step": 1,
        "agent": "researcher",
        "task": f"Conduct comprehensive information gathering for: {query}",
        "description": "Systematically collect information from multiple sources including web search, academic databases, and internal knowledge base",
        "tools_needed": ["web_search", "arxiv_search", "wikipedia_search", "rag_retrieval"],
        "expected_output": "Relevant documents and sources",
        "success_criteria": "At least 5 high-quality sources collected"
    })

    current_step = 2

    # 根据检测到的类型添加专门步骤
    if 'technical' in detected_types:
        plan.append({
            "step": current_step,
            "agent": "researcher",
            "task": f"Analyze technical implementations and code examples for: {query}",
            "description": "Focus on technical details, code samples, best practices, and implementation strategies",
            "tools_needed": ["code_search", "github_search", "technical_docs"],
            "expected_output": "Technical analysis and code examples",
            "success_criteria": "Technical concepts clearly explained with examples"
        })
        current_step += 1

    if 'analytical' in detected_types:
        plan.append({
            "step": current_step,
            "agent": "researcher",
            "task": f"Perform analytical review and data synthesis for: {query}",
            "description": "Analyze data patterns, compare different approaches, and synthesize analytical insights",
            "tools_needed": ["data_analysis", "statistics", "rag_retrieval"],
            "expected_output": "Analytical findings and data insights",
            "success_criteria": "Clear analytical framework with supporting evidence"
        })
        current_step += 1

    # 如果是综合性查询，添加深度分析步骤
    if 'comprehensive' in detected_types or len(detected_types) > 1:
        plan.append({
            "step": current_step,
            "agent": "researcher",
            "task": f"Conduct in-depth cross-domain analysis for: {query}",
            "description": "Integrate information from multiple domains and provide comprehensive coverage",
            "tools_needed": ["web_search", "rag_retrieval", "arxiv_search"],
            "expected_output": "Cross-domain insights and comprehensive analysis",
            "success_criteria": "Multiple perspectives integrated with supporting evidence"
        })
        current_step += 1

    # 最终报告生成（总是最后一步）
    plan.append({
        "step": current_step,
        "agent": "writer",
        "task": f"Generate comprehensive research report for: {query}",
        "description": "Create well-structured report with executive summary, findings, analysis, conclusions, and recommendations",
        "tools_needed": ["markdown_writer", "evidence_synthesis"],
        "expected_output": "Complete research report",
        "success_criteria": "Report covers all aspects with clear conclusions"
    })

    return plan


async def evaluate_and_route(state: GraphState) -> str:
    """
    智能评估当前状态并决定下一步行动
    基于LLM的反思和重规划机制
    """
    try:
        from ..llms.router import SmartModelRouter
        from ..config.config_loader import get_settings

        iteration_count = state.get("iteration_count", 0)
        plan = state.get("research_plan", [])
        retrieved_docs = state.get("retrieved_documents", [])
        draft_report = state.get("draft_report")
        original_query = state.get("original_query", "")
        error_log = state.get("error_log", [])

        # 如果还有计划步骤未完成，执行下一步
        if iteration_count <= len(plan):
            current_step_index = iteration_count - 1
            if current_step_index < len(plan):
                next_step = plan[current_step_index]

                # 检查当前步骤是否完成
                if await is_step_completed(next_step, state):
                    print(f"Step {next_step['step']} completed successfully")
                    # 继续下一步或进入反思阶段
                    if current_step_index + 1 < len(plan):
                        return plan[current_step_index + 1]["agent"]
                    else:
                        return "reflection"  # 所有步骤完成，进入反思
                else:
                    return next_step["agent"]  # 继续当前步骤

        # 如果没有明确计划或计划已完成，使用LLM智能路由
        return await llm_intelligent_routing(state)

    except Exception as e:
        print(f"Intelligent routing failed: {e}")
        # 回退到简单路由逻辑
        return fallback_routing(state)


async def is_step_completed(step: Dict[str, Any], state: GraphState) -> bool:
    """
    检查研究步骤是否完成
    """
    step_type = step.get("agent", "")
    success_criteria = step.get("success_criteria", "")

    if step_type == "researcher":
        # 检查是否收集到足够的信息
        retrieved_docs = state.get("retrieved_documents", [])
        return len(retrieved_docs) >= 3  # 至少3个文档

    elif step_type == "writer":
        # 检查是否生成了报告
        draft_report = state.get("draft_report")
        return draft_report is not None and len(draft_report) > 200

    elif step_type == "analyst":
        # 检查是否进行了数据分析
        analysis_result = state.get("analysis_result")
        return analysis_result is not None

    else:
        # 默认认为步骤完成
        return True


async def llm_intelligent_routing(state: GraphState) -> str:
    """
    使用LLM进行智能路由决策
    """
    try:
        from ..llms.router import SmartModelRouter
        from ..config.config_loader import get_settings

        settings = get_settings()
        router = SmartModelRouter.from_conf(Path(settings.get('CONFIG_FILE', 'conf.yaml')))

        # 构建状态摘要
        state_summary = f"""
        当前研究状态评估：

        研究查询：{state.get('original_query', '')}
        当前迭代：{state.get('iteration_count', 0)}
        已收集文档数：{len(state.get('retrieved_documents', []))}
        报告状态：{'已生成' if state.get('draft_report') else '未生成'}
        错误次数：{len(state.get('error_log', []))}

        请分析当前状态并决定下一步行动。可选行动：
        - researcher: 继续收集信息
        - writer: 生成或完善报告
        - analyst: 进行数据分析
        - reflection: 反思和重规划
        - finish: 完成研究

        请返回一个行动名称，只返回行动名称，不要解释。
        """

        messages = [{"role": "user", "content": state_summary}]
        result = await router.route_and_chat(
            task_type="reasoning",
            messages=messages,
            temperature=0.2,  # 低温度确保决策稳定
            max_tokens=100,
            quality_requirement=0.9
        )

        action = result.get("content", "").strip().lower()

        # 验证返回的行动
        valid_actions = ["researcher", "writer", "analyst", "reflection", "finish"]
        if action in valid_actions:
            return action
        else:
            print(f"Invalid action from LLM: {action}, using fallback")
            return "finish"

    except Exception as e:
        print(f"LLM routing failed: {e}")
        return "finish"


async def reflection_node(state: GraphState) -> dict:
    """
    反思节点：评估研究质量并决定是否需要额外步骤
    """
    print("---REFLECTION---")

    try:
        from ..llms.router import SmartModelRouter
        from ..config.config_loader import get_settings

        settings = get_settings()
        router = SmartModelRouter.from_conf(Path(settings.get('CONFIG_FILE', 'conf.yaml')))

        # 构建反思提示词
        reflection_prompt = f"""
        请对当前的研究结果进行反思和评估。

        研究查询：{state.get('original_query', '')}
        收集的文档数量：{len(state.get('retrieved_documents', []))}
        报告状态：{'已生成' if state.get('draft_report') else '未生成'}
        报告长度：{len(state.get('draft_report', ''))} 字符

        请评估：
        1. 信息收集是否充分？
        2. 报告质量是否满足要求？
        3. 是否需要额外的分析或信息？
        4. 研究是否可以结束？

        请返回JSON格式的评估结果：
        {{
            "information_sufficiency": "sufficient/insufficient/adequate",
            "report_quality": "excellent/good/fair/poor",
            "needs_additional_work": true/false,
            "recommended_actions": ["action1", "action2"],
            "can_finish": true/false,
            "reasoning": "评估理由"
        }}
        """

        messages = [{"role": "user", "content": reflection_prompt}]
        result = await router.route_and_chat(
            task_type="reasoning",
            messages=messages,
            temperature=0.3,
            max_tokens=500,
            quality_requirement=0.8
        )

        try:
            import json
            content = result.get("content", "")

            # 清理JSON响应
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            evaluation = json.loads(content)

            print(f"Reflection evaluation: {evaluation.get('reasoning', 'No reasoning')}")

            # 根据评估结果决定下一步
            if evaluation.get("can_finish", False):
                return {"next_action": "finish", "reflection_result": evaluation}
            elif evaluation.get("needs_additional_work", False):
                actions = evaluation.get("recommended_actions", [])
                if actions:
                    return {"next_action": actions[0], "reflection_result": evaluation}
                else:
                    return {"next_action": "researcher", "reflection_result": evaluation}
            else:
                return {"next_action": "writer", "reflection_result": evaluation}

        except json.JSONDecodeError:
            print("Failed to parse reflection JSON, defaulting to finish")
            return {"next_action": "finish", "reflection_result": {"parsing_error": True}}

    except Exception as e:
        print(f"Reflection failed: {e}")
        return {"next_action": "finish", "reflection_result": {"error": str(e)}}


def fallback_routing(state: GraphState) -> str:
    """
    简单的回退路由逻辑
    """
    retrieved_docs = state.get("retrieved_documents", [])
    draft_report = state.get("draft_report")

    if len(retrieved_docs) < 3:
        return "researcher"
    elif not draft_report:
        return "writer"
    else:
        return "finish"


async def researcher_node(state: GraphState) -> dict:
    """
    研究员智能体：负责信息检索。
    """
    print("---RESEARCHER---")
    query = state["original_query"]

    try:
        # 1. 初步检索
        from ..rag.retrieval import search_documents, RetrievalStrategy
        initial_results = await search_documents(query, strategy=RetrievalStrategy.VECTOR_ONLY, top_k=20)

        # 2. 转换为字典格式供重排序器使用
        initial_docs = []
        for result in initial_results:
            doc_dict = {
                'content': result.content,
                'metadata': result.metadata,
                'score': result.score,
                'source': result.source,
                'chunk_id': result.chunk_id
            }
            initial_docs.append(doc_dict)

        # 3. 重排序
        reranked_docs = await rerank_documents(query, initial_docs)

        # 4. 选择Top-N
        top_docs = reranked_docs[:5]

        print(f"Found {len(top_docs)} relevant documents after reranking.")

        # 更新状态
        current_docs = state.get("retrieved_documents", [])
        updated_docs = current_docs + top_docs

        return {"retrieved_documents": updated_docs, "next_action": "supervisor"}

    except Exception as e:
        print(f"Researcher error: {e}")
        error_log = state.get("error_log", [])
        return {
            "error_log": error_log + [f"Researcher error: {str(e)}"],
            "next_action": "supervisor"
        }


async def writer_node(state: GraphState) -> dict:
    """
    报告撰写智能体：负责生成最终报告。
    """
    print("---WRITER---")
    documents = state.get("retrieved_documents", [])
    original_query = state.get("original_query", "")

    if not documents:
        return {"draft_report": "No information found to generate a report.", "next_action": "supervisor"}

    try:
        # 生成结构化的研究报告
        report_content = await generate_structured_report(original_query, documents)

        return {"draft_report": report_content, "next_action": "supervisor"}

    except Exception as e:
        print(f"Writer error: {e}")
        error_log = state.get("error_log", [])
        return {
            "error_log": error_log + [f"Writer error: {str(e)}"],
            "draft_report": "Error occurred while generating report.",
            "next_action": "supervisor"
        }


async def generate_structured_report(query: str, documents: List[Dict[str, Any]]) -> str:
    """
    生成结构化的研究报告。
    """
    report_lines = []

    # 标题
    report_lines.append("# 研究报告")
    report_lines.append(f"**研究主题**: {query}")
    report_lines.append(f"**生成时间**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # 执行摘要
    report_lines.append("## 执行摘要")
    summary = extract_summary(query, documents)
    report_lines.append(summary)
    report_lines.append("")

    # 主要发现
    report_lines.append("## 主要发现")
    key_findings = extract_key_findings(documents)
    for i, finding in enumerate(key_findings, 1):
        report_lines.append(f"### 发现 {i}")
        report_lines.append(finding)
        report_lines.append("")

    # 详细分析
    report_lines.append("## 详细分析")
    for i, doc in enumerate(documents[:10], 1):  # 限制显示前10个文档
        report_lines.append(f"### 来源 {i}")
        metadata = doc.get('metadata', {})

        # 添加来源信息
        if metadata.get('source_url'):
            report_lines.append(f"**来源URL**: {metadata['source_url']}")
        if metadata.get('document_id'):
            report_lines.append(f"**文档ID**: {metadata['document_id']}")

        report_lines.append(f"**相关度**: {doc.get('rerank_score', doc.get('score', 'N/A')):.3f}")
        report_lines.append("")

        # 添加内容摘要
        content = doc.get('content', '')
        if len(content) > 500:
            content = content[:500] + "..."
        report_lines.append(f"**内容**: {content}")
        report_lines.append("")

    # 结论和建议
    report_lines.append("## 结论和建议")
    conclusions = generate_conclusions(query, documents)
    report_lines.append(conclusions)
    report_lines.append("")

    # 参考资料
    report_lines.append("## 参考资料")
    for i, doc in enumerate(documents, 1):
        metadata = doc.get('metadata', {})
        source_info = f"{i}. "
        if metadata.get('source_url'):
            source_info += f"[{metadata.get('source_url')}]"
        elif metadata.get('document_id'):
            source_info += f"文档ID: {metadata['document_id']}"
        else:
            source_info += f"来源 {i}"
        report_lines.append(source_info)
    report_lines.append("")

    return "\n".join(report_lines)


def extract_summary(query: str, documents: List[Dict[str, Any]]) -> str:
    """提取摘要"""
    if not documents:
        return "未找到相关信息。"

    total_docs = len(documents)
    avg_score = sum(doc.get('rerank_score', doc.get('score', 0)) for doc in documents) / total_docs

    summary = f"本次研究针对'{query}'主题，共检索到{total_docs}个相关信息来源，"
    summary += ".3f"
    summary += "这些信息来源于多个可靠渠道，经过重排序和筛选，提供了较为全面的视角。"

    return summary


def extract_key_findings(documents: List[Dict[str, Any]]) -> List[str]:
    """提取关键发现"""
    findings = []

    # 分析文档来源分布
    sources = {}
    for doc in documents:
        metadata = doc.get('metadata', {})
        source_type = metadata.get('source', 'unknown')
        sources[source_type] = sources.get(source_type, 0) + 1

    if sources:
        findings.append(f"信息来源分布: {', '.join([f'{k}({v})' for k, v in sources.items()])}")

    # 分析内容长度分布
    total_length = sum(len(doc.get('content', '')) for doc in documents)
    avg_length = total_length / len(documents) if documents else 0
    findings.append(f"平均内容长度: {int(avg_length)} 字符")

    # 分析最高相关度内容
    if documents:
        top_doc = max(documents, key=lambda x: x.get('rerank_score', x.get('score', 0)))
        findings.append(f"最相关内容预览: {top_doc.get('content', '')[:100]}...")

    return findings


def generate_conclusions(query: str, documents: List[Dict[str, Any]]) -> str:
    """生成结论"""
    if not documents:
        return "由于缺乏相关信息，无法得出可靠结论。建议扩大搜索范围或调整查询条件。"

    conclusion = "基于检索到的信息，可以得出以下初步结论：\n\n"
    conclusion += "1. **信息丰富度**: 检索结果显示该主题有较为丰富的信息来源\n"
    conclusion += "2. **内容质量**: 通过重排序算法，优先展示了最相关的内容\n"
    conclusion += "3. **建议**: 如需更深入的研究，建议结合多种信息来源进行交叉验证\n\n"
    conclusion += "本报告基于当前可用的数据生成，最终结论可能需要结合更多实证研究来验证。"

    return conclusion
