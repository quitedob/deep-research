#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度研究API接口
提供AgentScope深度研究功能的REST API
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio
import json

from src.services.agentscope_research_service import AgentScopeResearchService
from src.middleware.auth import get_current_user, get_optional_user
from src.schemas.research import (
    ResearchRequest,
    ResearchResponse,
    ResearchStatusResponse,
    ResearchListResponse,
    ResearchExportResponse
)


# 创建路由器
router = APIRouter(prefix="/api/research", tags=["deep-research"])

# 创建服务实例
research_service = AgentScopeResearchService()


@router.post("/start", response_model=ResearchResponse)
async def start_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    启动深度研究
    """
    try:
        # 从认证的用户信息中获取用户ID
        user_id = current_user["user_id"]

        # 处理 LLM 配置
        llm_provider = None
        if request.llm_config:
            llm_provider = request.llm_config.get("provider", "zhipu")
        
        # 处理多模态 LLM 配置（如果需要）
        multimodal_llm_instance = None
        if request.include_images and request.multimodal_llm_config:
            from src.core.llm.factory import LLMFactory
            try:
                multimodal_llm_instance = LLMFactory.create_llm(
                    provider="ollama",
                    base_url=request.multimodal_llm_config.get("host", "http://localhost:11434"),
                    model=request.multimodal_llm_config.get("model_name", "gemma3:4b")
                )
            except Exception as e:
                print(f"警告: 创建多模态LLM失败: {e}")

        # 启动研究
        result = await research_service.start_research(
            query=request.query,
            user_id=user_id,
            research_type=request.research_type,
            sources=request.sources,
            include_images=request.include_images,
            llm_provider=llm_provider,
            multimodal_llm_instance=multimodal_llm_instance,
            session_id=request.session_id
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "启动研究失败"))

        # 添加后台任务监控研究进度
        if result.get("session_id"):
            background_tasks.add_task(
                monitor_research_progress,
                result["session_id"],
                user_id
            )

        return ResearchResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动研究时出错: {str(e)}")


@router.get("/status/{session_id}", response_model=ResearchStatusResponse)
async def get_research_status(
    session_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    获取研究状态（不需要认证，但会验证会话访问权限）
    """
    try:
        # 如果提供了用户信息，验证访问权限
        if current_user:
            user_id = current_user["user_id"]
            has_access = await research_service.validate_session_access(session_id, user_id)
            if not has_access:
                raise HTTPException(status_code=403, detail="无权访问此研究会话")

        # 获取状态
        status = await research_service.get_research_status(session_id)

        return ResearchStatusResponse(
            success=True,
            session_id=session_id,
            status_data=status,
            message="获取状态成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取研究状态时出错: {str(e)}")


@router.post("/interrupt/{session_id}")
async def interrupt_research(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    中断研究会话
    """
    try:
        # 从认证的用户信息中获取用户ID
        user_id = current_user["user_id"]

        # 验证访问权限
        has_access = await research_service.validate_session_access(session_id, user_id)
        if not has_access:
            raise HTTPException(status_code=403, detail="无权访问此研究会话")

        # 中断研究
        result = await research_service.interrupt_research(session_id)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "中断研究失败"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"中断研究时出错: {str(e)}")


@router.post("/resume/{session_id}")
async def resume_research(
    session_id: str,
    state_data: Optional[Dict[str, Any]] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    恢复被中断的研究
    """
    try:
        # 从认证的用户信息中获取用户ID
        user_id = current_user["user_id"]

        # 验证访问权限
        has_access = await research_service.validate_session_access(session_id, user_id)
        if not has_access:
            raise HTTPException(status_code=403, detail="无权访问此研究会话")

        # 恢复研究
        result = await research_service.resume_research(session_id, state_data)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "恢复研究失败"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"恢复研究时出错: {str(e)}")


