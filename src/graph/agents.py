# -*- coding: utf-8 -*-
"""
定义多智能体系统中的各个智能体节点。
"""

from .state import GraphState
from ..rag.retrieval import search_documents  # 假设已有检索服务
from ..rag.reranker import rerank_documents  # 需要创建的重排序服务


async def supervisor_node(state: GraphState) -> dict:
    """
    主管智能体：负责规划、路由和评估。
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
            "error_log": []
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

    return {
        "next_action": next_action,
        "iteration_count": iteration_count + 1
    }


async def generate_research_plan(query: str) -> list:
    """
    生成详细的研究计划。
    暂时使用硬编码逻辑，未来可以集成LLM生成更智能的计划。
    """
    # 分析查询类型和复杂度
    query_lower = query.lower()

    plan = []

    # 基础信息收集
    plan.append({
        "step": 1,
        "agent": "researcher",
        "task": f"Perform comprehensive search for: {query}",
        "description": "Gather diverse sources of information from web, academic papers, and internal knowledge base",
        "tools_needed": ["web_search", "arxiv_search", "wikipedia_search", "rag_retrieval"]
    })

    # 如果是技术相关的问题，添加代码分析
    if any(keyword in query_lower for keyword in ["code", "programming", "algorithm", "software", "api", "framework"]):
        plan.append({
            "step": 2,
            "agent": "researcher",
            "task": f"Analyze technical aspects and code examples related to: {query}",
            "description": "Focus on technical implementation details, code examples, and best practices",
            "tools_needed": ["code_search", "github_search", "technical_docs"]
        })

    # 如果需要数据分析，添加分析步骤
    if any(keyword in query_lower for keyword in ["analyze", "compare", "statistics", "data", "trend", "performance"]):
        plan.append({
            "step": 3,
            "agent": "coder",  # 未来实现
            "task": f"Analyze data and provide quantitative insights for: {query}",
            "description": "Perform data analysis, create visualizations, and extract key metrics",
            "tools_needed": ["data_analysis", "visualization", "statistics"]
        })

    # 最终报告生成
    plan.append({
        "step": len(plan) + 1,
        "agent": "writer",
        "task": f"Generate comprehensive report synthesizing all findings for: {query}",
        "description": "Create a well-structured report with conclusions, recommendations, and supporting evidence",
        "tools_needed": ["markdown_writer", "evidence_synthesis"]
    })

    return plan


async def evaluate_and_route(state: GraphState) -> str:
    """
    评估当前状态并决定下一步行动。
    """
    iteration_count = state.get("iteration_count", 0)
    plan = state.get("research_plan", [])
    retrieved_docs = state.get("retrieved_documents", [])
    draft_report = state.get("draft_report")

    # 如果还没有完成所有计划步骤，继续执行计划
    if iteration_count <= len(plan):
        current_step_index = iteration_count - 1
        if current_step_index < len(plan):
            next_step = plan[current_step_index]
            return next_step["agent"]

    # 如果有报告生成，检查是否需要完善
    if draft_report:
        # 简单的质量检查（未来可以更复杂）
        if len(draft_report) < 500:  # 报告太短
            return "writer"  # 重新生成更详细的报告
        elif len(retrieved_docs) < 3:  # 信息来源不足
            return "researcher"  # 收集更多信息
        else:
            return "finish"  # 完成工作流

    # 如果有文档但没有报告，开始写报告
    if retrieved_docs and not draft_report:
        return "writer"

    # 默认情况下，如果有疑问，收集更多信息
    if len(retrieved_docs) < 5:
        return "researcher"

    # 最终完成
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
