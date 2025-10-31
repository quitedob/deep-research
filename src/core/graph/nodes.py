# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import json
import logging
import os
from functools import partial
from typing import Annotated, Literal

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
# from langchain_core.tools import tool  # Not needed for AgentScope
from langgraph.types import Command, interrupt

from ..mcp.client import MultiServerMCPClient
from src.agents import create_agent
from src.config.agents import AGENT_LLM_MAP
from src.config.configuration import Configuration
from src.llms.llm import get_llm_by_type, get_llm_token_limit_by_type
from src.prompts.planner_model import Plan
from src.prompts.template import apply_prompt_template
from src.tools import (
    crawl_tool,
    get_retriever_tool,
    get_web_search_tool,
    python_repl_tool,
)
from src.tools.search import LoggedTavilySearch
from src.utils.context_manager import ContextManager, validate_message_content
from src.utils.json_utils import repair_json_output, sanitize_tool_response
from ..config import SELECTED_SEARCH_ENGINE, SearchEngine
from .types import State
from .utils import (
    build_clarified_topic_from_history,
    get_message_content,
    is_user_message,
    reconstruct_clarification_history,
)

# 获取日志记录器
logger = logging.getLogger(__name__)


def handoff_to_planner(research_topic: str, locale: str):
    """
    一个工具函数，用于信号传递给 planner 代理来制定计划。
    """
    # 此工具不返回任何内容；仅用作 LLM 发出切换到 planner 信号的方式
    return


def handoff_after_clarification(locale: str, research_topic: str):
    """
    在澄清轮次完成后，将任务转交给 planner。将所有澄清历史传递给 planner 进行分析。
    """
    return


def needs_clarification(state: dict) -> bool:
    """
    根据当前状态检查是否需要澄清。
    用于确定何时继续澄清的集中式逻辑。
    """
    if not state.get("enable_clarification", False):
        return False
    clarification_rounds = state.get("clarification_rounds", 0)
    is_clarification_complete = state.get("is_clarification_complete", False)
    max_clarification_rounds = state.get("max_clarification_rounds", 3)
    
    # 需要澄清的条件：已启用 + 有剩余轮次 + 未完成 + 未超最大轮次
    # 使用 <= 是因为在询问第N个问题后，我们仍需等待第N个答案
    return (
        clarification_rounds > 0
        and not is_clarification_complete
        and clarification_rounds <= max_clarification_rounds
    )


def preserve_state_meta_fields(state: State) -> dict:
    """
    提取应在状态转换中保留的元/配置字段。
    这些字段对工作流的连续性至关重要。
    """
    return {
        "locale": state.get("locale", "en-US"),
        "research_topic": state.get("research_topic", ""),
        "clarified_research_topic": state.get("clarified_research_topic", ""),
        "clarification_history": state.get("clarification_history", []),
        "enable_clarification": state.get("enable_clarification", False),
        "max_clarification_rounds": state.get("max_clarification_rounds", 3),
        "clarification_rounds": state.get("clarification_rounds", 0),
        "resources": state.get("resources", []),
    }


def validate_and_fix_plan(plan: dict, enforce_web_search: bool = False) -> dict:
    """
    验证并修复计划，确保其满足要求。
    
    Args:
        plan: 待验证的计划字典。
        enforce_web_search: 如果为 True，确保至少有一个步骤设置 need_search=true。
        
    Returns:
        验证/修复后的计划字典。
    """
    if not isinstance(plan, dict):
        return plan
    steps = plan.get("steps", [])
    
    # ============================================================
    # SECTION 1: 修复缺失的 step_type 字段
    # ============================================================
    for idx, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        # 检查 step_type 是否缺失或为空
        if "step_type" not in step or not step.get("step_type"):
            # 根据 need_search 值推断 step_type
            inferred_type = "research" if step.get("need_search", False) else "processing"
            step["step_type"] = inferred_type
            logger.info(
                f"修复了步骤 {idx} ({step.get('title', 'Untitled')}) 缺失的 step_type： "
                f"根据 need_search={step.get('need_search', False)} 推断为 '{inferred_type}'"
            )
            
    # ============================================================
    # SECTION 2: 强制执行 Web 搜索要求
    # ============================================================
    if enforce_web_search:
        # 检查是否有步骤设置 need_search=true
        has_search_step = any(step.get("need_search", False) for step in steps)
        
        if not has_search_step and steps:
            # 确保第一个 research 步骤启用了 Web 搜索
            for idx, step in enumerate(steps):
                if step.get("step_type") == "research":
                    step["need_search"] = True
                    logger.info(f"在索引 {idx} 的 research 步骤上强制启用 Web 搜索")
                    break
            else:
                # 备用方案：如果没有 research 步骤，将第一个步骤转换为启用 Web 搜索的 research 步骤。
                steps[0]["step_type"] = "research"
                steps[0]["need_search"] = True
                logger.info("强制将第一个步骤转换为带 Web 搜索的 research 步骤")
                
        elif not has_search_step and not steps:
            # 如果计划没有步骤，添加一个默认的 research 步骤
            logger.warning("计划没有步骤。添加默认的 research 步骤。")
            plan["steps"] = [
                {
                    "need_search": True,
                    "title": "Initial Research",
                    "description": "Gather information about the topic",
                    "step_type": "research",
                }
            ]
    return plan