@router.get("/sessions", response_model=ResearchListResponse)
async def get_user_sessions(
    status: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    user_id: Optional[str] = Query(None, description="用户ID（可选，用于过滤特定用户的会话）"),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    获取研究会话列表（不需要认证）
    如果提供了user_id参数，则只返回该用户的会话
    """
    try:
        # 优先使用查询参数中的user_id，否则使用认证用户的ID
        if not user_id and current_user:
            user_id = current_user["user_id"]
        
        # 如果都没有，返回所有会话（可能需要限制）
        if not user_id:
            user_id = None  # 返回所有会话

        # 获取会话列表
        sessions = await research_service.get_user_sessions(
            user_id=user_id,
            status=status,
            limit=limit
        )

        return ResearchListResponse(
            success=True,
            sessions=sessions,
            total=len(sessions),
            message="获取会话列表成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话列表时出错: {str(e)}")


@router.get("/export/{session_id}", response_model=ResearchExportResponse)
async def export_session_data(
    session_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    导出会话数据（不需要认证，但会验证会话访问权限）
    """
    try:
        # 如果提供了用户信息，验证访问权限
        if current_user:
            user_id = current_user["user_id"]
            has_access = await research_service.validate_session_access(session_id, user_id)
            if not has_access:
                raise HTTPException(status_code=403, detail="无权访问此研究会话")

        # 导出数据
        data = await research_service.export_session_data(session_id)

        if not data:
            raise HTTPException(status_code=404, detail="会话数据不存在")

        # 构建响应（直接返回字典，让 FastAPI 处理）
        return {
            "success": True,
            "session_id": session_id,
            "data": data,
            "exported_at": data.get("exported_at", datetime.now().isoformat()),
            "message": "导出数据成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出会话数据时出错: {str(e)}")


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    删除研究会话
    """
    try:
        # 从认证的用户信息中获取用户ID
        user_id = current_user["user_id"]

        # 验证访问权限
        has_access = await research_service.validate_session_access(session_id, user_id)
        if not has_access:
            raise HTTPException(status_code=403, detail="无权访问此研究会话")

        # 删除会话
        result = await research_service.delete_session(session_id)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "删除会话失败"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除会话时出错: {str(e)}")


@router.get("/search")
async def search_research_content(
    query: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: Optional[str] = Query(None, description="用户ID（可选，用于过滤特定用户的内容）"),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    搜索研究内容（不需要认证）
    如果提供了user_id参数，则只搜索该用户的内容
    """
    try:
        # 优先使用查询参数中的user_id，否则使用认证用户的ID
        if not user_id and current_user:
            user_id = current_user["user_id"]

        # 搜索内容
        results = await research_service.search_research_content(
            query=query,
            user_id=user_id,
            limit=limit
        )

        return {
            "success": True,
            "query": query,
            "results": results,
            "total": len(results),
            "message": "搜索完成"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索研究内容时出错: {str(e)}")


@router.get("/statistics")
async def get_research_statistics(
    user_id: Optional[str] = Query(None, description="用户ID（可选，用于获取特定用户的统计）"),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    获取研究统计信息（不需要认证）
    如果提供了user_id参数，则返回该用户的统计；否则返回全局统计
    """
    try:
        # 优先使用查询参数中的user_id，否则使用认证用户的ID
        if not user_id and current_user:
            user_id = current_user["user_id"]
        
        # 检查是否为管理员用户
        is_admin = current_user.get("is_admin", False) if current_user else False

        # 获取统计信息（用户级别或全局级别）
        stats = await research_service.get_research_statistics(
            user_id=user_id if not is_admin else None
        )

        return {
            "success": True,
            "statistics": stats,
            "scope": "user" if not is_admin else "global",
            "message": "获取统计信息成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取研究统计时出错: {str(e)}")


@router.post("/cleanup")
async def cleanup_inactive_sessions(
    inactive_hours: int = Query(default=24, ge=1, le=168),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    清理非活跃会话（仅管理员）
    """
    try:
        # 只有管理员可以执行清理操作
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="权限不足：仅管理员可执行此操作")

        # 执行清理
        result = await research_service.cleanup_inactive_sessions(inactive_hours)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理非活跃会话时出错: {str(e)}")


@router.get("/stream/{session_id}")
async def stream_research_progress(
    session_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    ✅ SSE 端点：后端主动推送研究进度，前端只需监听
    """
    async def event_generator():
        """生成 SSE 事件流 - 分段推送避免 payload 过大"""
        try:
            # 1. 发送连接成功消息
            yield f"data: {json.dumps({'type': 'connected', 'session_id': session_id}, ensure_ascii=False)}\n\n"
            
            last_status = None
            
            while True:
                # 获取研究状态
                status_data = await research_service.get_research_status(session_id)
                current_status = status_data.get("status")
                
                # 2. 推送状态更新
                if current_status != last_status:
                    print(f"✓ SSE: 状态变化 {last_status} -> {current_status}")
                    event = {
                        "type": "status_update",
                        "status": current_status,
                        "data": status_data
                    }
                    try:
                        json_str = json.dumps(event, ensure_ascii=False, default=str)
                        yield f"data: {json_str}\n\n"
                        last_status = current_status
                    except Exception as e:
                        print(f"✗ SSE: 状态更新序列化失败: {str(e)}")
                
                # 研究完成，推送最终报告
                if current_status == "completed":
                    print(f"✓ SSE: 研究完成，准备生成最终报告...")
                    export_data = await research_service.export_session_data(session_id)
                    
                    if export_data:
                        try:
                            # 生成格式化报告
                            formatted_report = await research_service.format_final_report(
                                session_id,
                                export_data
                            )
                            
                            # 生成完整的报告文本
                            full_report_text = research_service.generate_full_report_text(formatted_report)
                            
                            print(f"✓ SSE: 报告已生成，长度: {len(full_report_text)} 字符")
                            
                            # ✅ 转换引用数据为前端证据链格式
                            citations = export_data.get("citations", [])
                            evidence_list = []
                            for idx, citation in enumerate(citations):
                                source_url = citation.get("source_url", "")
                                # 判断来源类型
                                if "wikipedia" in source_url.lower():
                                    source_type = "web"
                                elif "arxiv" in source_url.lower():
                                    source_type = "document"
                                else:
                                    source_type = "web"
                                
                                evidence_list.append({
                                    "id": idx + 1,
                                    "source_type": source_type,
                                    "source_title": citation.get("title", "未知来源"),
                                    "source_url": source_url,
                                    "content": f"引用自: {citation.get('title', '')}",
                                    "snippet": citation.get("title", ""),
                                    "relevance_score": 0.95,
                                    "confidence_score": 0.90
                                })
                            
                            print(f"✓ SSE: 证据链数量: {len(evidence_list)}")
                            
                            # 推送完成事件（包含报告文本和证据链）
                            final_event = {
                                "type": "completed",
                                "status": "completed",
                                "data": {
                                    "report_text": full_report_text,  # ✅ 完整的报告文本
                                    "session_id": session_id,
                                    "metadata": {
                                        "type": "research",
                                        "session_id": session_id,
                                        "evidence": evidence_list,  # ✅ 证据链数据
                                        "citations": citations
                                    }
                                }
                            }
                            yield f"data: {json.dumps(final_event, ensure_ascii=False, default=str)}\n\n"
                            print(f"✓ SSE: 完整报告和证据链已推送")
                            
                        except Exception as e:
                            print(f"✗ SSE: 生成报告失败: {str(e)}")
                            import traceback
                            traceback.print_exc()
                            error_event = {
                                "type": "error",
                                "error": f"生成报告失败: {str(e)}"
                            }
                            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
                    else:
                        print(f"⚠️ SSE: 报告数据为空")
                        error_event = {
                            "type": "error",
                            "error": "报告数据为空"
                        }
                        yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
                    break
                    
                elif current_status == "failed":
                    error_event = {
                        "type": "failed",
                        "status": "failed",
                        "error": status_data.get("error", "研究失败")
                    }
                    yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
                    break
                    
                elif current_status == "not_found":
                    not_found_event = {
                        "type": "error",
                        "error": "会话不存在"
                    }
                    yield f"data: {json.dumps(not_found_event, ensure_ascii=False)}\n\n"
                    break
                
                # 等待3秒再检查
                await asyncio.sleep(3)
                
        except asyncio.CancelledError:
            print(f"客户端断开 SSE 连接: {session_id}")
        except Exception as e:
            print(f"✗ SSE: 事件生成器异常: {str(e)}")
            import traceback
            traceback.print_exc()
            error_event = {
                "type": "error",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 nginx 缓冲
        }
    )


async def monitor_research_progress(session_id: str, user_id: str):
    """
    监控研究进度的后台任务（已废弃，使用 SSE 替代）

    Args:
        session_id: 会话ID
        user_id: 用户ID
    """
    # 不再需要，SSE 会处理进度推送
    pass


# WebSocket端点用于实时进度更新（可选功能）
@router.websocket("/ws/progress/{session_id}")
async def websocket_research_progress(websocket, session_id: str):
    """
    实时研究进度WebSocket连接
    """
    try:
        await websocket.accept()

        # 验证WebSocket连接（简化版，实际应该验证token）
        # 这里应该添加WebSocket认证逻辑

        # 发送初始状态
        initial_status = await research_service.get_research_status(session_id)
        await websocket.send_json(initial_status)

        # 定期发送更新
        while True:
            await asyncio.sleep(5)  # 每5秒发送一次更新

            status = await research_service.get_research_status(session_id)
            await websocket.send_json(status)

            # 如果研究完成，关闭连接
            if status.get("status") in ["completed", "failed"]:
                break

    except Exception as e:
        print(f"WebSocket连接出错: {str(e)}")
    finally:
        await websocket.close()