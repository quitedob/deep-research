#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AgentScope研究服务
提供深度研究功能的主要服务接口
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from src.services.base_service import BaseService

# 导入自定义组件
from src.core.agentscope.research_agent import DeepResearchAgent
from src.core.agentscope.memory.research_memory import ResearchMemoryManager
from src.dao.research_dao import ResearchDAO

# 导入LLM抽象层
from src.core.llm.factory import LLMFactory
from src.core.llm.base_llm import BaseLLM, ConfigurationError
from src.config.llm_config import get_config


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
        
        # ✅ 导入 ChatDAO 用于保存到聊天历史
        from src.dao.chat_dao import ChatDAO
        self.chat_dao = ChatDAO()
        
        # 内存中的会话信息（用于数据库未启用时）
        self.session_cache: Dict[str, Dict[str, Any]] = {}
        
        # ✅ 报告缓存 - 研究完成后缓存完整报告，避免重复生成
        self.report_cache: Dict[str, Dict[str, Any]] = {}
        
        # 设置默认LLM提供商
        self.llm_provider = llm_provider
        
        # 使用LLM工厂创建默认LLM实例
        try:
            self.default_llm = LLMFactory.create_llm(provider=llm_provider)
        except ConfigurationError as e:
            # 如果配置失败，记录错误但不阻止服务初始化
            print(f"警告: 无法初始化默认LLM ({llm_provider}): {str(e)}")
            self.default_llm = None
        
        # 获取配置
        self.config = get_config()
        
        # 创建默认多模态LLM实例（用于Ollama图像分析）
        try:
            self.default_multimodal_llm = LLMFactory.create_llm(
                provider="ollama",
                base_url="http://localhost:11434",
                model="gemma3:4b"
            )
        except ConfigurationError as e:
            print(f"警告: 无法初始化多模态LLM (Ollama): {str(e)}")
            self.default_multimodal_llm = None

    async def start_research(
        self,
        query: str,
        user_id: Optional[str] = None,
        research_type: str = "comprehensive",
        sources: Optional[List[str]] = None,
        include_images: bool = False,
        llm_provider: Optional[str] = None,
        multimodal_llm_instance: Optional[BaseLLM] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        启动深度研究

        Args:
            query: 研究查询
            user_id: 用户ID
            research_type: 研究类型
            sources: 指定的信息源类型
            include_images: 是否包含图像分析
            llm_provider: LLM提供商名称（可选，默认使用服务的默认提供商）
            multimodal_llm_instance: 自定义多模态LLM实例（可选）
            session_id: 指定会话ID，如果为None则自动生成

        Returns:
            研究启动结果
        """
        try:
            # 生成或验证会话ID
            if not session_id:
                session_id = str(uuid.uuid4())
            elif session_id in self.active_researchers:
                return {
                    "success": False,
                    "error": "研究会话已存在",
                    "session_id": session_id
                }

            # 确定使用的LLM提供商
            provider = llm_provider or self.llm_provider
            
            # 创建或获取LLM实例
            try:
                if provider == self.llm_provider and self.default_llm:
                    llm_instance = self.default_llm
                else:
                    llm_instance = LLMFactory.create_llm(provider=provider)
            except ConfigurationError as e:
                return {
                    "success": False,
                    "error": f"LLM配置错误: {str(e)}",
                    "session_id": session_id
                }
            
            # 验证DeepSeek API密钥（如果使用DeepSeek）
            if provider == "deepseek":
                provider_config = self.config.get_provider_config("deepseek")
                if not provider_config.api_key:
                    return {
                        "success": False,
                        "error": "DeepSeek API密钥未配置。请设置DEEPSEEK_API_KEY环境变量。",
                        "session_id": session_id
                    }

            # 确定使用的多模态LLM实例
            final_multimodal_llm = multimodal_llm_instance or self.default_multimodal_llm

            # 获取API密钥
            web_search_api_key = await self._get_web_search_api_key()
            if not web_search_api_key:
                return {
                    "success": False,
                    "error": "网络搜索API密钥未配置"
                }

            # 创建研究代理，传入LLM实例
            researcher = DeepResearchAgent(
                session_id=session_id,
                llm_instance=llm_instance,
                multimodal_llm_instance=final_multimodal_llm,
                web_search_api_key=web_search_api_key
            )

            # 异步初始化研究代理
            await researcher.async_init()

            # 存储活跃研究者
            self.active_researchers[session_id] = researcher

            # 在数据库中创建会话记录
            await self.research_dao.create_research_session(
                session_id=session_id,
                user_id=user_id,
                title=f"研究: {query[:50]}..."
            )
            
            # 同时在内存中缓存会话信息（用于数据库未启用时）
            self.session_cache[session_id] = {
                "id": session_id,
                "user_id": user_id,
                "title": f"研究: {query[:50]}...",
                "status": "active",
                "created_at": datetime.now().isoformat()
            }

            # 启动异步研究，并在完成后自动生成报告
            async def research_with_completion():
                """研究完成后自动生成并缓存报告"""
                try:
                    result = await researcher.conduct_research(
                        query=query,
                        research_type=research_type,
                        sources=sources,
                        include_images=include_images
                    )
                    
                    # ✅ 研究完成后，立即生成完整报告并缓存
                    print(f"✓ 研究完成，开始生成最终报告...")
                    
                    try:
                        final_report = await self._generate_final_report(session_id, researcher)
                        
                        # 缓存完整报告
                        if final_report:
                            self.report_cache[session_id] = final_report
                            print(f"✓ 报告已生成并缓存")
                        else:
                            print(f"⚠️ 报告生成返回空值")
                    except Exception as report_error:
                        print(f"⚠️ 生成报告时出错: {str(report_error)}")
                        import traceback
                        traceback.print_exc()
                        # 即使报告生成失败，也继续更新状态
                    
                    # 更新会话状态为已完成（即使报告生成失败）
                    try:
                        await self.research_dao.update_session_status(
                            session_id,
                            "completed",
                            datetime.now()
                        )
                        print(f"✓ 会话状态已更新为 completed")
                    except Exception as db_error:
                        print(f"⚠️ 更新数据库状态失败: {str(db_error)}")
                        # 数据库更新失败不影响研究结果
                    
                    # ✅ 保存研究结果到聊天历史记录
                    try:
                        await self._save_research_to_chat_history(session_id, query, result)
                    except Exception as save_error:
                        print(f"⚠️ 保存到聊天历史失败: {str(save_error)}")
                        # 保存失败不影响研究结果
                    
                    print(f"✓ 会话 {session_id} 完成")
                    return result
                    
                except Exception as e:
                    print(f"✗ 研究失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    
                    # 更新会话状态为失败
                    try:
                        await self.research_dao.update_session_status(
                            session_id,
                            "failed",
                            datetime.now()
                        )
                    except Exception as db_error:
                        print(f"⚠️ 更新失败状态时出错: {str(db_error)}")
                    
                    raise
            
            research_task = asyncio.create_task(research_with_completion())

            # 存储任务引用
            self.active_researchers[session_id]._research_task = research_task

            return {
                "success": True,
                "session_id": session_id,
                "status": "started",
                "message": "研究已启动",
                "started_at": datetime.now().isoformat()
            }

        except Exception as e:
            # 打印详细的错误信息
            import traceback
            print(f"启动研究时出错: {e}")
            print(f"错误类型: {type(e).__name__}")
            print("完整堆栈:")
            traceback.print_exc()
            
            # 清理失败的会话
            if session_id and session_id in self.active_researchers:
                del self.active_researchers[session_id]

            return {
                "success": False,
                "error": f"启动研究失败: {str(e)}",
                "session_id": session_id
            }

    async def get_research_status(self, session_id: str) -> Dict[str, Any]:
        """
        获取研究状态

        Args:
            session_id: 会话ID

        Returns:
            研究状态信息
        """
        try:
            # 检查是否为活跃会话
            if session_id in self.active_researchers:
                researcher = self.active_researchers[session_id]

                # 检查任务状态
                if hasattr(researcher, '_research_task'):
                    task = researcher._research_task
                    if task.done():
                        # ✅ 任务完成，从活跃列表中移除
                        del self.active_researchers[session_id]
                        
                        try:
                            result = task.result()
                            return {
                                "session_id": session_id,
                                "status": "completed",
                                "result": result,
                                "completed_at": datetime.now().isoformat()
                            }
                        except Exception as e:
                            return {
                                "session_id": session_id,
                                "status": "failed",
                                "error": str(e),
                                "failed_at": datetime.now().isoformat()
                            }

                # 获取当前状态
                status = await researcher.get_research_status()
                return {
                    "session_id": session_id,
                    "status": "in_progress",
                    "progress": status,
                    "updated_at": datetime.now().isoformat()
                }

            # ✅ 检查是否有缓存的报告（已完成的会话）
            if session_id in self.report_cache:
                return {
                    "session_id": session_id,
                    "status": "completed",
                    "note": "研究已完成，报告已缓存",
                    "completed_at": datetime.now().isoformat()
                }

            # 检查数据库中的会话
            session_info = await self.research_dao.get_research_session(session_id)
            if session_info:
                return {
                    "session_id": session_id,
                    "status": session_info["status"],
                    "session_info": session_info,
                    "note": "会话已完成或已中断"
                }

            return {
                "session_id": session_id,
                "status": "not_found",
                "error": "研究会话不存在"
            }

        except Exception as e:
            return {
                "session_id": session_id,
                "status": "error",
                "error": f"获取状态失败: {str(e)}"
            }

    async def interrupt_research(self, session_id: str) -> Dict[str, Any]:
        """
        中断研究会话

        Args:
            session_id: 会话ID

        Returns:
            中断结果
        """
        try:
            if session_id not in self.active_researchers:
                return {
                    "success": False,
                    "error": "研究会话不存在或已结束",
                    "session_id": session_id
                }

            researcher = self.active_researchers[session_id]

            # 中断研究
            interrupt_result = await researcher.interrupt_research()

            # 从活跃列表中移除
            del self.active_researchers[session_id]

            # 更新数据库状态
            await self.research_dao.update_session_status(
                session_id,
                "interrupted",
                datetime.now()
            )

            return {
                "success": True,
                "session_id": session_id,
                "interrupt_result": interrupt_result,
                "message": "研究已中断"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"中断研究失败: {str(e)}",
                "session_id": session_id
            }

    async def resume_research(
        self,
        session_id: str,
        state_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        恢复被中断的研究

        Args:
            session_id: 会话ID
            state_data: 保存的状态数据

        Returns:
            恢复结果
        """
        try:
            if session_id in self.active_researchers:
                return {
                    "success": False,
                    "error": "研究会话已存在",
                    "session_id": session_id
                }

            # 获取保存的状态数据
            if not state_data:
                session_data = await self.research_dao.export_session_data(session_id)
                if not session_data:
                    return {
                        "success": False,
                        "error": "无法获取会话状态数据",
                        "session_id": session_id
                    }
                state_data = session_data

            # 重建研究代理
            web_search_api_key = await self._get_web_search_api_key()
            
            # 创建LLM实例
            try:
                llm_instance = self.default_llm or LLMFactory.create_llm(provider=self.llm_provider)
            except ConfigurationError as e:
                return {
                    "success": False,
                    "error": f"LLM配置错误: {str(e)}",
                    "session_id": session_id
                }
            
            researcher = DeepResearchAgent(
                session_id=session_id,
                llm_instance=llm_instance,
                multimodal_llm_instance=self.default_multimodal_llm,
                web_search_api_key=web_search_api_key
            )

            # 恢复状态
            recovery_success = await researcher.resume_research(state_data)
            if not recovery_success:
                return {
                    "success": False,
                    "error": "恢复会话状态失败",
                    "session_id": session_id
                }

            # 重新激活会话
            self.active_researchers[session_id] = researcher
            await self.research_dao.update_session_status(session_id, "active")

            return {
                "success": True,
                "session_id": session_id,
                "message": "研究会话已恢复"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"恢复研究失败: {str(e)}",
                "session_id": session_id
            }

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
            print(f"获取用户会话失败: {str(e)}")
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
                print(f"✓ 从缓存返回报告 (会话: {session_id})")
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
                        created_at = cached_session.get("created_at", datetime.now().isoformat())
                    
                    updated_at = agent_data.get("last_updated")
                    if isinstance(updated_at, datetime):
                        updated_at = updated_at.isoformat()
                    elif not updated_at:
                        updated_at = datetime.now().isoformat()
                    
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
                        "exported_at": datetime.now().isoformat()
                    }

            # 尝试从数据库获取
            db_data = await self.research_dao.export_session_data(session_id)
            if db_data:
                return db_data
            
            # 如果数据库未启用，从缓存获取基本信息
            if session_id in self.session_cache:
                session_info = self.session_cache[session_id]
                return {
                    "session_info": session_info,
                    "findings": [],
                    "citations": [],
                    "memory": [],
                    "exported_at": datetime.now().isoformat()
                }
            
            return None

        except Exception as e:
            print(f"导出会话数据失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    async def _save_research_to_chat_history(
        self,
        session_id: str,
        query: str,
        result: Dict[str, Any]
    ) -> bool:
        """
        将研究结果保存到聊天历史记录
        
        Args:
            session_id: 研究会话ID
            query: 用户查询
            result: 研究结果
            
        Returns:
            是否保存成功
        """
        try:
            # 获取会话信息
            session_info = self.session_cache.get(session_id, {})
            user_id = session_info.get("user_id")
            
            if not user_id:
                print(f"⚠️ 无法保存到聊天历史：未找到 user_id")
                return False
            
            # 创建或获取聊天会话
            chat_session_id = session_info.get("chat_session_id")
            
            if not chat_session_id:
                # 创建新的聊天会话
                chat_session = await self.chat_dao.create_session(
                    user_id=user_id,
                    title=f"深度研究: {query[:30]}...",
                    llm_provider="agentscope",
                    model_name="deep-research"  # ✅ 添加 model_name 参数
                )
                chat_session_id = chat_session.get("id")
                print(f"✓ 创建聊天会话: {chat_session_id}")
            
            # 保存用户消息
            await self.chat_dao.add_message(
                session_id=chat_session_id,
                role="user",
                content=query
            )
            print(f"✓ 保存用户消息")
            
            # 获取报告内容
            report = result.get("report", "")
            if not report:
                # 尝试从缓存获取
                export_data = await self.export_session_data(session_id)
                if export_data:
                    report = export_data.get("report", "")
            
            if not report:
                print(f"⚠️ 未找到报告内容")
                return False
            
            # 保存助手回复（研究报告）
            await self.chat_dao.add_message(
                session_id=chat_session_id,
                role="assistant",
                content=report
            )
            print(f"✓ 保存研究报告到聊天历史")
            
            return True
            
        except Exception as e:
            print(f"✗ 保存到聊天历史失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

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
        try:
            # 如果指定了用户ID，需要先获取用户的会话ID
            session_ids = None
            if user_id:
                user_sessions = await self.get_user_sessions(user_id)
                session_ids = [session["id"] for session in user_sessions]

            # 执行搜索
            results = []
            if session_ids:
                for session_id in session_ids:
                    session_results = await self.research_dao.search_research_content(
                        query=query,
                        limit=limit // len(session_ids) + 1,
                        session_id=session_id
                    )
                    results.extend(session_results)
            else:
                results = await self.research_dao.search_research_content(
                    query=query,
                    limit=limit
                )

            return results[:limit]

        except Exception as e:
            print(f"搜索研究内容失败: {str(e)}")
            return []

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
            print(f"获取研究统计失败: {str(e)}")
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

            # 清理活跃研究者列表
            cleaned_sessions = []
            cutoff_time = datetime.now() - timedelta(hours=inactive_hours)

            for session_id, researcher in list(self.active_researchers.items()):
                try:
                    session_info = await self.research_dao.get_research_session(session_id)
                    if session_info and session_info.get("updated_at"):
                        updated_at = datetime.fromisoformat(session_info["updated_at"])
                        if updated_at < cutoff_time:
                            await self.interrupt_research(session_id)
                            cleaned_sessions.append(session_id)
                except Exception as e:
                    print(f"清理会话 {session_id} 时出错: {str(e)}")

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
                created_at = cached_session.get("created_at", datetime.now().isoformat())
            
            updated_at = datetime.now().isoformat()
            
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
            print(f"✗ 生成最终报告失败: {str(e)}")
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
        report += f"## 研究时间\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        if findings:
            report += "## 主要发现\n\n"
            for i, finding in enumerate(findings, 1):
                source_type = finding.get("source_type", "未知")
                content = finding.get("content", "")
                relevance = finding.get("relevance_score", 0)

                report += f"### 发现 {i} [{source_type}来源]\n"
                report += f"{content}\n\n"
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
        return os.getenv("BIGMODEL_API_KEY") or os.getenv("WEB_SEARCH_API_KEY")

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

            # 如果会话没有用户ID，则允许所有用户访问（公共会话）
            if not session_info.get("user_id"):
                return True

            # 检查用户ID匹配
            return session_info.get("user_id") == user_id

        except Exception as e:
            print(f"验证会话访问权限失败: {str(e)}")
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
            if agent_report and isinstance(agent_report, str) and len(agent_report) > 100:
                print(f"✓ 使用 Agent 生成的报告，长度: {len(agent_report)} 字符")
                return {
                    "title": "深度研究报告",
                    "agent_report": agent_report,  # ✅ 保存完整的 Agent 报告
                    "metadata": {
                        "generated_at": datetime.now().isoformat(),
                        "report_source": "agent",
                        "report_length": len(agent_report)
                    }
                }
            
            # 如果没有 Agent 报告，则从 findings 生成
            print(f"⚠️ 未找到 Agent 报告，从 findings 生成")
            
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
                    "generated_at": datetime.now().isoformat(),
                    "total_findings": len(findings),
                    "total_citations": len(citations),
                    "quality_score": self._calculate_quality_score(findings, citations),
                    "quality_level": self._determine_quality_level(findings, citations),
                    "tools_count": len(tools_used),
                    "evidence_strength": evidence_chain.get("overall_strength", "medium")
                }
            }
            
            return formatted_report
            
        except Exception as e:
            print(f"格式化报告失败: {str(e)}")
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
                    "generated_at": datetime.now().isoformat(),
                    "total_findings": 0,
                    "total_citations": 0,
                    "quality_score": 0.0,
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
            key=lambda x: x.get("relevance_score", 0),
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
                key=lambda x: x.get("relevance_score", 0),
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
            "search_arxiv_papers": "📖 学术论文检索 - 获取同行评审的学术研究",
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
            key=lambda x: x.get("relevance_score", 0),
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

    def _calculate_quality_score(self, findings: List[Dict], citations: List[Dict]) -> float:
        """计算报告质量评分（0-1）"""
        score = 0.0
        
        # 发现数量评分（权重 30%）
        if len(findings) >= 15:
            score += 0.30
        elif len(findings) >= 10:
            score += 0.25
        elif len(findings) >= 5:
            score += 0.15
        elif len(findings) > 0:
            score += 0.05
        
        # 平均相关性评分（权重 40%）
        if findings:
            avg_relevance = sum(f.get("relevance_score", 0) for f in findings) / len(findings)
            score += avg_relevance * 0.40
        
        # 引用数量评分（权重 30%）
        if len(citations) >= 10:
            score += 0.30
        elif len(citations) >= 5:
            score += 0.20
        elif len(citations) >= 3:
            score += 0.12
        elif len(citations) > 0:
            score += 0.05
        
        return min(score, 1.0)

    def _determine_quality_level(self, findings: List[Dict], citations: List[Dict]) -> str:
        """确定证据质量等级"""
        score = self._calculate_quality_score(findings, citations)
        
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "medium"
        elif score >= 0.2:
            return "fair"
        else:
            return "low"

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
                avg_relevance = sum(f.get("relevance_score", 0) for f in source_findings) / len(source_findings)
                source_strengths[source] = {
                    "count": len(source_findings),
                    "avg_relevance": avg_relevance,
                    "strength": "strong" if avg_relevance >= 0.7 else "medium" if avg_relevance >= 0.4 else "weak"
                }
            
            # 提取证据关系
            relationships = self._extract_evidence_relationships(findings)
            
            # 计算整体证据强度
            overall_avg = sum(f.get("relevance_score", 0) for f in findings) / len(findings) if findings else 0
            overall_strength = "strong" if overall_avg >= 0.7 else "medium" if overall_avg >= 0.4 else "weak"
            
            return {
                "sources": findings_by_source,
                "source_strengths": source_strengths,
                "relationships": relationships,
                "overall_strength": overall_strength,
                "total_evidence_points": len(findings),
                "citation_support": len(citations)
            }
            
        except Exception as e:
            print(f"构建证据链失败: {str(e)}")
            return {
                "sources": {},
                "source_strengths": {},
                "relationships": [],
                "overall_strength": "weak",
                "total_evidence_points": 0,
                "citation_support": 0
            }

    def _extract_evidence_relationships(self, findings: List[Dict]) -> List[Dict]:
        """提取证据之间的关系"""
        relationships = []
        
        try:
            # 简单的关系提取：找出相关性高的发现对
            sorted_findings = sorted(findings, key=lambda x: x.get("relevance_score", 0), reverse=True)
            
            # 只处理前10个最相关的发现
            top_findings = sorted_findings[:10]
            
            for i, finding1 in enumerate(top_findings):
                for finding2 in top_findings[i+1:]:
                    # 如果两个发现来自不同来源但相关性都很高，认为它们相互支持
                    if (finding1.get("source_type") != finding2.get("source_type") and
                        finding1.get("relevance_score", 0) >= 0.6 and
                        finding2.get("relevance_score", 0) >= 0.6):
                        
                        relationships.append({
                            "type": "supports",
                            "from_source": finding1.get("source_type"),
                            "to_source": finding2.get("source_type"),
                            "strength": min(finding1.get("relevance_score", 0), finding2.get("relevance_score", 0))
                        })
            
            # 限制关系数量
            return relationships[:20]
            
        except Exception as e:
            print(f"提取证据关系失败: {str(e)}")
            return []

    def _extract_key_findings(self, findings: List[Dict]) -> List[Dict]:
        """提取关键发现（最重要的5-10个）"""
        try:
            # 按相关性排序
            sorted_findings = sorted(
                findings,
                key=lambda x: x.get("relevance_score", 0),
                reverse=True
            )
            
            # 提取前8个最相关的发现
            key_findings = []
            for finding in sorted_findings[:8]:
                key_findings.append({
                    "content": finding.get("content", "")[:300],  # 限制长度
                    "source_type": finding.get("source_type", "unknown"),
                    "relevance_score": finding.get("relevance_score", 0),
                    "quality": "high" if finding.get("relevance_score", 0) >= 0.7 else "medium" if finding.get("relevance_score", 0) >= 0.4 else "low"
                })
            
            return key_findings
            
        except Exception as e:
            print(f"提取关键发现失败: {str(e)}")
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
                print(f"✓ 返回 Agent 完整报告，长度: {len(agent_report)} 字符")
                return agent_report
            
            # 如果没有 Agent 报告，则从结构化数据生成
            print(f"⚠️ 从结构化数据生成报告")
            
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
            print(f"生成完整报告文本失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"# 报告生成失败\n\n错误: {str(e)}"