def background_investigation_node(state: State, config: RunnableConfig):
    """背景调查节点，使用搜索引擎获取初步信息。"""
    logger.info("background investigation node 正在运行。")
    configurable = Configuration.from_runnable_config(config)
    query = state.get("clarified_research_topic") or state.get("research_topic")
    background_investigation_results = []

    if SELECTED_SEARCH_ENGINE == SearchEngine.TAVILY.value:
        searched_content = LoggedTavilySearch(
            max_results=configurable.max_search_results
        ).invoke(query)

        # 检查 searched_content 是否为元组，如果是则解包
        if isinstance(searched_content, tuple):
            searched_content = searched_content[0]

        # 处理字符串 JSON 响应（来自修复后的 Tavily 工具的新格式）
        if isinstance(searched_content, str):
            try:
                parsed = json.loads(searched_content)
                if isinstance(parsed, dict) and "error" in parsed:
                    logger.error(f"Tavily 搜索错误: {parsed['error']}")
                    background_investigation_results = []
                elif isinstance(parsed, list):
                    background_investigation_results = [
                        f"## {elem.get('title', 'Untitled')}\n\n{elem.get('content', 'No content')}"
                        for elem in parsed
                    ]
                else:
                    logger.error(f"Tavily 响应格式意外: {searched_content}")
                    background_investigation_results = []
            except json.JSONDecodeError:
                logger.error(f"解析 Tavily 响应 JSON 失败: {searched_content}")
                background_investigation_results = []
        # 处理遗留的列表格式
        elif isinstance(searched_content, list):
            background_investigation_results = [
                f"## {elem['title']}\n\n{elem['content']}" for elem in searched_content
            ]
        else:
            logger.error(f"Tavily 搜索返回了格式错误的响应: {searched_content}")
            background_investigation_results = []
        
        # [FIXED] 修复了缩进错误，此 return 应位于 Tavily if 块的末尾
        return {
            "background_investigation_results": "\n\n".join(
                background_investigation_results
            )
        }
    else:
        # 其他搜索引擎逻辑
        background_investigation_results = get_web_search_tool(
            configurable.max_search_results
        ).invoke(query)
        return {
            "background_investigation_results": json.dumps(
                background_investigation_results, ensure_ascii=False
            )
        }


