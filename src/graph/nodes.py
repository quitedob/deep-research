# -*- coding: utf-8 -*-
"""
AgentWork 工作流节点实现
定义各个代理节点的处理逻辑
"""

import logging
import json
from typing import Dict, Any, Union, List

from src.config.logging import get_logger
from src.config.settings import get_settings
import asyncio
import httpx
try:
    from duckduckgo_search import DDGS  # type: ignore
except Exception:  # pragma: no cover
    DDGS = None  # type: ignore
try:
    import trafilatura  # type: ignore
except Exception:  # pragma: no cover
    trafilatura = None  # type: ignore
from .types import State, Plan, Step, StepType

logger = get_logger("nodes")
settings = get_settings()


def coordinator_node(state: Union[State, Dict[str, Any]]) -> Dict[str, Any]:
    """协调器节点 - 初始化和协调整个工作流"""
    logger.info("协调器节点启动")
    
    try:
        # 如果state是字典，转换为State对象
        if isinstance(state, dict):
            research_topic = state.get("research_topic", "")
            locale = state.get("locale", "zh-CN")
        else:
            research_topic = getattr(state, "research_topic", "")
            locale = getattr(state, "locale", "zh-CN")
        
        logger.info(f"研究主题: {research_topic}")
        logger.info(f"语言环境: {locale}")
        
        # 初始化协调信息
        coordination_message = f"开始处理研究主题: {research_topic}"
        
        return {
            "messages": [{"role": "coordinator", "content": coordination_message}],
            "locale": locale,
            "research_topic": research_topic,
            "execution_status": "running"
        }
        
    except Exception as e:
        logger.error(f"协调器节点执行失败: {e}")
        return {
            "messages": [{"role": "coordinator", "content": f"协调器启动失败: {str(e)}"}],
            "execution_status": "failed",
            "error_message": str(e)
        }


def triage_node(state: Union[State, Dict[str, Any]]) -> Dict[str, Any]:
    """分流节点 - 判断是简单聊天还是深度研究"""
    logger.info("分流节点运行")
    
    try:
        if isinstance(state, dict):
            research_topic = state.get("research_topic", "")
            messages = state.get("messages", [])
        else:
            research_topic = getattr(state, "research_topic", "")
            messages = getattr(state, "messages", [])
        
        # 简单的分流逻辑
        # 如果包含特定关键词，判断为简单聊天
        simple_chat_keywords = [
            "你好", "hello", "hi", "谢谢", "再见", "怎么样", 
            "什么时间", "天气", "简单问题", "快速回答"
        ]
        
        is_simple_chat = any(
            keyword in research_topic.lower() 
            for keyword in simple_chat_keywords
        )
        
        # 或者查询长度很短（少于20个字符）也可能是简单聊天
        if len(research_topic.strip()) < 20:
            is_simple_chat = True
        
        # 更新状态
        triage_result = "简单聊天" if is_simple_chat else "深度研究"
        logger.info(f"分流结果: {triage_result}")
        
        return {
            "chat_mode": is_simple_chat,
            "messages": messages + [{"role": "triage", "content": f"分流结果: {triage_result}"}]
        }
        
    except Exception as e:
        logger.error(f"分流节点执行失败: {e}")
        return {
            "chat_mode": True,  # 出错时默认简单聊天
            "messages": [{"role": "triage", "content": f"分流失败，默认简单聊天: {str(e)}"}],
            "error_message": str(e)
        }


def simple_chat_node(state: Union[State, Dict[str, Any]]) -> Dict[str, Any]:
    """简单聊天节点 - 处理简单的对话请求"""
    logger.info("简单聊天节点运行")
    
    try:
        if isinstance(state, dict):
            research_topic = state.get("research_topic", "")
            messages = state.get("messages", [])
        else:
            research_topic = getattr(state, "research_topic", "")
            messages = getattr(state, "messages", [])
        
        # TODO: 这里应该调用LLM进行简单对话
        # 现在提供模拟回复
        chat_response = f"您好！关于\"{research_topic}\"，这是一个简单的回复。如需深度分析，请使用研究功能。"
        
        logger.info("简单聊天完成")
        
        return {
            "final_report": chat_response,
            "execution_status": "completed",
            "messages": messages + [{"role": "assistant", "content": chat_response}]
        }
        
    except Exception as e:
        logger.error(f"简单聊天节点执行失败: {e}")
        return {
            "final_report": f"聊天处理失败: {str(e)}",
            "execution_status": "failed",
            "error_message": str(e)
        }


