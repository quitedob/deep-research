#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AgentScope研究服务
提供深度研究功能的主要服务接口
"""

import asyncio
import uuid
import json
import os
import logging
from collections import OrderedDict
from contextlib import suppress
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from backend.services.base_service import BaseService

# 导入自定义组件
from backend.core.agentscope.research_agent import DeepResearchAgent
from backend.core.agentscope.memory.research_memory import ResearchMemoryManager
from backend.repositories.research_dao import ResearchDAO

# 导入LLM抽象层
from backend.core.llm.factory import LLMFactory
from backend.core.llm.base_llm import BaseLLM, ConfigurationError
from backend.config.llm_config import get_config
from backend.services.evidence import citation_evidence

logger = logging.getLogger(__name__)


class AgentScopeResearchService(BaseService):
    """
    AgentScope研究服务
    管理深度研究的生命周期和协调各个组件
    """

    def __init__(self, llm_provider: str = "deepseek"):
        """
        初始化研究服务
        
        Args:
            llm_provider: LLM提供商名称 (默认: "deepseek")
        """
        super().__init__()
        self.research_dao = ResearchDAO()
        self.memory_manager = ResearchMemoryManager(self.research_dao)
        self.active_researchers: Dict[str, DeepResearchAgent] = {}
        self._lifecycle_lock = asyncio.Lock()
        self.max_active_sessions = int(os.getenv("RESEARCH_MAX_ACTIVE_SESSIONS", "16"))
        self.cache_limit = int(os.getenv("RESEARCH_CACHE_LIMIT", "128"))
        if self.max_active_sessions < 1 or self.cache_limit < self.max_active_sessions:
            raise ConfigurationError("RESEARCH_CACHE_LIMIT must cover RESEARCH_MAX_ACTIVE_SESSIONS, both positive")
        
        # ✅ 导入 ChatDAO 用于保存到聊天历史
        from backend.repositories.chat_dao import ChatDAO
        self.chat_dao = ChatDAO()
        
        # 内存中的会话信息（用于数据库未启用时）
        self.session_cache: Dict[str, Dict[str, Any]] = OrderedDict()
        
        # ✅ 报告缓存 - 研究完成后缓存完整报告，避免重复生成
        self.report_cache: Dict[str, Dict[str, Any]] = OrderedDict()
        
        # 设置默认LLM提供商
        self.llm_provider = llm_provider
        
        # 使用LLM工厂创建默认LLM实例
        try:
            self.default_llm = LLMFactory.create_llm(provider=llm_provider)
        except ConfigurationError as e:
            # 如果配置失败，记录错误但不阻止服务初始化
            logger.info(f"警告: 无法初始化默认LLM ({llm_provider}): {str(e)}")
            self.default_llm = None
        
        # 获取配置
        self.config = get_config()
        
        # The selected default model handles text and image input.
        self.default_multimodal_llm = self.default_llm

    def _cache(self, cache, session_id, value):
        cache.pop(session_id, None)
        cache[session_id] = value
        while len(cache) > self.cache_limit:
            removable = next((key for key in cache if key not in self.active_researchers), None)
            if removable is None:
                break
            cache.pop(removable, None)

    async def _set_status(self, session_id, status):
        await self.research_dao.update_session_status(session_id, status, datetime.utcnow())
        if session_id in self.session_cache:
            self.session_cache[session_id]["status"] = status
        if session_id in self.report_cache:
            self.report_cache[session_id]["session_info"]["status"] = status

    async def start_research(
        self, query: str, user_id: Optional[str] = None,
        research_type: str = "comprehensive", sources: Optional[List[str]] = None,
        include_images: bool = False, llm_provider: Optional[str] = None,
        multimodal_llm_instance: Optional[BaseLLM] = None,
        session_id: Optional[str] = None, _resume: bool = False,
    ) -> Dict[str, Any]:
        if not user_id:
            return {"success": False, "error": "Authentication required"}
        session_id = session_id or str(uuid.uuid4())
        async with self._lifecycle_lock:
            if session_id in self.active_researchers:
                return {"success": False, "error": "研究会话已在运行", "session_id": session_id}
            if len(self.active_researchers) >= self.max_active_sessions:
                return {"success": False, "error": "研究任务已满，请稍后重试", "session_id": session_id}
            existing = await self.research_dao.get_research_session(session_id)
            if existing and (not _resume or existing.get("user_id") != user_id):
                return {"success": False, "error": "研究会话已存在", "session_id": session_id}
            owned_llms = []
            researcher = None
            try:
                provider = llm_provider or self.llm_provider
                llm = self.default_llm if provider == self.llm_provider and self.default_llm else LLMFactory.create_llm(provider=provider)
                for instance in (llm, multimodal_llm_instance):
                    if instance is not None and instance is not self.default_llm and instance is not self.default_multimodal_llm:
                        if all(instance is not previous for previous in owned_llms):
                            owned_llms.append(instance)
                key = await self._get_web_search_api_key()
                if not key:
                    raise ConfigurationError("网络搜索API密钥未配置")
                researcher = DeepResearchAgent(
                    session_id=session_id, llm_instance=llm,
                    multimodal_llm_instance=multimodal_llm_instance or self.default_multimodal_llm,
                    web_search_api_key=key,
                )
                researcher._owned_llms = owned_llms
                if not existing:
                    await self.research_dao.create_research_session(
                        session_id=session_id, user_id=user_id, title=f"研究: {query[:50]}"
                    )
                await researcher.async_init()
                if _resume:
                    records = await self.research_dao.get_long_term_memory(session_id, 1000)
                    checkpoint = next((record for record in records if record["message_name"] == "research_checkpoint"), None)
                    if checkpoint and not await researcher.resume_research(json.loads(checkpoint["message_content"])):
                        raise RuntimeError("Research checkpoint could not be restored")
                request = {"query": query, "research_type": research_type, "sources": sources,
                           "include_images": include_images, "llm_provider": provider}
                await self.research_dao.save_message_to_long_term(
                    session_id, "system", "research_request", json.dumps(request, ensure_ascii=False), datetime.utcnow().isoformat()
                )
                await self.research_dao.update_session_status(session_id, "active")
                self.active_researchers[session_id] = researcher
                self._cache(self.session_cache, session_id, {
                    "id": session_id, "user_id": user_id, "title": f"研究: {query[:50]}",
                    "status": "active", "created_at": datetime.utcnow().isoformat(),
                    "llm_provider": provider, "model_name": llm.model,
                })
                researcher._research_task = asyncio.create_task(self._run_research(session_id, researcher, request))
                researcher._research_task.add_done_callback(lambda task: task.exception() if not task.cancelled() else None)
                return {"success": True, "session_id": session_id, "status": "started", "message": "研究已启动",
                        "started_at": datetime.utcnow().isoformat()}
            except Exception:
                logging.getLogger(__name__).exception("Research startup failed")
                if researcher is not None:
                    await self._close_research_resources(researcher)
                else:
                    await asyncio.gather(*(instance.close() for instance in owned_llms))
                self.active_researchers.pop(session_id, None)
                if await self.research_dao.get_research_session(session_id):
                    await self._set_status(session_id, "failed")
                return {"success": False, "error": "研究启动失败，请检查服务配置", "session_id": session_id}

    async def _run_research(self, session_id, researcher, request):
        try:
            result = await asyncio.wait_for(
                researcher.conduct_research(**{key: value for key, value in request.items() if key != "llm_provider"}),
                timeout=float(os.getenv("RESEARCH_TIMEOUT_SECONDS", "1800")),
            )
            if result.get("error"):
                raise RuntimeError("Research execution failed")
            report = await self._generate_final_report(session_id, researcher)
            if not report or not report.get("report"):
                raise RuntimeError("Research report was not generated")
            await self.research_dao.save_message_to_long_term(
                session_id, "assistant", "research_report", report["report"], datetime.utcnow().isoformat()
            )
            self._cache(self.report_cache, session_id, report)
            if not await self._save_research_to_chat_history(session_id, request["query"], result):
                raise RuntimeError("Research chat history was not saved")
            await self._set_status(session_id, "completed")
            return result
        except asyncio.CancelledError:
            await self._set_status(session_id, "interrupted")
            raise
        except Exception:
            await self._set_status(session_id, "failed")
            raise
        finally:
            # Task cleanup is independent of status polling, which may have many readers.
            self.active_researchers.pop(session_id, None)
            researcher.memory_manager.active_sessions.pop(session_id, None)
            await self._close_research_resources(researcher)

    async def _close_research_resources(self, researcher):
        if getattr(researcher, "_resources_closed", False):
            return
        researcher._resources_closed = True
        try:
            if hasattr(researcher, "close"):
                await researcher.close()
        finally:
            await asyncio.gather(*(instance.close() for instance in getattr(researcher, "_owned_llms", [])))

    async def get_research_status(self, session_id: str) -> Dict[str, Any]:
        async with self._lifecycle_lock:
            researcher = self.active_researchers.get(session_id)
            if researcher is not None:
                return {"session_id": session_id, "status": "in_progress",
                        "progress": await researcher.get_research_status()}
            session = await self.research_dao.get_research_session(session_id)
            if not session:
                return {"session_id": session_id, "status": "not_found"}
            status = session["status"]
            # The application holds a DB-backed single-worker lock. Without a live task,
            # an active persisted session belongs to an interrupted previous process.
            if status in ("active", "started", "in_progress"):
                await self._set_status(session_id, "interrupted")
                status = "interrupted"
            return {"session_id": session_id, "status": status, "session_info": session}

    async def interrupt_research(self, session_id: str) -> Dict[str, Any]:
        async with self._lifecycle_lock:
            researcher = self.active_researchers.get(session_id)
            if researcher is None:
                return {"success": False, "session_id": session_id, "error": "研究会话不存在或已结束"}
            task = researcher._research_task
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
            await self._close_research_resources(researcher)
            self.active_researchers.pop(session_id, None)
            # Persist the checkpoint after cancellation, when no tools can mutate it.
            checkpoint = await researcher.export_session_data()
            await self.research_dao.save_message_to_long_term(
                session_id, "system", "research_checkpoint",
                json.dumps(checkpoint, ensure_ascii=False, default=str), datetime.utcnow().isoformat()
            )
            await self._set_status(session_id, "interrupted")
            researcher.memory_manager.active_sessions.pop(session_id, None)
            if hasattr(researcher, "close"):
                await researcher.close()
            return {"success": True, "session_id": session_id, "message": "研究已中断"}

    async def resume_research(self, session_id: str, state_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        session = await self.research_dao.get_research_session(session_id)
        if not session:
            return {"success": False, "session_id": session_id, "error": "研究会话不存在"}
        if session["status"] not in ("interrupted", "failed"):
            return {"success": False, "session_id": session_id, "error": "仅能恢复已中断或失败的会话"}
        records = await self.research_dao.get_long_term_memory(session_id, 1000)
        request = next((json.loads(record["message_content"]) for record in records
                        if record["message_name"] == "research_request"), None)
        if not request:
            return {"success": False, "session_id": session_id, "error": "缺少原始研究请求，无法恢复"}
        return await self.start_research(**request, user_id=session["user_id"], session_id=session_id, _resume=True)

    async def close(self):
        for session_id in list(self.active_researchers):
            await self.interrupt_research(session_id)

    async def get_user_sessions(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取用户的研究会话列表

        Args:
            user_id: 用户ID
            status: 过滤状态
            limit: 结果数量限制

        Returns:
            会话列表
        """
        try:
            # 尝试从数据库获取
            db_sessions = await self.research_dao.get_user_research_sessions(
                user_id=user_id,
                status=status,
                limit=limit
            )
            
            if db_sessions:
                return db_sessions
            
            # 如果数据库未启用，从缓存获取
            cached_sessions = []
            for session_id, session_info in self.session_cache.items():
                if session_info.get("user_id") == user_id:
                    if status is None or session_info.get("status") == status:
                        cached_sessions.append({
                            "id": session_id,
                            "user_id": session_info.get("user_id"),
                            "title": session_info.get("title"),
                            "status": session_info.get("status"),
                            "created_at": session_info.get("created_at"),
                            "updated_at": session_info.get("created_at"),
                            "ended_at": None,
                            "findings_count": 0,
                            "citations_count": 0
                        })
            
            return cached_sessions[:limit]
            
        except Exception as e:
            logger.info(f"获取用户会话失败: {str(e)}")
            return []

    async def export_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        导出会话数据

        Args:
            session_id: 会话ID

        Returns:
            会话数据字典
        """
        try:
            # ✅ 优先从缓存获取完整报告（研究完成后）
            if session_id in self.report_cache:
                logger.info(f"从缓存返回报告 (会话: {session_id})")
                return self.report_cache[session_id]
            
            # 如果是活跃会话，从代理获取数据
            if session_id in self.active_researchers:
                researcher = self.active_researchers[session_id]
                agent_data = await researcher.export_session_data()
                
                # 转换格式以匹配 API 期望
                if agent_data:
                    # 获取缓存的会话信息
                    cached_session = self.session_cache.get(session_id, {})
                    
                    # 确保日期时间字段是字符串格式
                    created_at = agent_data.get("created_at")
                    if isinstance(created_at, datetime):
                        created_at = created_at.isoformat()
                    elif not created_at:
                        created_at = cached_session.get("created_at", datetime.utcnow().isoformat())
                    
                    updated_at = agent_data.get("last_updated")
                    if isinstance(updated_at, datetime):
                        updated_at = updated_at.isoformat()
                    elif not updated_at:
                        updated_at = datetime.utcnow().isoformat()
                    
                    # ✅ 使用 agent 生成的报告，如果没有则生成一个
                    report = agent_data.get("report")
                    if not report:
                        report = await self._generate_report_from_data(
                            agent_data.get("research_findings", []),
                            agent_data.get("citations", []),
                            cached_session.get("title", "研究会话")
                        )
                    
                    # 确定会话状态
                    status = "completed" if agent_data.get("research_phase") == "completed" else "active"
                    
                    # ✅ 序列化 findings 和 citations，确保所有字段都是可序列化的
                    findings = agent_data.get("research_findings", [])
                    serialized_findings = []
                    for finding in findings:
                        serialized_finding = dict(finding) if not isinstance(finding, dict) else finding.copy()
                        # 转换 id 为字符串
                        if 'id' in serialized_finding and not isinstance(serialized_finding['id'], str):
                            serialized_finding['id'] = str(serialized_finding['id'])
                        # 转换 created_at 为字符串
                        if 'created_at' in serialized_finding:
                            if isinstance(serialized_finding['created_at'], datetime):
                                serialized_finding['created_at'] = serialized_finding['created_at'].isoformat()
                            elif not isinstance(serialized_finding['created_at'], str):
                                serialized_finding['created_at'] = str(serialized_finding['created_at'])
                        serialized_findings.append(serialized_finding)
                    
                    citations = agent_data.get("citations", [])
                    serialized_citations = []
                    for citation in citations:
                        serialized_citation = dict(citation) if not isinstance(citation, dict) else citation.copy()
                        # 转换 id 为字符串
                        if 'id' in serialized_citation and not isinstance(serialized_citation['id'], str):
                            serialized_citation['id'] = str(serialized_citation['id'])
                        # 转换 created_at 为字符串
                        if 'created_at' in serialized_citation:
                            if isinstance(serialized_citation['created_at'], datetime):
                                serialized_citation['created_at'] = serialized_citation['created_at'].isoformat()
                            elif not isinstance(serialized_citation['created_at'], str):
                                serialized_citation['created_at'] = str(serialized_citation['created_at'])
                        serialized_citations.append(serialized_citation)
                    
                    return {
                        "session_info": {
                            "id": agent_data.get("session_id", session_id),
                            "user_id": cached_session.get("user_id"),
                            "title": cached_session.get("title", "研究会话"),
                            "status": status,
                            "created_at": created_at,
                            "updated_at": updated_at,
                            "ended_at": None,
                            "findings_count": len(serialized_findings),
                            "citations_count": len(serialized_citations)
                        },
                        "findings": serialized_findings,
                        "citations": serialized_citations,
                        "memory": agent_data.get("short_memory", []),
                        "report": report,  # ✅ 添加报告字段
                        "tools_used": agent_data.get("tools_used", []),
                        "exported_at": datetime.utcnow().isoformat()
                    }

            # 尝试从数据库获取
            db_data = await self.research_dao.export_session_data(session_id)
            if db_data:
                report_record = next((record for record in db_data.get("memory", []) if record.get("message_name") == "research_report"), None)
                if report_record:
                    db_data["report"] = report_record["message_content"]
                chat_link = next((record for record in db_data.get("memory", []) if record.get("message_name") == "research_chat_link"), None)
                if chat_link:
                    db_data["session_info"]["chat_session_id"] = chat_link["message_content"]
                return db_data
            
            # 如果数据库未启用，从缓存获取基本信息
            if session_id in self.session_cache:
                session_info = self.session_cache[session_id]
                return {
                    "session_info": session_info,
                    "findings": [],
                    "citations": [],
                    "memory": [],
                    "exported_at": datetime.utcnow().isoformat()
                }
            
            return None

        except Exception as e:
            logger.info(f"导出会话数据失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    async def _save_research_to_chat_history(self, session_id, query, result) -> bool:
        """Persist the report and its research linkage before announcing completion."""
        session_info = self.session_cache.get(session_id, {})
        if not session_info.get("user_id"):
            return False
        exported = await self.export_session_data(session_id) or {}
        report = exported.get("report") or result.get("report")
        if not report:
            return False
        chat_session_id = session_info.get("chat_session_id")
        if not chat_session_id:
            session = await self.chat_dao.create_session(
                user_id=session_info["user_id"], title=f"深度研究: {query[:30]}",
                llm_provider=session_info.get("llm_provider", self.llm_provider),
                model_name=session_info.get("model_name") or self.config.get_provider_config(self.llm_provider).default_model,
            )
            chat_session_id = session["id"]
        citations = exported.get("citations", [])
        await self.chat_dao.add_message(session_id=chat_session_id, role="user", content=query)
        await self.chat_dao.add_message(
            session_id=chat_session_id, role="assistant", content=report,
            metadata={"type": "research", "session_id": session_id,
                      "evidence": citation_evidence(citations), "citations": citations},
        )
        await self.research_dao.save_message_to_long_term(
            session_id, "system", "research_chat_link", chat_session_id, datetime.utcnow().isoformat(),
        )
        session_info["chat_session_id"] = chat_session_id
        if session_id in self.report_cache:
            self.report_cache[session_id]["session_info"]["chat_session_id"] = chat_session_id
        logger.info("Saved research report to chat history: %s", chat_session_id)
        return True

    async def delete_session(self, session_id: str) -> Dict[str, Any]:
        """
        删除研究会话

        Args:
            session_id: 会话ID

        Returns:
            删除结果
        """
        try:
            # 如果是活跃会话，先中断
            if session_id in self.active_researchers:
                await self.interrupt_research(session_id)

            # 从数据库删除
            await self.research_dao.delete_research_session(session_id)
            self.session_cache.pop(session_id, None)
            self.report_cache.pop(session_id, None)
            self.memory_manager.active_sessions.pop(session_id, None)

            return {
                "success": True,
                "session_id": session_id,
                "message": "研究会话已删除"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"删除会话失败: {str(e)}",
                "session_id": session_id
            }

    async def search_research_content(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        搜索研究内容

        Args:
            query: 搜索查询
            user_id: 用户ID，用于过滤
            limit: 结果数量限制

        Returns:
            搜索结果列表
        """
        if not user_id:
            return []
        return await self.research_dao.search_research_content(query=query, limit=limit, user_id=user_id)

    async def get_research_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取研究统计信息

        Args:
            user_id: 用户ID，如果为None则获取全局统计

        Returns:
            统计信息字典
        """
        try:
            return await self.research_dao.get_research_statistics(user_id=user_id)
        except Exception as e:
            logger.info(f"获取研究统计失败: {str(e)}")
            return {}

    async def cleanup_inactive_sessions(self, inactive_hours: int = 24) -> Dict[str, Any]:
        """
        清理非活跃会话

        Args:
            inactive_hours: 非活跃时间阈值（小时）

        Returns:
            清理结果
        """
        try:
            # 清理内存管理器中的非活跃会话
            await self.memory_manager.cleanup_inactive_sessions(inactive_hours)

            for cache in (self.session_cache, self.report_cache):
                for cached_id in list(cache):
                    if cached_id not in self.active_researchers:
                        cache.pop(cached_id, None)

            # 清理活跃研究者列表
            cleaned_sessions = []
            cutoff_time = datetime.utcnow() - timedelta(hours=inactive_hours)

            for session_id, researcher in list(self.active_researchers.items()):
                try:
                    session_info = await self.research_dao.get_research_session(session_id)
                    if session_info and session_info.get("updated_at"):
                        updated_at = session_info["updated_at"]
                        if isinstance(updated_at, str):
                            updated_at = datetime.fromisoformat(updated_at)
                        if updated_at < cutoff_time:
                            await self.interrupt_research(session_id)
                            cleaned_sessions.append(session_id)
                except Exception as e:
                    logger.info(f"清理会话 {session_id} 时出错: {str(e)}")

            return {
                "success": True,
                "cleaned_sessions": cleaned_sessions,
                "message": f"清理了 {len(cleaned_sessions)} 个非活跃会话"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"清理非活跃会话失败: {str(e)}"
            }

    async def _generate_final_report(
        self,
        session_id: str,
        researcher: DeepResearchAgent
    ) -> Dict[str, Any]:
        """
        生成最终的完整研究报告（只在研究完成时调用一次）
        
        Args:
            session_id: 会话ID
            researcher: 研究代理实例
            
        Returns:
            完整的报告数据字典
        """
        try:
            # 从代理获取数据
            agent_data = await researcher.export_session_data()
            
            # 获取缓存的会话信息
            cached_session = self.session_cache.get(session_id, {})
            
            # 确保日期时间字段是字符串格式
            created_at = agent_data.get("created_at")
            if isinstance(created_at, datetime):
                created_at = created_at.isoformat()
            elif not created_at:
                created_at = cached_session.get("created_at", datetime.utcnow().isoformat())
            
            updated_at = datetime.utcnow().isoformat()
            
            # 序列化 findings 和 citations
            findings = agent_data.get("research_findings", [])
            serialized_findings = []
            for finding in findings:
                serialized_finding = dict(finding) if not isinstance(finding, dict) else finding.copy()
                if 'id' in serialized_finding and not isinstance(serialized_finding['id'], str):
                    serialized_finding['id'] = str(serialized_finding['id'])
                if 'created_at' in serialized_finding:
                    if isinstance(serialized_finding['created_at'], datetime):
                        serialized_finding['created_at'] = serialized_finding['created_at'].isoformat()
                    elif not isinstance(serialized_finding['created_at'], str):
                        serialized_finding['created_at'] = str(serialized_finding['created_at'])
                serialized_findings.append(serialized_finding)
            
            citations = agent_data.get("citations", [])
            serialized_citations = []
            for citation in citations:
                serialized_citation = dict(citation) if not isinstance(citation, dict) else citation.copy()
                if 'id' in serialized_citation and not isinstance(serialized_citation['id'], str):
                    serialized_citation['id'] = str(serialized_citation['id'])
                if 'created_at' in serialized_citation:
                    if isinstance(serialized_citation['created_at'], datetime):
                        serialized_citation['created_at'] = serialized_citation['created_at'].isoformat()
                    elif not isinstance(serialized_citation['created_at'], str):
                        serialized_citation['created_at'] = str(serialized_citation['created_at'])
                serialized_citations.append(serialized_citation)
            
            # 生成报告文本
            report = agent_data.get("report")
            if not report:
                report = await self._generate_report_from_data(
                    serialized_findings,
                    serialized_citations,
                    cached_session.get("title", "研究会话")
                )
            
            # 构建完整报告
            final_report = {
                "session_info": {
                    "id": agent_data.get("session_id", session_id),
                    "user_id": cached_session.get("user_id"),
                    "title": cached_session.get("title", "研究会话"),
                    "status": "completed",
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "ended_at": updated_at,
                    "findings_count": len(serialized_findings),
                    "citations_count": len(serialized_citations)
                },
                "findings": serialized_findings,
                "citations": serialized_citations,
                "memory": agent_data.get("short_memory", []),
                "report": report,
                "tools_used": agent_data.get("tools_used", []),
                "exported_at": updated_at
            }
            
            return final_report
            
        except Exception as e:
            logger.info(f"生成最终报告失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    async def _generate_report_from_data(
        self,
        findings: List[Dict[str, Any]],
        citations: List[Dict[str, Any]],
        title: str
    ) -> str:
        """
        从研究数据生成报告
        
        Args:
            findings: 研究发现列表
            citations: 引用列表
            title: 研究标题
            
        Returns:
            格式化的研究报告
        """
        report = f"# 研究报告\n\n"
        report += f"## 研究主题\n{title}\n\n"
        report += f"## 研究时间\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        if findings:
            report += "## 主要发现\n\n"
            for i, finding in enumerate(findings, 1):
                source_type = finding.get("source_type", "未知")
                content = finding.get("content", "")
                relevance = (finding.get("relevance_score") or 0)

                report += f"### 发现 {i} [{source_type}来源]\n"
                report += f"{content}\n\n"
                if finding.get("relevance_score") is not None:
                    report += f"相关性评分: {relevance:.2f}\n\n"

        if citations:
            report += "## 参考文献\n\n"
            for i, citation in enumerate(citations, 1):
                title_text = citation.get("title", "无标题")
                authors = citation.get("authors", [])
                year = citation.get("publication_year", "未知")
                url = citation.get("source_url", "")

                report += f"{i}. {title_text}\n"
                if authors:
                    report += f"   作者: {', '.join(authors)}\n"
                if year != "未知":
                    report += f"   发表年份: {year}\n"
                if url:
                    report += f"   链接: {url}\n\n"

        report += f"\n## 统计信息\n\n"
        report += f"- 发现数量: {len(findings)}\n"
        report += f"- 引用数量: {len(citations)}\n"

        return report

    async def _get_web_search_api_key(self) -> Optional[str]:
        """
        获取网络搜索API密钥

        Returns:
            API密钥字符串
        """
        # 这里应该从环境变量或配置文件获取
        import os
        return os.getenv("WEB_SEARCH_API_KEY") or os.getenv("BIGMODEL_API_KEY") or os.getenv("ZHIPU_API_KEY")

    async def validate_session_access(self, session_id: str, user_id: str) -> bool:
        """
        验证用户对会话的访问权限

        Args:
            session_id: 会话ID
            user_id: 用户ID

        Returns:
            是否有访问权限
        """
        try:
            # 先尝试从数据库获取
            session_info = await self.research_dao.get_research_session(session_id)
            
            # 如果数据库未启用，从内存缓存获取
            if not session_info and session_id in self.session_cache:
                session_info = self.session_cache[session_id]
            
            if not session_info:
                return False

            if not user_id or not session_info.get("user_id"):
                return False

            # 检查用户ID匹配
            return session_info.get("user_id") == user_id

        except Exception as e:
            logger.info(f"验证会话访问权限失败: {str(e)}")
            return False

    async def format_final_report(
        self,
        session_id: str,
        export_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        将原始导出数据格式化为前端友好的最终报告（包含完整证据链）
        
        Args:
            session_id: 会话ID
            export_data: 从export_session_data获取的原始数据
            
        Returns:
            格式化后的报告字典
        """
        try:
            # ✅ 优先使用 Agent 生成的报告
            agent_report = export_data.get("report")
            if agent_report and isinstance(agent_report, str) and agent_report.strip():
                logger.info(f"使用 Agent 生成的报告，长度: {len(agent_report)} 字符")
                return {
                    "title": "深度研究报告",
                    "agent_report": agent_report,  # ✅ 保存完整的 Agent 报告
                    "metadata": {
                        "generated_at": datetime.utcnow().isoformat(),
                        "report_source": "agent",
                        "report_length": len(agent_report)
                    }
                }
            
            # 如果没有 Agent 报告，则从 findings 生成
            logger.info(f"未找到 Agent 报告，从 findings 生成")
            
            # 提取关键数据
            session_info = export_data.get("session_info", {})
            findings = export_data.get("findings", [])
            citations = export_data.get("citations", [])
            tools_used = export_data.get("tools_used", [])
            
            # 构建证据链
            evidence_chain = self._build_evidence_chain(findings, citations)
            
            # 提取关键发现
            key_findings = self._extract_key_findings(findings)
            
            # 构建报告
            formatted_report = {
                "title": session_info.get("title", "深度研究报告"),
                "summary": self._generate_executive_summary(findings),
                "sections": self._generate_report_sections(findings),
                "methodology": self._generate_methodology_section(tools_used),
                "conclusions": self._generate_conclusions(findings),
                "references": self._format_references(citations),
                "key_findings": key_findings,
                "evidence_chain": evidence_chain,
                "metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "total_findings": len(findings),
                    "total_citations": len(citations),
                    "quality_score": None,
                    "quality_level": "unassessed",
                    "tools_count": len(tools_used),
                    "evidence_strength": evidence_chain.get("overall_strength", "medium")
                }
            }
            
            return formatted_report
            
        except Exception as e:
            logger.info(f"格式化报告失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "title": "报告生成失败",
                "error": str(e),
                "summary": "",
                "sections": [],
                "methodology": "",
                "conclusions": "",
                "references": "",
                "key_findings": [],
                "evidence_chain": {},
                "metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "total_findings": 0,
                    "total_citations": 0,
                    "quality_score": None,
                    "quality_level": "low",
                    "tools_count": 0,
                    "evidence_strength": "weak"
                }
            }

    def _generate_executive_summary(self, findings: List[Dict]) -> str:
        """生成执行摘要"""
        if not findings:
            return "未找到相关发现。"
        
        # 选择相关性最高的前3个发现
        top_findings = sorted(
            findings,
            key=lambda x: (x.get("relevance_score") or 0),
            reverse=True
        )[:3]
        
        summary = "## 执行摘要\n\n"
        for i, finding in enumerate(top_findings, 1):
            content = finding.get("content", "")
            # 限制长度
            if len(content) > 300:
                content = content[:300] + "..."
            summary += f"- {content}\n\n"
        
        return summary

    def _generate_report_sections(self, findings: List[Dict]) -> List[Dict]:
        """按来源类型生成报告分段"""
        sections = []
        
        # 按来源分类
        findings_by_source = {}
        for finding in findings:
            source = finding.get("source_type", "其他")
            if source not in findings_by_source:
                findings_by_source[source] = []
            findings_by_source[source].append(finding)
        
        # 来源类型的显示名称
        source_names = {
            "web": "🌐 网络搜索发现",
            "wikipedia": "📚 维基百科知识库",
            "arxiv": "📖 学术论文见解",
            "image": "🖼️ 图像分析结果",
            "synthesis": "🔍 综合分析"
        }
        
        for source, source_findings in findings_by_source.items():
            # 取相关性最高的2个发现
            top_findings = sorted(
                source_findings,
                key=lambda x: (x.get("relevance_score") or 0),
                reverse=True
            )[:2]
            
            section = {
                "title": source_names.get(source, f"📌 {source}"),
                "content": "\n\n".join([
                    f.get("content", "")[:500] for f in top_findings
                ])
            }
            sections.append(section)
        
        return sections

    def _generate_methodology_section(self, tools_used: List[str]) -> str:
        """生成方法论部分"""
        methodology = "## 研究方法\n\n"
        methodology += "本研究采用了以下工具和方法进行多源信息收集和分析：\n\n"
        
        tool_descriptions = {
            "web_search": "🔍 互联网搜索 - 获取最新的网络信息和新闻",
            "search_wikipedia": "📚 维基百科查询 - 收集权威的背景知识",
            "search_arxiv_papers": "📖 学术论文检索 - 获取学术研究预印本",
            "analyze_image": "🖼️ 图像分析 - 处理和解释视觉内容",
            "synthesize_research_findings": "✨ 智能合成 - 整合多源信息形成结论"
        }
        
        if tools_used:
            for tool in tools_used:
                description = tool_descriptions.get(tool, f"🔧 {tool}")
                methodology += f"• {description}\n"
        else:
            methodology += "• 多源信息收集和分析\n"
        
        return methodology

    def _generate_conclusions(self, findings: List[Dict]) -> str:
        """生成结论部分"""
        conclusions = "## 主要结论\n\n"
        
        if not findings:
            return conclusions + "基于现有数据无法得出确定的结论。"
        
        # 按相关性排序，取前5个
        sorted_findings = sorted(
            findings,
            key=lambda x: (x.get("relevance_score") or 0),
            reverse=True
        )[:5]
        
        for i, finding in enumerate(sorted_findings, 1):
            content = finding.get("content", "")
            # 提取前2句作为结论
            sentences = content.split("。")[:2]
            conclusion = "。".join(sentences)
            if not conclusion.endswith("。"):
                conclusion += "。"
            conclusions += f"{i}. {conclusion}\n\n"
        
        return conclusions

    def _format_references(self, citations: List[Dict]) -> str:
        """格式化参考文献"""
        if not citations:
            return "## 参考文献\n\n未找到相关引用。"
        
        references = "## 参考文献\n\n"
        for i, citation in enumerate(citations, 1):
            title = citation.get("title", "Unknown")
            authors = citation.get("authors", [])
            year = citation.get("publication_year", "")
            url = citation.get("source_url", "")
            
            authors_str = ", ".join(authors[:3]) if authors else "Unknown"  # 最多显示3个作者
            
            ref_text = f"{i}. {title}"
            if authors_str:
                ref_text += f" - {authors_str}"
            if authors and len(authors) > 3:
                ref_text += f" 等"
            if year:
                ref_text += f" ({year})"
            if url:
                ref_text += f"\n   [链接]({url})"
            
            references += ref_text + "\n\n"
        
        return references

    def _build_evidence_chain(self, findings: List[Dict], citations: List[Dict]) -> Dict[str, Any]:
        """构建证据链数据结构"""
        try:
            # 按来源类型分组
            findings_by_source = {}
            for finding in findings:
                source = finding.get("source_type", "other")
                if source not in findings_by_source:
                    findings_by_source[source] = []
                findings_by_source[source].append(finding)
            
            # 计算每个来源的平均相关性
            source_strengths = {}
            for source, source_findings in findings_by_source.items():
                scores = [f["relevance_score"] for f in source_findings if isinstance(f.get("relevance_score"), (int, float))]
                avg_relevance = sum(scores) / len(scores) if scores else None
                source_strengths[source] = {
                    "count": len(source_findings),
                    "avg_relevance": avg_relevance,
                    "strength": "unassessed"
                }
            
            # 提取证据关系
            relationships = self._extract_evidence_relationships(findings)
            
            # 计算整体证据强度
            overall_avg = sum((f.get("relevance_score") or 0) for f in findings) / len(findings) if findings else 0
            overall_strength = "strong" if overall_avg >= 0.7 else "medium" if overall_avg >= 0.4 else "weak"
            
            return {
                "sources": findings_by_source,
                "source_strengths": source_strengths,
                "relationships": relationships,
                "overall_strength": "unassessed",
                "total_evidence_points": len(findings),
                "citation_support": len(citations)
            }
            
        except Exception as e:
            logger.info(f"构建证据链失败: {str(e)}")
            return {
                "sources": {},
                "source_strengths": {},
                "relationships": [],
                "overall_strength": "weak",
                "total_evidence_points": 0,
                "citation_support": 0
            }

    def _extract_evidence_relationships(self, findings: List[Dict]) -> List[Dict]:
        # Similar relevance does not establish that two sources support each other.
        return []

    def _extract_key_findings(self, findings: List[Dict]) -> List[Dict]:
        """提取关键发现（最重要的5-10个）"""
        try:
            # 按相关性排序
            sorted_findings = sorted(
                findings,
                key=lambda x: (x.get("relevance_score") or 0),
                reverse=True
            )
            
            # 提取前8个最相关的发现
            key_findings = []
            for finding in sorted_findings[:8]:
                key_findings.append({
                    "content": finding.get("content", "")[:300],  # 限制长度
                    "source_type": finding.get("source_type", "unknown"),
                    "relevance_score": finding.get("relevance_score"),
                    "quality": "unassessed"
                })
            
            return key_findings
            
        except Exception as e:
            logger.info(f"提取关键发现失败: {str(e)}")
            return []

    def generate_full_report_text(self, formatted_report: Dict[str, Any]) -> str:
        """
        将格式化的报告转换为完整的 Markdown 文本
        
        Args:
            formatted_report: 格式化后的报告字典
            
        Returns:
            完整的报告文本（Markdown 格式）
        """
        try:
            # ✅ 优先返回 Agent 生成的完整报告
            agent_report = formatted_report.get("agent_report")
            if agent_report:
                logger.info(f"返回 Agent 完整报告，长度: {len(agent_report)} 字符")
                return agent_report
            
            # 如果没有 Agent 报告，则从结构化数据生成
            logger.info(f"从结构化数据生成报告")
            
            report_text = ""
            
            # 标题
            title = formatted_report.get("title", "深度研究报告")
            report_text += f"# {title}\n\n"
            
            # 元数据
            metadata = formatted_report.get("metadata", {})
            if metadata:
                report_text += "---\n\n"
                report_text += f"**生成时间**: {metadata.get('generated_at', '')}\n\n"
                
                # 只在有质量评分时显示
                if metadata.get('quality_score'):
                    report_text += f"**质量评分**: {int(metadata.get('quality_score', 0) * 100)}% ({metadata.get('quality_level', 'unknown')})\n\n"
                
                report_text += f"**发现数量**: {metadata.get('total_findings', 0)} | "
                report_text += f"**引用数量**: {metadata.get('total_citations', 0)} | "
                report_text += f"**工具使用**: {metadata.get('tools_count', 0)}\n\n"
                report_text += "---\n\n"
            
            # 执行摘要
            summary = formatted_report.get("summary", "")
            if summary:
                report_text += summary + "\n\n"
            
            # 报告章节
            sections = formatted_report.get("sections", [])
            if sections:
                for section in sections:
                    report_text += f"## {section.get('title', '章节')}\n\n"
                    report_text += f"{section.get('content', '')}\n\n"
            
            # 研究方法
            methodology = formatted_report.get("methodology", "")
            if methodology:
                report_text += methodology + "\n\n"
            
            # 主要结论
            conclusions = formatted_report.get("conclusions", "")
            if conclusions:
                report_text += conclusions + "\n\n"
            
            # 参考文献
            references = formatted_report.get("references", "")
            if references:
                report_text += references + "\n\n"
            
            return report_text
            
        except Exception as e:
            logger.info(f"生成完整报告文本失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"# 报告生成失败\n\n错误: {str(e)}"