def planner_node(
    state: State, config: RunnableConfig
) -> Command[Literal["human_feedback", "reporter"]]:
    """Planner 节点，用于生成完整的研究计划。"""
    logger.info("Planner 正在生成完整计划，locale: %s", state.get("locale", "en-US"))
    configurable = Configuration.from_runnable_config(config)
    plan_iterations = state["plan_iterations"] if state.get("plan_iterations", 0) else 0

    # 对于澄清功能：使用澄清后的研究主题
    if state.get("enable_clarification", False) and state.get(
        "clarified_research_topic"
    ):
        # 修改 state 以使用澄清后的话题
        modified_state = state.copy()
        modified_state["messages"] = [
            {"role": "user", "content": state["clarified_research_topic"]}
        ]
        modified_state["research_topic"] = state["clarified_research_topic"]
        messages = apply_prompt_template("planner", modified_state, configurable, state.get("locale", "en-US"))
        logger.info(
            f"澄清模式：使用澄清后的话题: {state['clarified_research_topic']}"
        )
    else:
        # 正常模式：使用完整的对话历史
        messages = apply_prompt_template("planner", state, configurable, state.get("locale", "en-US"))

    # 添加背景调查结果
    if state.get("enable_background_investigation") and state.get(
        "background_investigation_results"
    ):
        messages += [
            {
                "role": "user",
                "content": (
                    "用户查询的背景调查结果:\n"
                    + state["background_investigation_results"]
                    + "\n"
                ),
            }
        ]
    
    # 选择 LLM
    if configurable.enable_deep_thinking:
        llm = get_llm_by_type("reasoning")
    elif AGENT_LLM_MAP["planner"] == "basic":
        llm = get_llm_by_type("basic").with_structured_output(
            Plan,
            method="json_mode",
        )
    else:
        llm = get_llm_by_type(AGENT_LLM_MAP["planner"])

    # 检查是否超过最大计划迭代次数
    if plan_iterations >= configurable.max_plan_iterations:
        return Command(
            update=preserve_state_meta_fields(state),
            goto="reporter"
        )

    # 调用 LLM
    full_response = ""
    if AGENT_LLM_MAP["planner"] == "basic" and not configurable.enable_deep_thinking:
        response = llm.invoke(messages)
        full_response = response.model_dump_json(indent=4, exclude_none=True)
    else:
        response = llm.stream(messages)
        for chunk in response:
            full_response += chunk.content
            
    logger.debug(f"当前状态消息: {state['messages']}")
    logger.info(f"Planner 响应: {full_response}")

    try:
        curr_plan = json.loads(repair_json_output(full_response))
    except json.JSONDecodeError:
        logger.warning("Planner 响应不是有效的 JSON")
        if plan_iterations > 0:
            return Command(
                update=preserve_state_meta_fields(state),
                goto="reporter"
            )
        else:
            return Command(
                update=preserve_state_meta_fields(state),
                goto="__end__"
            )
    
    # 验证并修复计划
    if isinstance(curr_plan, dict):
        curr_plan = validate_and_fix_plan(curr_plan, configurable.enforce_web_search)

    if isinstance(curr_plan, dict) and curr_plan.get("has_enough_context"):
        logger.info("Planner 响应包含足够上下文。")
        new_plan = Plan.model_validate(curr_plan)
        return Command(
            update={
                "messages": [AIMessage(content=full_response, name="planner")],
                "current_plan": new_plan,
                **preserve_state_meta_fields(state),
            },
            goto="reporter",
        )
    
    # 否则，进入人工反馈
    return Command(
        update={
            "messages": [AIMessage(content=full_response, name="planner")],
            "current_plan": full_response,
            **preserve_state_meta_fields(state),
        },
        goto="human_feedback",
    )


def human_feedback_node(
    state: State, config: RunnableConfig
) -> Command[Literal["planner", "research_team", "reporter", "__end__"]]:
    """人工反馈节点，用于审查和批准计划。"""
    current_plan = state.get("current_plan", "")
    
    # 检查计划是否被自动接受
    auto_accepted_plan = state.get("auto_accepted_plan", False)
    if not auto_accepted_plan:
        feedback = interrupt("请审查计划。") # 中断等待用户输入

        # 处理 None 或空反馈
        if not feedback:
            logger.warning(f"收到空或 None 反馈: {feedback}。返回 planner 重新制定计划。")
            return Command(
                update=preserve_state_meta_fields(state),
                goto="planner"
            )

        # 规范化反馈字符串
        feedback_normalized = str(feedback).strip().upper()

        if feedback_normalized.startswith("[EDIT_PLAN]"):
            logger.info(f"用户请求编辑计划: {feedback}")
            return Command(
                update={
                    "messages": [
                        HumanMessage(content=feedback, name="feedback"),
                    ],
                    **preserve_state_meta_fields(state),
                },
                goto="planner",
            )
        elif feedback_normalized.startswith("[ACCEPTED]"):
            logger.info("计划被用户接受。")
        else:
            logger.warning(f"不支持的反馈格式: {feedback}。请使用 '[ACCEPTED]' 接受或 '[EDIT_PLAN]' 编辑。")
            return Command(
                update=preserve_state_meta_fields(state),
                goto="planner"
            )

    # 如果计划被接受，继续执行
    plan_iterations = state["plan_iterations"] if state.get("plan_iterations", 0) else 0
    goto = "research_team"
    
    try:
        current_plan = repair_json_output(current_plan)
        # 增加计划迭代次数
        plan_iterations += 1
        # 解析计划
        new_plan = json.loads(current_plan)
        
        # 验证并修复计划
        configurable = Configuration.from_runnable_config(config)
        new_plan = validate_and_fix_plan(new_plan, configurable.enforce_web_search)
        
    except json.JSONDecodeError:
        logger.warning("Planner 响应不是有效的 JSON")
        if plan_iterations > 1: # 迭代次数在此检查前已增加
            return Command(
                update=preserve_state_meta_fields(state),
                goto="reporter"
            )
        else:
            return Command(
                update=preserve_state_meta_fields(state),
                goto="__end__"
            )

    # 构建更新字典，安全处理 locale
    update_dict = {
        "current_plan": Plan.model_validate(new_plan),
        "plan_iterations": plan_iterations,
        **preserve_state_meta_fields(state),
    }

    # 仅当 new_plan 提供了有效的 locale 时才覆盖
    if new_plan.get("locale"):
        update_dict["locale"] = new_plan["locale"]
        
    return Command(
        update=update_dict,
        goto=goto,
    )