def background_investigation_node(state: Union[State, Dict[str, Any]]) -> Dict[str, Any]:
    """背景调查节点 - 真实 Web 搜索 + 抓取 + 抽取正文（若依赖缺失则退回占位）。"""
    logger.info("背景调查节点运行")
    
    try:
        if isinstance(state, dict):
            research_topic = state.get("research_topic", "")
        else:
            research_topic = getattr(state, "research_topic", "")
        
        if DDGS and trafilatura:
            hits = DDGS().text(research_topic, max_results=6) if research_topic else []
            urls = [h.get("href") or h.get("url") for h in hits if isinstance(h, dict)]
            urls = [u for u in urls if u]

            async def _fetch(url: str) -> str:
                try:
                    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                        r = await client.get(url)
                        r.raise_for_status()
                        html = r.text
                    text = trafilatura.extract(html, include_comments=False, include_tables=False) or ""
                    return text.strip()
                except Exception as e:  # pragma: no cover
                    logger.warning(f"抓取失败 {url}: {e}")
                    return ""

            texts: List[str] = asyncio.run(asyncio.gather(*[_fetch(u) for u in urls])) if urls else []
            bullets = []
            for u, t in zip(urls, texts):
                if t:
                    head = (t.split("\n")[0] if "\n" in t else t)[:120]
                    bullets.append(f"- 来源: {u}\n  摘要: {head}…")
            background_results = f"## 关于\"{research_topic}\"的背景信息\n\n" + ("\n".join(bullets) if bullets else "（搜索结果很少或无法抽取正文）")
        else:
            # 依赖缺失回退到占位
            background_results = f"""
## 关于"{research_topic}"的背景信息

（依赖 duckduckgo-search 或 trafilatura 不可用，已使用占位摘要）
            """.strip()
        
        logger.info("背景调查完成")
        
        return {
            "background_investigation_results": background_results,
            "observations": [f"完成了关于'{research_topic}'的背景调查"],
            "messages": [{"role": "investigator", "content": "背景调查完成"}]
        }
        
    except Exception as e:
        logger.error(f"背景调查节点执行失败: {e}")
        return {
            "background_investigation_results": f"背景调查失败: {str(e)}",
            "error_message": str(e)
        }


def planner_node(state: Union[State, Dict[str, Any]]) -> Dict[str, Any]:
    """规划器节点 - 生成研究计划"""
    logger.info("规划器节点运行")
    
    try:
        if isinstance(state, dict):
            research_topic = state.get("research_topic", "")
            background_results = state.get("background_investigation_results", "")
            plan_iterations = state.get("plan_iterations", 0)
        else:
            research_topic = getattr(state, "research_topic", "")
            background_results = getattr(state, "background_investigation_results", "")
            plan_iterations = getattr(state, "plan_iterations", 0)
        
        # 创建研究计划
        plan = Plan(
            title=f"关于'{research_topic}'的研究计划",
            description=f"针对'{research_topic}'的系统性研究方案",
            steps=[
                Step(
                    title="信息收集",
                    description=f"收集关于'{research_topic}'的详细信息",
                    step_type=StepType.RESEARCH,
                    tools_needed=["web_search", "document_analysis"]
                ),
                Step(
                    title="数据分析",
                    description="分析收集到的信息，提取关键观点",
                    step_type=StepType.ANALYSIS,
                    tools_needed=["analysis_tools"]
                ),
                Step(
                    title="综合总结", 
                    description="整合分析结果，形成完整报告",
                    step_type=StepType.SYNTHESIS,
                    tools_needed=["synthesis_tools"]
                )
            ],
            has_enough_context=bool(background_results),
            estimated_time=15
        )
        
        logger.info(f"生成研究计划，包含{len(plan.steps)}个步骤")
        
        return {
            "current_plan": plan,
            "plan_iterations": plan_iterations + 1,
            "messages": [{"role": "planner", "content": f"生成了包含{len(plan.steps)}个步骤的研究计划"}]
        }
        
    except Exception as e:
        logger.error(f"规划器节点执行失败: {e}")
        return {
            "current_plan": f"规划生成失败: {str(e)}",
            "error_message": str(e)
        }


