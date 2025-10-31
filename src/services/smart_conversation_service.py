# -*- coding: utf-8 -*-
"""
智能对话编排服务
实现消息计数、模式切换、RAG增强、联网搜索等核心功能
"""

from __future__ import annotations

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from .conversation_service import ConversationService
from .network_need_detector import get_network_need_detector
from src.config.loader.config_loader import get_settings
from src.config.logging.logging import get_logger

logger = get_logger("smart_conversation")


class ConversationMode(str, Enum):
    """对话模式枚举"""
    NORMAL = "normal"  # 普通对话模式
    RAG_ENHANCED = "rag_enhanced"  # RAG增强模式


class SmartConversationService:
    """智能对话编排服务"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.conversation_service = ConversationService(db_session)
        self.network_detector = get_network_need_detector()
        self.settings = get_settings()

        # 配置参数
        self.message_threshold = self.settings.smart_conversation_message_threshold
        self.memory_threshold = self.settings.smart_conversation_memory_threshold
        self.enable_auto_rag = self.settings.smart_conversation_enable_auto_rag
        self.enable_auto_search = self.settings.smart_conversation_enable_auto_search
        self.rag_top_k = self.settings.smart_conversation_rag_top_k
        self.rag_score_threshold = self.settings.smart_conversation_rag_score_threshold
        self.search_limit = self.settings.smart_conversation_search_limit
        self.enable_reranking = self.settings.smart_conversation_enable_reranking

        # 会话状态缓存
        self._session_states: Dict[str, Dict[str, Any]] = {}

    async def process_message(
        self,
        user_id: str,
        session_id: str,
        message: str,
        force_mode: Optional[ConversationMode] = None
    ) -> Dict[str, Any]:
        """
        处理用户消息（核心编排逻辑）

        Args:
            user_id: 用户ID
            session_id: 会话ID
            message: 用户消息
            force_mode: 强制使用的模式（可选）

        Returns:
            处理结果，包含响应和元数据
        """
        try:
            # 1. 获取或初始化会话状态
            session_state = await self._get_session_state(user_id, session_id)

            # 2. 添加用户消息到历史
            await self.conversation_service.add_message(
                user_id=user_id,
                session_id=session_id,
                role="user",
                content=message
            )

            # 3. 更新消息计数
            session_state["message_count"] += 1
            current_count = session_state["message_count"]

            logger.info(f"会话 {session_id} 消息计数: {current_count}")

            # 4. 检测对话模式
            if force_mode:
                current_mode = force_mode
            else:
                current_mode = await self._determine_mode(session_state, current_count)

            session_state["current_mode"] = current_mode.value

            # 5. 检测是否需要联网搜索
            network_detection = self.network_detector.detect(message)
            needs_network = network_detection["needs_network"] and self.enable_auto_search

            logger.info(
                f"模式: {current_mode.value}, 需要联网: {needs_network}, "
                f"置信度: {network_detection['confidence']:.2f}"
            )

            # 6. 根据模式和需求处理消息
            if current_mode == ConversationMode.NORMAL:
                # 普通对话模式
                response = await self._process_normal_mode(
                    user_id=user_id,
                    session_id=session_id,
                    message=message,
                    needs_network=needs_network,
                    network_detection=network_detection
                )
            else:
                # RAG增强模式
                response = await self._process_rag_mode(
                    user_id=user_id,
                    session_id=session_id,
                    message=message,
                    needs_network=needs_network,
                    network_detection=network_detection
                )

            # 7. 添加助手响应到历史
            await self.conversation_service.add_message(
                user_id=user_id,
                session_id=session_id,
                role="assistant",
                content=response["content"]
            )

            # 8. 检查是否需要触发记忆摘要
            if current_count >= self.memory_threshold:
                await self._trigger_memory_summary(user_id, session_id, session_state)

            # 9. 更新会话状态
            session_state["last_message_time"] = datetime.utcnow().isoformat()
            await self._save_session_state(session_id, session_state)

            # 10. 构建返回结果
            result = {
                "success": True,
                "content": response["content"],
                "mode": current_mode.value,
                "message_count": current_count,
                "needs_network": needs_network,
                "network_detection": network_detection,
                "rag_used": response.get("rag_used", False),
                "search_used": response.get("search_used", False),
                "sources": response.get("sources", []),
                "metadata": {
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "mode_switched": session_state.get("mode_switched", False)
                }
            }

            return result

        except Exception as e:
            logger.error(f"处理消息失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "content": "抱歉，处理您的消息时出现了错误，请稍后重试。"
            }

    async def _get_session_state(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """获取或初始化会话状态"""
        if session_id not in self._session_states:
            # 从数据库获取消息计数
            session_info = await self.conversation_service.get_conversation(
                user_id=user_id,
                session_id=session_id
            )

            message_count = session_info.get("message_count", 0) if session_info else 0

            self._session_states[session_id] = {
                "session_id": session_id,
                "user_id": user_id,
                "message_count": message_count,
                "current_mode": ConversationMode.NORMAL.value,
                "mode_switched": False,
                "memory_summary_triggered": False,
                "last_message_time": datetime.utcnow().isoformat(),
                "created_at": datetime.utcnow().isoformat()
            }

        return self._session_states[session_id]

    async def _save_session_state(self, session_id: str, state: Dict[str, Any]) -> None:
        """保存会话状态"""
        self._session_states[session_id] = state

    async def _determine_mode(
        self,
        session_state: Dict[str, Any],
        message_count: int
    ) -> ConversationMode:
        """
        确定对话模式

        Args:
            session_state: 会话状态
            message_count: 消息计数

        Returns:
            对话模式
        """
        if not self.enable_auto_rag:
            return ConversationMode.NORMAL

        # 检查是否达到阈值
        if message_count >= self.message_threshold:
            # 切换到RAG增强模式
            if session_state["current_mode"] == ConversationMode.NORMAL.value:
                session_state["mode_switched"] = True
                logger.info(f"会话 {session_state['session_id']} 切换到RAG增强模式")

            return ConversationMode.RAG_ENHANCED

        return ConversationMode.NORMAL

    async def _process_normal_mode(
        self,
        user_id: str,
        session_id: str,
        message: str,
        needs_network: bool,
        network_detection: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理普通对话模式

        Args:
            user_id: 用户ID
            session_id: 会话ID
            message: 用户消息
            needs_network: 是否需要联网
            network_detection: 联网检测结果

        Returns:
            响应结果
        """
        logger.info(f"使用普通对话模式处理消息")

        # 获取对话历史
        messages_result = await self.conversation_service.get_conversation_messages(
            user_id=user_id,
            session_id=session_id,
            limit=10  # 最近10条消息
        )

        history = messages_result.get("messages", [])

        # 如果需要联网，触发搜索
        search_results = []
        search_used = False

        if needs_network:
            try:
                search_results = await self._perform_web_search(
                    query=message,
                    limit=self.search_limit
                )
                search_used = len(search_results) > 0
                logger.info(f"联网搜索返回 {len(search_results)} 个结果")
            except Exception as e:
                logger.error(f"联网搜索失败: {e}")

        # 调用LLM生成响应
        llm_response = await self._generate_llm_response(
            message=message,
            history=history,
            search_results=search_results,
            mode="normal"
        )

        return {
            "content": llm_response,
            "rag_used": False,
            "search_used": search_used,
            "sources": search_results
        }

    async def _process_rag_mode(
        self,
        user_id: str,
        session_id: str,
        message: str,
        needs_network: bool,
        network_detection: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理RAG增强模式

        Args:
            user_id: 用户ID
            session_id: 会话ID
            message: 用户消息
            needs_network: 是否需要联网
            network_detection: 联网检测结果

        Returns:
            响应结果
        """
        logger.info(f"使用RAG增强模式处理消息")

        # 获取对话历史
        messages_result = await self.conversation_service.get_conversation_messages(
            user_id=user_id,
            session_id=session_id,
            limit=10
        )

        history = messages_result.get("messages", [])

        # 1. 知识库检索
        rag_results = []
        rag_used = False

        try:
            rag_results = await self._perform_rag_search(
                query=message,
                user_id=user_id,
                top_k=self.rag_top_k,
                score_threshold=self.rag_score_threshold
            )
            rag_used = len(rag_results) > 0
            logger.info(f"RAG检索返回 {len(rag_results)} 个结果")
        except Exception as e:
            logger.error(f"RAG检索失败: {e}")

        # 2. 如果需要联网，触发搜索
        search_results = []
        search_used = False

        if needs_network:
            try:
                search_results = await self._perform_web_search(
                    query=message,
                    limit=self.search_limit
                )
                search_used = len(search_results) > 0
                logger.info(f"联网搜索返回 {len(search_results)} 个结果")
            except Exception as e:
                logger.error(f"联网搜索失败: {e}")

        # 3. 合并所有上下文
        all_sources = rag_results + search_results

        # 4. 调用LLM生成响应
        llm_response = await self._generate_llm_response(
            message=message,
            history=history,
            search_results=all_sources,
            mode="rag_enhanced"
        )

        return {
            "content": llm_response,
            "rag_used": rag_used,
            "search_used": search_used,
            "sources": all_sources
        }

    async def _perform_rag_search(
        self,
        query: str,
        user_id: str,
        top_k: int = 5,
        score_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        执行RAG检索

        Args:
            query: 查询文本
            user_id: 用户ID
            top_k: 返回结果数
            score_threshold: 分数阈值

        Returns:
            检索结果列表
        """
        try:
            from src.core.rag.pgvector_store import get_pgvector_store

            pgvector_store = get_pgvector_store()

            # 执行向量搜索
            search_results = await pgvector_store.search(
                query=query,
                top_k=top_k,
                filter_metadata={"user_id": user_id},
                score_threshold=score_threshold
            )

            # 转换结果格式
            results = []
            for doc, score in search_results:
                results.append({
                    "type": "rag",
                    "content": doc.content,
                    "score": score,
                    "source": doc.metadata.get("filename", "unknown"),
                    "metadata": doc.metadata
                })

            return results

        except Exception as e:
            logger.error(f"RAG检索失败: {e}")
            return []

    async def _perform_web_search(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        执行联网搜索

        Args:
            query: 查询文本
            limit: 结果数限制

        Returns:
            搜索结果列表
        """
        try:
            from src.services.unified_search import get_unified_search_service

            search_service = get_unified_search_service()

            # 执行搜索
            result = await search_service.search(
                query=query,
                search_limit=limit
            )

            if not result.get("success"):
                logger.warning(f"搜索失败: {result.get('error')}")
                return []

            # 转换结果格式
            search_results = result.get("search_results", [])
            formatted_results = []

            for item in search_results:
                formatted_results.append({
                    "type": "web_search",
                    "content": item.get("content", ""),
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "source": item.get("source", "web"),
                    "metadata": item
                })

            return formatted_results

        except Exception as e:
            logger.error(f"联网搜索失败: {e}")
            return []

    async def _generate_llm_response(
        self,
        message: str,
        history: List[Dict[str, Any]],
        search_results: List[Dict[str, Any]],
        mode: str = "normal"
    ) -> str:
        """
        生成LLM响应

        Args:
            message: 用户消息
            history: 对话历史
            search_results: 搜索结果（RAG或联网）
            mode: 对话模式

        Returns:
            LLM响应文本
        """
        try:
            from src.core.llms.router.smart_router import ModelRouter, LLMMessage
            from pathlib import Path

            # 初始化模型路由器
            model_router = ModelRouter.from_conf(Path("conf.yaml"))

            # 构建上下文
            context_parts = []

            if search_results:
                context_parts.append("以下是相关的参考信息：\n")
                for i, result in enumerate(search_results[:5], 1):
                    result_type = result.get("type", "unknown")
                    content = result.get("content", "")
                    source = result.get("source", "unknown")

                    if result_type == "rag":
                        context_parts.append(f"{i}. [知识库] {content[:200]}... (来源: {source})")
                    elif result_type == "web_search":
                        title = result.get("title", "")
                        url = result.get("url", "")
                        context_parts.append(f"{i}. [网络] {title}: {content[:200]}... (链接: {url})")

                context_parts.append("\n请基于以上信息回答用户问题。\n")

            # 构建消息列表
            messages = []

            # 添加系统提示
            system_prompt = "你是一个智能助手。"
            if mode == "rag_enhanced":
                system_prompt += "你可以利用知识库和网络搜索结果来提供更准确的回答。"

            if context_parts:
                system_prompt += "\n\n" + "".join(context_parts)

            messages.append(LLMMessage(role="system", content=system_prompt))

            # 添加历史消息（最近5轮）
            for msg in history[-10:]:
                messages.append(LLMMessage(
                    role=msg["role"],
                    content=msg["content"]
                ))

            # 添加当前消息
            messages.append(LLMMessage(role="user", content=message))

            # 调用LLM
            result = await model_router.chat(
                task="general",
                size="medium",
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )

            return result["content"]

        except Exception as e:
            logger.error(f"生成LLM响应失败: {e}", exc_info=True)
            return "抱歉，生成响应时出现了错误，请稍后重试。"

    async def _trigger_memory_summary(
        self,
        user_id: str,
        session_id: str,
        session_state: Dict[str, Any]
    ) -> None:
        """
        触发记忆摘要生成

        Args:
            user_id: 用户ID
            session_id: 会话ID
            session_state: 会话状态
        """
        if session_state.get("memory_summary_triggered"):
            return

        logger.info(f"触发会话 {session_id} 的记忆摘要生成")

        try:
            # 获取完整对话历史
            messages_result = await self.conversation_service.get_conversation_messages(
                user_id=user_id,
                session_id=session_id,
                limit=100
            )

            messages = messages_result.get("messages", [])

            if len(messages) < self.memory_threshold:
                return

            # 生成摘要（异步任务）
            asyncio.create_task(
                self._generate_memory_summary(user_id, session_id, messages)
            )

            session_state["memory_summary_triggered"] = True

        except Exception as e:
            logger.error(f"触发记忆摘要失败: {e}")

    async def _generate_memory_summary(
        self,
        user_id: str,
        session_id: str,
        messages: List[Dict[str, Any]]
    ) -> None:
        """
        生成记忆摘要（后台任务）

        Args:
            user_id: 用户ID
            session_id: 会话ID
            messages: 消息列表
        """
        try:
            logger.info(f"开始生成会话 {session_id} 的记忆摘要")

            # 构建摘要提示
            conversation_text = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in messages
            ])

            summary_prompt = f"""请为以下对话生成一个简洁的摘要，包括：
1. 主要讨论的话题
2. 用户的关键需求或问题
3. 重要的结论或建议

对话内容：
{conversation_text[:4000]}

请生成摘要："""

            from src.core.llms.router.smart_router import ModelRouter, LLMMessage
            from pathlib import Path

            model_router = ModelRouter.from_conf(Path("conf.yaml"))

            result = await model_router.chat(
                task="general",
                size="small",
                messages=[LLMMessage(role="user", content=summary_prompt)],
                temperature=0.3,
                max_tokens=500
            )

            summary = result["content"]

            # 保存摘要到数据库（这里需要扩展数据模型）
            logger.info(f"记忆摘要生成完成: {summary[:100]}...")

            # TODO: 保存到长期记忆表

        except Exception as e:
            logger.error(f"生成记忆摘要失败: {e}", exc_info=True)

    async def get_session_status(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        获取会话状态

        Args:
            user_id: 用户ID
            session_id: 会话ID

        Returns:
            会话状态信息
        """
        session_state = await self._get_session_state(user_id, session_id)

        return {
            "session_id": session_id,
            "message_count": session_state["message_count"],
            "current_mode": session_state["current_mode"],
            "mode_switched": session_state.get("mode_switched", False),
            "memory_summary_triggered": session_state.get("memory_summary_triggered", False),
            "last_message_time": session_state.get("last_message_time"),
            "thresholds": {
                "message_threshold": self.message_threshold,
                "memory_threshold": self.memory_threshold
            }
        }

    async def switch_mode(
        self,
        user_id: str,
        session_id: str,
        mode: ConversationMode
    ) -> Dict[str, Any]:
        """
        手动切换对话模式

        Args:
            user_id: 用户ID
            session_id: 会话ID
            mode: 目标模式

        Returns:
            切换结果
        """
        session_state = await self._get_session_state(user_id, session_id)

        old_mode = session_state["current_mode"]
        session_state["current_mode"] = mode.value
        session_state["mode_switched"] = True

        await self._save_session_state(session_id, session_state)

        logger.info(f"会话 {session_id} 模式切换: {old_mode} -> {mode.value}")

        return {
            "success": True,
            "old_mode": old_mode,
            "new_mode": mode.value,
            "message": f"对话模式已切换到 {mode.value}"
        }


# 全局实例缓存
_service_instances: Dict[str, SmartConversationService] = {}


def get_smart_conversation_service(db_session: AsyncSession) -> SmartConversationService:
    """获取智能对话服务实例"""
    # 注意：这里简化处理，实际应该基于session来管理实例
    session_id = id(db_session)
    if session_id not in _service_instances:
        _service_instances[session_id] = SmartConversationService(db_session)
    return _service_instances[session_id]