def coordinator_node(
    state: State, config: RunnableConfig
) -> Command[Literal["planner", "background_investigator", "coordinator", "__end__"]]:
    """
    Coordinator 节点，与客户沟通并处理澄清。
    [FIXED] 修复了此函数中严重的缩进错误。
    """
    logger.info("Coordinator 正在沟通。")
    configurable = Configuration.from_runnable_config(config)
    
    # 检查是否启用澄清
    enable_clarification = state.get("enable_clarification", False)
    initial_topic = state.get("research_topic", "")
    clarified_topic = initial_topic
    
    # 初始化将在两个分支中设置并在公共出口处使用的变量
    response = None
    goto = "__end__"
    locale = state.get("locale", "en-US")
    research_topic = initial_topic
    clarification_rounds = 0
    clarification_history = []
    
    # ============================================================
    # BRANCH 1: 澄清功能已禁用 (遗留模式)
    # ============================================================
    if not enable_clarification:
        # 使用正常提示，并明确指示跳过澄清
        messages = apply_prompt_template("coordinator", state, locale=state.get("locale", "en-US"))
        messages.append(
            {
                "role": "system",
                "content": "关键：澄清功能已禁用。您必须立即调用 handoff_to_planner 工具，并按原样使用用户的查询。不要提问或提及需要更多信息。",
            }
        )
        
        # 仅绑定 handoff_to_planner 工具
        tools = [handoff_to_planner]
        response = (
            get_llm_by_type(AGENT_LLM_MAP["coordinator"])
            .bind_tools(tools)
            .invoke(messages)
        )
        
        locale = state.get("locale", "en-US")
        logger.info(f"Coordinator locale: {locale}")
        research_topic = state.get("research_topic", "")
        
        # 处理遗留模式的工具调用
        if response.tool_calls:
            try:
                for tool_call in response.tool_calls:
                    tool_name = tool_call.get("name", "")
                    tool_args = tool_call.get("args", {})
                    if tool_name == "handoff_to_planner":
                        logger.info("转交给 planner")
                        goto = "planner"
                        # 提取 research_topic
                        if tool_args.get("research_topic"):
                            research_topic = tool_args.get("research_topic")
                        break
            except Exception as e:
                logger.error(f"处理工具调用出错: {e}")
                goto = "planner"
        # 分支1 结束，将流向底部的公共返回逻辑

    # ============================================================
    # BRANCH 2: 澄清功能已启用 (新功能)
    # ============================================================
    else:
        # 加载澄清状态
        clarification_rounds = state.get("clarification_rounds", 0)
        clarification_history = list(state.get("clarification_history", []) or [])
        clarification_history = [item for item in clarification_history if item]
        max_clarification_rounds = state.get("max_clarification_rounds", 3)
        
        # 准备 Coordinator 的消息
        state_messages = list(state.get("messages", []))
        messages = apply_prompt_template("coordinator", state, locale=state.get("locale", "en-US"))
        
        clarification_history = reconstruct_clarification_history(
            state_messages, clarification_history, initial_topic
        )
        clarified_topic, clarification_history = build_clarified_topic_from_history(
            clarification_history
        )
        
        logger.debug("澄清历史重建: %s", clarification_history)
        
        if clarification_history:
            initial_topic = clarification_history[0]
            latest_user_content = clarification_history[-1]
        else:
            latest_user_content = ""

        # 添加第一轮的澄清状态
        if clarification_rounds == 0:
            messages.append(
                {
                    "role": "system",
                    "content": "澄清模式已启用。请遵循您指示中的“澄清流程”指南。",
                }
            )
            
        current_response = latest_user_content or "无响应"
        logger.info(
            "澄清轮次 %s/%s | 话题: %s | 当前用户响应: %s",
            clarification_rounds,
            max_clarification_rounds,
            clarified_topic or initial_topic,
            current_response,
        )
        
        clarification_context = f"""继续澄清 (轮次 {clarification_rounds}/{max_clarification_rounds}):
        用户的最新响应: {current_response}
        询问剩余的缺失维度。不要重复提问或开启新话题。"""
        messages.append({"role": "system", "content": clarification_context})

        # 绑定两个澄清工具
        tools = [handoff_to_planner, handoff_after_clarification]

        # 检查是否已达到最大轮次
        if clarification_rounds >= max_clarification_rounds:
            # 达到最大轮次 - 强制转交
            logger.warning(
                f"达到最大澄清轮次 ({max_clarification_rounds})。强制转交给 planner。使用准备好的澄清后话题: {clarified_topic}"
            )
            messages.append(
                {
                    "role": "system",
                    "content": f"已达最大轮次。您必须调用 handoff_after_clarification (不是 handoff_to_planner)，使用适当的 locale 和 research_topic='{clarified_topic}'。不要再提问。",
                }
            )
            
        response = (
            get_llm_by_type(AGENT_LLM_MAP["coordinator"])
            .bind_tools(tools)
            .invoke(messages)
        )
        
        logger.debug(f"当前状态消息: {state['messages']}")

        # 初始化响应处理变量
        goto = "__end__"
        locale = state.get("locale", "en-US")
        research_topic = (
            clarification_history[0]
            if clarification_history
            else state.get("research_topic", "")
        )
        if not clarified_topic:
            clarified_topic = research_topic

        # --- 处理 LLM 响应 ---
        # 没有工具调用 - LLM 正在询问一个澄清问题
        if not response.tool_calls and response.content:
            if clarification_rounds >= max_clarification_rounds:
                # 即使 LLM 想提问，但已达最大轮次，强制转交
                logger.warning(
                    f"达到最大澄清轮次 ({max_clarification_rounds})。 "
                    "LLM 没有调用转交工具，强制转交给 planner。"
                )
                goto = "planner"
                # 继续执行到公共返回逻辑
            else:
                # 继续澄清流程
                clarification_rounds += 1
                logger.info(
                    f"澄清响应: {clarification_rounds}/{max_clarification_rounds}: {response.content}"
                )
                
                # 将 coordinator 的问题附加到消息中
                updated_messages = list(state_messages)
                if response.content:
                    updated_messages.append(
                        HumanMessage(content=response.content, name="coordinator")
                    )
                
                # !! 关键：这是分支2的提前退出，用于中断以获取用户输入 !!
                return Command(
                    update={
                        "messages": updated_messages,
                        "locale": locale,
                        "research_topic": research_topic,
                        "resources": configurable.resources,
                        "clarification_rounds": clarification_rounds,
                        "clarification_history": clarification_history,
                        "clarified_research_topic": clarified_topic,
                        "is_clarification_complete": False,
                        "goto": goto,
                        "__interrupt__": [("coordinator", response.content)],
                    },
                    goto=goto,
                )
        else:
            # LLM 调用了工具（转交）或没有内容 - 澄清完成
            if response.tool_calls:
                logger.info(
                    f"澄清在 {clarification_rounds} 轮后完成。LLM 调用了转交工具。"
                )
            else:
                logger.warning("LLM 响应既无内容也无工具调用。")
            # goto 将在下面的公共逻辑中设置
            # 分支2结束，将流向底部的公共返回逻辑
    
    # ============================================================
    # [FIXED] Final: 构建并返回 Command (两个分支的公共退出路径)
    # 此块代码已从 'else' 块中反向缩进，以修复原始 bug
    # ============================================================
    
    messages = list(state.get("messages", []))
    if response and response.content:
        messages.append(HumanMessage(content=response.content, name="coordinator"))

    # 处理两个分支的工具调用
    if response and response.tool_calls:
        try:
            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name", "")
                tool_args = tool_call.get("args", {})
                if tool_name in ["handoff_to_planner", "handoff_after_clarification"]:
                    logger.info("转交给 planner")
                    goto = "planner"
                    
                    if not enable_clarification and tool_args.get("research_topic"):
                        research_topic = tool_args["research_topic"]
                        
                    if enable_clarification:
                        logger.info(
                            "使用准备好的澄清后话题: %s",
                            clarified_topic or research_topic,
                        )
                    else:
                        logger.info(
                            "使用 research_topic 进行转交: %s", research_topic
                        )
                    break
        except Exception as e:
            logger.error(f"处理工具调用出错: {e}")
            goto = "planner"
    elif not enable_clarification: # 仅在非澄清模式下，无工具调用才是个问题
        # 未检测到工具调用 - 回退到 planner
        logger.warning(
            "LLM 未调用任何工具。这可能表示模型的工具调用有问题。"
            "回退到 planner 以确保研究继续进行。"
        )
        logger.debug(f"Coordinator 响应内容: {response.content if response else 'N/A'}")
        logger.debug(f"Coordinator 响应对象: {response}")
        # 回退到 planner
        goto = "planner"
    
    # 如果启用，应用 background_investigation 路由（统一逻辑）
    if goto == "planner" and state.get("enable_background_investigation"):
        goto = "background_investigator"
        
    # 为状态变量设置默认值（以防在遗留模式下未定义）
    if not enable_clarification:
        clarification_rounds = 0
        clarification_history = []
        
    clarified_research_topic_value = clarified_topic or research_topic

    # 最终的公共返回
    return Command(
        update={
            "messages": messages,
            "locale": locale,
            "research_topic": research_topic,
            "clarified_research_topic": clarified_research_topic_value,
            "resources": configurable.resources,
            "clarification_rounds": clarification_rounds,
            "clarification_history": clarification_history,
            "is_clarification_complete": goto != "coordinator",
            "goto": goto,
        },
        goto=goto,
    )


