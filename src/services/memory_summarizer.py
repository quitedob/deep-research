# -*- coding: utf-8 -*-
"""
记忆摘要生成器
生成对话摘要并存储到长期记忆
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


class MemorySummarizer:
    """记忆摘要生成器"""

    def __init__(self):
        # 摘要缓存
        self._summaries: Dict[str, Dict[str, Any]] = {}

    async def generate_summary(
        self,
        session_id: str,
        messages: List[Dict[str, Any]],
        user_id: str
    ) -> Dict[str, Any]:
        """
        生成对话摘要

        Args:
            session_id: 会话ID
            messages: 消息列表
            user_id: 用户ID

        Returns:
            摘要结果
        """
        try:
            logger.info(f"开始生成会话 {session_id} 的摘要，消息数: {len(messages)}")

            # 1. 提取关键信息
            topics = await self._extract_topics(messages)
            key_points = await self._extract_key_points(messages)
            user_preferences = await self._extract_user_preferences(messages)

            # 2. 生成摘要文本
            summary_text = await self._generate_summary_text(
                messages=messages,
                topics=topics,
                key_points=key_points
            )

            # 3. 构建摘要对象
            summary = {
                "session_id": session_id,
                "user_id": user_id,
                "summary_text": summary_text,
                "topics": topics,
                "key_points": key_points,
                "user_preferences": user_preferences,
                "message_count": len(messages),
                "created_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "first_message_time": messages[0]["created_at"] if messages else None,
                    "last_message_time": messages[-1]["created_at"] if messages else None
                }
            }

            # 4. 缓存摘要
            self._summaries[session_id] = summary

            logger.info(f"会话 {session_id} 摘要生成完成")

            return {
                "success": True,
                "summary": summary
            }

        except Exception as e:
            logger.error(f"生成摘要失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def _extract_topics(self, messages: List[Dict[str, Any]]) -> List[str]:
        """
        提取对话主题

        Args:
            messages: 消息列表

        Returns:
            主题列表
        """
        try:
            # 简单实现：基于关键词提取
            # 实际应该使用NLP模型进行主题建模

            # 收集所有用户消息
            user_messages = [
                msg["content"]
                for msg in messages
                if msg.get("role") == "user"
            ]

            if not user_messages:
                return []

            # 使用LLM提取主题
            from src.core.llms.router.smart_router import ModelRouter, LLMMessage
            from pathlib import Path

            model_router = ModelRouter.from_conf(Path("conf.yaml"))

            conversation_text = "\n".join(user_messages[:10])  # 限制长度

            prompt = f"""请分析以下对话内容，提取3-5个主要讨论的话题关键词。
只返回关键词列表，用逗号分隔，不要其他解释。

对话内容：
{conversation_text}

话题关键词："""

            result = await model_router.chat(
                task="general",
                size="small",
                messages=[LLMMessage(role="user", content=prompt)],
                temperature=0.3,
                max_tokens=100
            )

            # 解析主题
            topics_text = result["content"].strip()
            topics = [t.strip() for t in topics_text.split(",") if t.strip()]

            return topics[:5]  # 最多5个主题

        except Exception as e:
            logger.error(f"提取主题失败: {e}")
            return []

    async def _extract_key_points(self, messages: List[Dict[str, Any]]) -> List[str]:
        """
        提取关键要点

        Args:
            messages: 消息列表

        Returns:
            关键要点列表
        """
        try:
            # 收集助手的重要回复
            assistant_messages = [
                msg["content"]
                for msg in messages
                if msg.get("role") == "assistant"
            ]

            if not assistant_messages:
                return []

            # 使用LLM提取关键要点
            from src.core.llms.router.smart_router import ModelRouter, LLMMessage
            from pathlib import Path

            model_router = ModelRouter.from_conf(Path("conf.yaml"))

            conversation_text = "\n".join(assistant_messages[:10])

            prompt = f"""请从以下助手回复中提取3-5个关键要点或结论。
每个要点用一句话概括，用换行符分隔。

助手回复：
{conversation_text[:2000]}

关键要点："""

            result = await model_router.chat(
                task="general",
                size="small",
                messages=[LLMMessage(role="user", content=prompt)],
                temperature=0.3,
                max_tokens=200
            )

            # 解析要点
            key_points = [
                point.strip()
                for point in result["content"].strip().split("\n")
                if point.strip() and not point.strip().startswith("#")
            ]

            return key_points[:5]

        except Exception as e:
            logger.error(f"提取关键要点失败: {e}")
            return []

    async def _extract_user_preferences(
        self,
        messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        提取用户偏好

        Args:
            messages: 消息列表

        Returns:
            用户偏好字典
        """
        try:
            # 简单实现：分析用户消息的特征
            user_messages = [
                msg["content"]
                for msg in messages
                if msg.get("role") == "user"
            ]

            if not user_messages:
                return {}

            # 统计特征
            avg_length = sum(len(msg) for msg in user_messages) / len(user_messages)

            # 检测偏好
            preferences = {
                "message_style": "详细" if avg_length > 100 else "简洁",
                "avg_message_length": int(avg_length),
                "total_messages": len(user_messages)
            }

            return preferences

        except Exception as e:
            logger.error(f"提取用户偏好失败: {e}")
            return {}

    async def _generate_summary_text(
        self,
        messages: List[Dict[str, Any]],
        topics: List[str],
        key_points: List[str]
    ) -> str:
        """
        生成摘要文本

        Args:
            messages: 消息列表
            topics: 主题列表
            key_points: 关键要点列表

        Returns:
            摘要文本
        """
        try:
            # 构建对话文本
            conversation_text = "\n".join([
                f"{msg['role']}: {msg['content'][:200]}"
                for msg in messages[:20]  # 限制消息数量
            ])

            # 使用LLM生成摘要
            from src.core.llms.router.smart_router import ModelRouter, LLMMessage
            from pathlib import Path

            model_router = ModelRouter.from_conf(Path("conf.yaml"))

            prompt = f"""请为以下对话生成一个简洁的摘要（100-200字）。

主要话题：{', '.join(topics)}
关键要点：
{chr(10).join(f'- {point}' for point in key_points)}

对话内容：
{conversation_text}

摘要："""

            result = await model_router.chat(
                task="general",
                size="small",
                messages=[LLMMessage(role="user", content=prompt)],
                temperature=0.3,
                max_tokens=300
            )

            return result["content"].strip()

        except Exception as e:
            logger.error(f"生成摘要文本失败: {e}")
            return "摘要生成失败"

    async def get_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话摘要

        Args:
            session_id: 会话ID

        Returns:
            摘要数据
        """
        return self._summaries.get(session_id)

    async def get_all_summaries(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取用户的所有摘要

        Args:
            user_id: 用户ID

        Returns:
            摘要列表
        """
        return [
            summary
            for summary in self._summaries.values()
            if summary.get("user_id") == user_id
        ]

    async def delete_summary(self, session_id: str) -> bool:
        """
        删除摘要

        Args:
            session_id: 会话ID

        Returns:
            是否成功
        """
        if session_id in self._summaries:
            del self._summaries[session_id]
            return True
        return False


# 全局实例
_summarizer = None


def get_memory_summarizer() -> MemorySummarizer:
    """获取全局记忆摘要生成器实例"""
    global _summarizer
    if _summarizer is None:
        _summarizer = MemorySummarizer()
    return _summarizer
