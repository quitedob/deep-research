# -*- coding: utf-8 -*-
"""
RAG核心逻辑模块：管理RAG状态、构建提示词、整合检索和生成
"""

import asyncio
import json
from pathlib import Path
from typing import Tuple, Optional

from src.config.logging import get_logger
from .config import (DEFAULT_RAG_MODE, DYNAMIC_PROMPT_FILE)
from .knowledge_base import KnowledgeBase

logger = get_logger("rag_core")

class RAGCore:
    """
    RAG核心逻辑类，负责管理RAG状态、构建提示词。
    """

    def __init__(self, llm_client):
        """
        初始化RAG核心。
        :param llm_client: 一个LLMClient的实例。
        """
        self.llm_client = llm_client # 注入共享的LLM客户端
        self.use_rag = DEFAULT_RAG_MODE
        self.current_kb_name: Optional[str] = None
        self.kb_instance: Optional[KnowledgeBase] = None
        self.system_prompt = self._load_system_prompt()
        logger.info("RAG核心初始化完成，并已连接到共享LLM客户端。")

    def _load_system_prompt(self) -> str:
        """从文件加载动态提示词，如果文件不存在则创建默认值。"""
        try:
            if DYNAMIC_PROMPT_FILE.exists():
                with open(DYNAMIC_PROMPT_FILE, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            else:
                default_dynamic_prompt = "请根据我提供的上下文，以专业、严谨的风格回答问题。"
                with open(DYNAMIC_PROMPT_FILE, 'w', encoding='utf-8') as f:
                    f.write(default_dynamic_prompt)
                return default_dynamic_prompt
        except Exception as e:
            logger.error(f"加载或创建动态提示词文件失败: {e}")
            return "请根据上下文回答问题。"

    def update_system_prompt(self, new_prompt: str):
        """更新动态系统提示词并保存到文件。"""
        try:
            with open(DYNAMIC_PROMPT_FILE, 'w', encoding='utf-8') as f:
                f.write(new_prompt)
            self.system_prompt = new_prompt
            logger.info(f"系统提示词已更新为: '{new_prompt[:50]}...'")
            return True
        except Exception as e:
            logger.error(f"更新系统提示词文件失败: {e}")
            return False

    def set_rag_mode(self, use_rag: bool):
        """设置RAG模式的开关。"""
        self.use_rag = use_rag
        logger.info(f"RAG 模式已切换为: {'ON' if use_rag else 'OFF'}")

    def switch_kb(self, kb_name: Optional[str]) -> bool:
        """
        切换当前使用的知识库。
        这将创建或销毁一个 KnowledgeBase 实例。
        """
        if kb_name and kb_name == self.current_kb_name:
            logger.info(f"知识库 '{kb_name}' 已是当前激活的知识库。")
            return True

        # 检查知识库是否存在
        existing_kbs = KnowledgeBase.list_kbs()
        if kb_name and kb_name not in existing_kbs:
            logger.warning(f"尝试切换到不存在的知识库: '{kb_name}'")
            self.current_kb_name = None
            self.kb_instance = None
            return False
        
        if kb_name:
            # 切换到新的知识库
            try:
                self.kb_instance = KnowledgeBase(kb_name)
                self.current_kb_name = kb_name
                logger.info(f"当前知识库已切换为: '{kb_name}'")
            except Exception as e:
                logger.error(f"实例化知识库 '{kb_name}' 失败: {e}")
                self.current_kb_name = None
                self.kb_instance = None
                return False
        else:
            # 取消使用知识库
            self.current_kb_name = None
            self.kb_instance = None
            logger.info("已取消使用知识库。")
            
        return True

    def set_current_kb(self, kb_name: Optional[str]):
        """
        安全地设置当前对话使用的知识库。
        这是 switch_kb 的别名，用于向后兼容或更清晰的意图。
        """
        self.switch_kb(kb_name)

    def _build_prompt(self, user_query: str, context: str) -> Tuple[str, Optional[str]]:
        """
        中文提示词优化版：
        - 不允许出现"根据你的/您提供的参考信息"等元叙述
        - 就事论事，直接回答
        - 有上下文就融合表达，不要显式提及"参考/资料/文档/上下文"等字眼
        :return: (final_user_query, system_prompt_override)
        """
        additional_requirements = self.system_prompt

        # 检查用户查询中是否包含数字人背景提示
        avatar_bg_prompt = ""
        if "【数字人背景提示】" in user_query:
            # 提取背景提示部分
            parts = user_query.split("【数字人背景提示】", 1)
            if len(parts) == 2:
                user_query = parts[0].strip()
                avatar_bg_prompt = parts[1].strip()

        if self.use_rag and context:
            # RAG模式且有上下文 - 优化版提示词
            # 组装可读的context，不要附加任何"参考信息"字样
            context_block = context.strip()
            
            # 构建系统提示词 - 要求直接回答，禁止元叙述
            sys_prompt = (
                "你是可靠的中文答复助手，要求："
                "1) 直接回答，不要出现"根据/依据/参考/资料/上下文/你提供的"等字眼；"
                "2) 先给结论，再列1-3条要点；"
                "3) 若把握不足，使用"可能/不确定"，再给继续核实的建议；"
                "4) 语气自然、简洁、礼貌；"
                "5) 禁止输出表情符号与过度客套。"
            )
            
            # 用户提示词 - 自然融合上下文
            context_line = f"已知要点：\n{context_block}\n" if context_block else ""

            # 组合附加要求：系统提示词 + 数字人背景提示词
            combined_requirements = additional_requirements
            if avatar_bg_prompt:
                if combined_requirements:
                    combined_requirements += f"\n\n数字人背景信息：{avatar_bg_prompt}"
                else:
                    combined_requirements = f"数字人背景信息：{avatar_bg_prompt}"

            requirements_line = f"附加要求：{combined_requirements}\n" if combined_requirements else ""
            final_user_query = (
                f"问题：{user_query.strip()}\n"
                f"{context_line}"
                f"{requirements_line}"
                "请按要求作答。"
            )
            
            # 使用新的系统提示词覆盖默认的
            system_prompt_override = sys_prompt
            return final_user_query, system_prompt_override
        else:
            # 纯LLM模式或无上下文
            # 组合附加要求：系统提示词 + 数字人背景提示词
            combined_requirements = additional_requirements
            if avatar_bg_prompt:
                if combined_requirements:
                    combined_requirements += f"\n\n数字人背景信息：{avatar_bg_prompt}"
                else:
                    combined_requirements = f"数字人背景信息：{avatar_bg_prompt}"

            requirements_line = f"附加要求: {combined_requirements}\n\n" if combined_requirements else ""
            final_user_query = (
                 f"{requirements_line}"
                 f"问题: {user_query}"
            )
            # 使用LLMClient中默认的系统提示词
            system_prompt_override = None
            return final_user_query, system_prompt_override
            
    async def get_response(self, user_query: str, external_system_prompt: Optional[str] = None):
        """
        根据当前RAG模式，获取LLM的响应。
        :param user_query: 用户查询
        :param external_system_prompt: 外部传入的系统提示词，用于覆盖默认的RAG系统提示词
        """
        context = ""
        # 1. 如果RAG模式开启且已选择知识库实例，则进行检索
        if self.use_rag and self.kb_instance:
            # KnowledgeBase 的 search 方法现在是同步的，但在一个IO密集型应用中，
            # 将CPU密集型或潜在阻塞的操作（如模型推理）放入线程池是最佳实践。
            loop = asyncio.get_event_loop()
            query_result = await loop.run_in_executor(
                None,
                self.kb_instance.search,
                user_query
            )

            if query_result and query_result.hits:
                context = "\n\n---\n\n".join([hit.text for hit in query_result.hits])

        # 2. 构建最终的提示词和可选的系统提示词覆盖
        final_query, system_prompt_override = self._build_prompt(user_query, context)

        # 3. 如果有外部系统提示词，则合并或覆盖
        if external_system_prompt:
            if system_prompt_override:
                # 合并外部系统提示词和RAG的系统提示词
                system_prompt_override = f"{external_system_prompt}\n\n{system_prompt_override}"
            else:
                # 直接使用外部系统提示词
                system_prompt_override = external_system_prompt

        # 4. 使用共享的LLM客户端进行流式调用
        async for chunk in self.llm_client.ask(final_query, system_prompt_override=system_prompt_override):
            yield chunk