def reporter_node(state: State, config: RunnableConfig):
    """Reporter 节点，撰写最终报告。"""
    logger.info("Reporter 正在撰写最终报告")
    configurable = Configuration.from_runnable_config(config)
    current_plan = state.get("current_plan")
    
    input_ = {
        "messages": [
            HumanMessage(
                f"# 研究要求\n\n## 任务\n\n{current_plan.title}\n\n## 描述\n\n{current_plan.thought}"
            )
        ],
        "locale": state.get("locale", "en-US"),
    }
    
    invoke_messages = apply_prompt_template("reporter", input_, configurable, input_.get("locale", "en-US"))
    observations = state.get("observations", [])

    # 添加关于新报告格式、引用样式和表格使用的提醒
    invoke_messages.append(
        HumanMessage(
            content="""重要：请按照提示中的格式构建您的报告。请记住包括：

1.  **关键点** - 最重要发现的项目符号列表
2.  **概述** - 对主题的简要介绍
3.  **详细分析** - 组织成逻辑清晰的章节
4.  **调研说明** (可选) - 适用于更全面的报告
5.  **关键引用** - 在末尾列出所有参考文献

对于引用，**请勿在文本中包含内联引用**。相反，请将所有引用放在末尾的“关键引用”部分，使用以下格式：
`- [来源标题](URL)`
为提高可读性，请在每个引用之间留一个空行。

**优先使用 MARKDOWN 表格** 进行数据呈现和比较。在呈现比较数据、统计数据、功能或选项时，请尽量使用表格。表格应具有清晰的表头和对齐的列。示例如下：

| 功能 | 描述 | 优点 | 缺点 |
|---|---|---|---|
| 功能 1 | 描述 1 | 优点 1 | 缺点 1 |
| 功能 2 | 描述 2 | 优点 2 | 缺点 2 |""",
            name="system",
        )
    )

    observation_messages = []
    for observation in observations:
        observation_messages.append(
            HumanMessage(
                content=f"以下是针对研究任务的一些观察结果：\n\n{observation}",
                name="observation",
            )
        )

    # 上下文压缩
    llm_token_limit = get_llm_token_limit_by_type(AGENT_LLM_MAP["reporter"])
    compressed_state = ContextManager(llm_token_limit).compress_messages(
        {"messages": observation_messages}
    )
    
    invoke_messages += compressed_state.get("messages", [])
    logger.debug(f"当前的 invoke messages: {invoke_messages}")
    
    response = get_llm_by_type(AGENT_LLM_MAP["reporter"]).invoke(invoke_messages)
    response_content = response.content
    logger.info(f"reporter 响应: {response_content}")
    
    return {"final_report": response_content}