def researcher_node(state: Union[State, Dict[str, Any]]) -> Dict[str, Any]:
    """研究员节点 - 执行具体的研究任务"""
    logger.info("研究员节点运行")
    
    try:
        if isinstance(state, dict):
            current_plan = state.get("current_plan")
            research_topic = state.get("research_topic", "")
            observations = state.get("observations", [])
        else:
            current_plan = getattr(state, "current_plan", None)
            research_topic = getattr(state, "research_topic", "")
            observations = getattr(state, "observations", [])
        
        if not current_plan or isinstance(current_plan, str):
            return {
                "messages": [{"role": "researcher", "content": "无有效研究计划，跳过研究步骤"}]
            }
        
        # 找到下一个未完成的步骤
        current_step = None
        for step in current_plan.steps:
            if not step.execution_res:
                current_step = step
                break
        
        if not current_step:
            return {
                "messages": [{"role": "researcher", "content": "所有研究步骤已完成"}]
            }
        
        # 执行当前步骤
        logger.info(f"执行步骤: {current_step.title}")
        
        # TODO: 根据步骤类型调用相应的工具
        if current_step.step_type == StepType.RESEARCH:
            execution_result = f"完成了关于'{research_topic}'的{current_step.title}。收集了相关的信息和数据。"
        elif current_step.step_type == StepType.ANALYSIS:
            execution_result = f"完成了{current_step.title}。分析了收集到的信息，提取了关键观点。"
        elif current_step.step_type == StepType.SYNTHESIS:
            execution_result = f"完成了{current_step.title}。整合了分析结果，准备形成最终报告。"
        else:
            execution_result = f"完成了{current_step.title}。"
        
        # 更新步骤执行结果
        current_step.execution_res = execution_result
        
        new_observations = observations + [f"完成步骤: {current_step.title}"]
        
        logger.info(f"步骤'{current_step.title}'执行完成")
        
        return {
            "current_plan": current_plan,
            "observations": new_observations,
            "messages": [{"role": "researcher", "content": f"完成步骤: {current_step.title}"}]
        }
        
    except Exception as e:
        logger.error(f"研究员节点执行失败: {e}")
        return {
            "messages": [{"role": "researcher", "content": f"研究执行失败: {str(e)}"}],
            "error_message": str(e)
        }


def reporter_node(state: Union[State, Dict[str, Any]]) -> Dict[str, Any]:
    """报告员节点 - 生成最终研究报告"""
    logger.info("报告员节点运行")
    
    try:
        if isinstance(state, dict):
            research_topic = state.get("research_topic", "")
            current_plan = state.get("current_plan")
            observations = state.get("observations", [])
            background_results = state.get("background_investigation_results", "")
        else:
            research_topic = getattr(state, "research_topic", "")
            current_plan = getattr(state, "current_plan", None)
            observations = getattr(state, "observations", [])
            background_results = getattr(state, "background_investigation_results", "")
        
        # 生成最终报告
        report_sections = []
        
        # 标题
        report_sections.append(f"# 关于'{research_topic}'的研究报告")
        
        # 摘要
        report_sections.append("\n## 摘要")
        report_sections.append(f"本报告针对'{research_topic}'进行了系统性研究和分析。")
        
        # 背景信息
        if background_results:
            report_sections.append("\n## 背景信息")
            report_sections.append(background_results)
        
        # 研究过程
        if observations:
            report_sections.append("\n## 研究过程")
            for i, obs in enumerate(observations, 1):
                report_sections.append(f"{i}. {obs}")
        
        # 详细分析
        report_sections.append("\n## 详细分析")
        if current_plan and hasattr(current_plan, 'steps'):
            for step in current_plan.steps:
                if step.execution_res:
                    report_sections.append(f"\n### {step.title}")
                    report_sections.append(step.execution_res)
        else:
            report_sections.append("基于收集的信息进行了全面分析。")
        
        # 结论
        report_sections.append("\n## 结论")
        report_sections.append(f"通过深入研究'{research_topic}'，我们获得了重要的发现和洞察。")
        
        # 时间戳
        from datetime import datetime
        report_sections.append(f"\n---\n*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        final_report = "\n".join(report_sections)
        
        logger.info("最终报告生成完成")
        
        return {
            "final_report": final_report,
            "execution_status": "completed",
            "messages": [{"role": "reporter", "content": "研究报告已生成"}]
        }
        
    except Exception as e:
        logger.error(f"报告员节点执行失败: {e}")
        return {
            "final_report": f"报告生成失败: {str(e)}",
            "execution_status": "failed",
            "error_message": str(e)
        } 