def research_team_node(state: State):
    """Research team 节点，协调多个代理协作完成任务。"""
    logger.info("Research team 正在协作执行任务。")
    logger.debug("进入 research_team_node - 协调 researcher 和 coder 代理")
    # [FIXED] 修复了缩进
    pass


async def _execute_agent_step(
    state: State, agent, agent_name: str
) -> Command[Literal["research_team"]]:
    """帮助函数，使用指定的代理执行一个步骤。"""
    logger.debug(f"[_execute_agent_step] 开始执行代理: {agent_name}")
    current_plan = state.get("current_plan")
    plan_title = current_plan.title
    observations = state.get("observations", [])
    logger.debug(f"[_execute_agent_step] 计划标题: {plan_title}, 观察结果数量: {len(observations)}")

    # 查找第一个未执行的步骤
    current_step = None
    completed_steps = []
    for idx, step in enumerate(current_plan.steps):
        if not step.execution_res:
            current_step = step
            logger.debug(f"[_execute_agent_step] 在索引 {idx} 找到未执行步骤: {step.title}")
            break
        else:
            completed_steps.append(step)

    if not current_step:
        logger.warning(f"[_execute_agent_step] 在 {len(current_plan.steps)} 个总步骤中未找到未执行步骤")
        return Command(
            update=preserve_state_meta_fields(state),
            goto="research_team"
        )

    logger.info(f"[_execute_agent_step] 正在执行步骤: {current_step.title}, 代理: {agent_name}")
    logger.debug(f"[_execute_agent_step] 已完成步骤数量: {len(completed_steps)}")
    
    # 格式化已完成步骤的信息
    completed_steps_info = ""
    if completed_steps:
        completed_steps_info = "# 已完成的研究步骤\n\n"
        for i, step in enumerate(completed_steps):
            completed_steps_info += f"## 已完成步骤 {i + 1}: {step.title}\n\n"
            completed_steps_info += f"<finding>\n{step.execution_res}\n</finding>\n\n"

    # 准备代理的输入
    agent_input = {
        "messages": [
            HumanMessage(
                content=f"# 研究主题\n\n{plan_title}\n\n{completed_steps_info}# 当前步骤\n\n## 标题\n\n{current_step.title}\n\n## 描述\n\n{current_step.description}\n\n## 语言区域\n\n{state.get('locale', 'en-US')}"
            )
        ]
    }
    
    # 为 researcher 代理添加引用提醒
    if agent_name == "researcher":
        if state.get("resources"):
            resources_info = "**用户提到了以下资源文件:**\n\n"
            for resource in state.get("resources"):
                resources_info += f"- {resource.title} ({resource.description})\n"
            agent_input["messages"].append(
                HumanMessage(
                    content=resources_info
                    + "\n\n"
                    + "您必须使用 **local_search_tool** 从资源文件中检索信息。",
                )
            )
            
        agent_input["messages"].append(
            HumanMessage(
                content="""重要：请勿在文本中包含内联引用。
                请跟踪所有来源，并在末尾添加一个“参考文献”部分，使用链接引用格式。
                为提高可读性，请在每个引用之间留一个空行。
                每个引用的格式如下：\n- [来源标题](URL)\n\n- [另一个来源](URL)""",
                name="system",
            )
        )

    # 调用代理
    default_recursion_limit = 25
    try:
        env_value_str = os.getenv("AGENT_RECURSION_LIMIT", str(default_recursion_limit))
        parsed_limit = int(env_value_str)
        if parsed_limit > 0:
            recursion_limit = parsed_limit
            logger.info(f"递归限制设置为: {recursion_limit}")
        else:
            logger.warning(
                f"AGENT_RECURSION_LIMIT 值 '{env_value_str}' (解析为 {parsed_limit}) 不是正数。"
                f"使用默认值 {default_recursion_limit}。"
            )
            recursion_limit = default_recursion_limit
    except ValueError:
        raw_env_value = os.getenv("AGENT_RECURSION_LIMIT")
        logger.warning(
            f"无效的 AGENT_RECURSION_LIMIT 值: '{raw_env_value}'。"
            f"使用默认值 {default_recursion_limit}。"
        )
        recursion_limit = default_recursion_limit

    logger.info(f"代理输入: {agent_input}")
    
    # 在调用代理前验证消息内容
    try:
        validated_messages = validate_message_content(agent_input["messages"])
        agent_input["messages"] = validated_messages
    except Exception as validation_error:
        logger.error(f"验证代理输入消息时出错: {validation_error}")
        # （继续尝试执行，或者在这里抛出错误）
        
    try:
        result = await agent.ainvoke(
            input=agent_input, config={"recursion_limit": recursion_limit}
        )
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        error_message = f"执行 {agent_name} 代理步骤 '{current_step.title}' 时出错: {str(e)}"
        logger.exception(error_message)
        logger.error(f"完整回溯:\n{error_traceback}")
        
        # 针对内容相关错误的增强型错误诊断
        if "Field required" in str(e) and "content" in str(e):
            logger.error("检测到消息内容验证错误")
            for i, msg in enumerate(agent_input.get('messages', [])):
                logger.error(f"消息 {i}: type={type(msg).__name__}, "
                             f"has_content={hasattr(msg, 'content')}, "
                             f"content_type={type(msg.content).__name__ if hasattr(msg, 'content') else 'N/A'}, "
                             f"content_len={len(str(msg.content)) if hasattr(msg, 'content') and msg.content else 0}")
                             
        detailed_error = f"[错误] {agent_name.capitalize()} 代理错误\n\n步骤: {current_step.title}\n\n错误详情:\n{str(e)}\n\n请检查日志获取更多信息。"
        current_step.execution_res = detailed_error
        
        return Command(
            update={
                "messages": [
                    HumanMessage(
                        content=detailed_error,
                        name=agent_name,
                    )
                ],
                "observations": observations + [detailed_error],
                **preserve_state_meta_fields(state),
            },
            goto="research_team",
        )

    # 处理结果
    response_content = result["messages"][-1].content
    # 清理响应，移除多余 token
    response_content = sanitize_tool_response(str(response_content))
    logger.debug(f"{agent_name.capitalize()} 完整响应: {response_content}")
    
    # 更新步骤的执行结果
    current_step.execution_res = response_content
    logger.info(f"步骤 '{current_step.title}' 由 {agent_name} 执行完毕")

    return Command(
        update={
            "messages": [
                HumanMessage(
                    content=response_content,
                    name=agent_name,
                )
            ],
            "observations": observations + [response_content],
            **preserve_state_meta_fields(state),
        },
        goto="research_team",
    )


async def _setup_and_execute_agent_step(
    state: State,
    config: RunnableConfig,
    agent_type: str,
    default_tools: list,
) -> Command[Literal["research_team"]]:
    """
    帮助函数：设置代理工具并执行步骤。
    处理 researcher_node 和 coder_node 的通用逻辑：
    1. 配置 MCP 服务器和工具
    2. 创建带工具的代理
    3. 执行代理
    """
    configurable = Configuration.from_runnable_config(config)
    mcp_servers = {}
    enabled_tools = {}

    # 提取此代理类型的 MCP 服务器配置
    if configurable.mcp_settings:
        for server_name, server_config in configurable.mcp_settings["servers"].items():
            if (
                server_config["enabled_tools"]
                and agent_type in server_config["add_to_agents"]
            ):
                mcp_servers[server_name] = {
                    k: v
                    for k, v in server_config.items()
                    if k in ("transport", "command", "args", "url", "env", "headers")
                }
                for tool_name in server_config["enabled_tools"]:
                    enabled_tools[tool_name] = server_name

    # 如果 MCP 可用，创建并执行带 MCP 工具的代理
    if mcp_servers:
        client = MultiServerMCPClient(mcp_servers)
        loaded_tools = default_tools[:]
        all_tools = await client.get_tools()
        for tool in all_tools:
            if tool.name in enabled_tools:
                tool.description = (
                    f"由 '{enabled_tools[tool.name]}' 提供支持。\n{tool.description}"
                )
                loaded_tools.append(tool)
                
        llm_token_limit = get_llm_token_limit_by_type(AGENT_LLM_MAP[agent_type])
        pre_model_hook = partial(ContextManager(llm_token_limit, 3).compress_messages)
        
        agent = create_agent(
            agent_type,
            agent_type,
            loaded_tools,
            agent_type,
            pre_model_hook,
            interrupt_before_tools=configurable.interrupt_before_tools,
        )
        return await _execute_agent_step(state, agent, agent_type)
    else:
        # 如果没有配置 MCP，使用默认工具
        llm_token_limit = get_llm_token_limit_by_type(AGENT_LLM_MAP[agent_type])
        pre_model_hook = partial(ContextManager(llm_token_limit, 3).compress_messages)
        
        agent = create_agent(
            agent_type,
            agent_type,
            default_tools,
            agent_type,
            pre_model_hook,
            interrupt_before_tools=configurable.interrupt_before_tools,
        )
        return await _execute_agent_step(state, agent, agent_type)


async def researcher_node(
    state: State, config: RunnableConfig
) -> Command[Literal["research_team"]]:
    """Researcher 节点，执行研究任务。"""
    logger.info("Researcher 节点正在研究。")
    logger.debug("[researcher_node] 启动 researcher 代理")
    configurable = Configuration.from_runnable_config(config)
    logger.debug(f"[researcher_node] 最大搜索结果数: {configurable.max_search_results}")
    
    tools = [get_web_search_tool(configurable.max_search_results), crawl_tool]
    
    retriever_tool = get_retriever_tool(state.get("resources", []))
    if retriever_tool:
        logger.debug("[researcher_node] 添加 retriever_tool 到工具列表")
        tools.insert(0, retriever_tool)
        
    logger.info(f"[researcher_node] Researcher 工具数量: {len(tools)}")
    logger.debug(f"[researcher_node] Researcher 工具: {[tool.name if hasattr(tool, 'name') else str(tool) for tool in tools]}")
    
    return await _setup_and_execute_agent_step(
        state,
        config,
        "researcher",
        tools,
    )


async def coder_node(
    state: State, config: RunnableConfig
) -> Command[Literal["research_team"]]:
    """Coder 节点，执行代码分析和执行。"""
    logger.info("Coder 节点正在编码。")
    logger.debug("[coder_node] 启动 coder 代理 (带 python_repl_tool)")
    
    return await _setup_and_execute_agent_step(
        state,
        config,
        "coder",
        [python_repl_tool],
    )