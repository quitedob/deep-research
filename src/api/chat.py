#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话API路由
处理对话会话和消息的接口
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List, Optional

from src.schemas.chat import (
    ChatSessionCreate, ChatSessionUpdate, ChatSessionResponse,
    ChatRequest, ChatResponse, ChatMessage, ModelListResponse
)
from src.services.chat_service import ChatService
from src.api.user import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["对话管理"])
chat_service = ChatService()


@router.post("/sessions", response_model=ChatSessionResponse, summary="创建对话会话")
async def create_session(
    session_data: ChatSessionCreate,
    user_id: str = Depends(get_current_user_id)
):
    """
    创建新的对话会话
    
    - **title**: 会话标题
    - **llm_provider**: LLM提供商（deepseek/zhipu）
    - **model_name**: 模型名称
    - **system_prompt**: 系统提示词（可选）
    """
    try:
        session = await chat_service.create_session(user_id, session_data)
        if not session:
            raise HTTPException(status_code=500, detail="创建会话失败")
        return session
    except Exception as e:
        logger.error(f"创建会话失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=List[ChatSessionResponse], summary="获取会话列表")
async def get_sessions(
    limit: int = 50,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id)
):
    """获取当前用户的对话会话列表"""
    try:
        sessions = await chat_service.get_user_sessions(user_id, limit, offset)
        return sessions
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse, summary="获取会话详情")
async def get_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """获取指定会话的详细信息"""
    session = await chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 验证会话所有权
    if session['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="无权访问此会话")
    
    return session


@router.put("/sessions/{session_id}", summary="更新会话")
async def update_session(
    session_id: str,
    update_data: ChatSessionUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """更新会话信息"""
    # 验证会话所有权
    session = await chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    if session['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="无权访问此会话")
    
    success = await chat_service.update_session(session_id, update_data)
    if not success:
        raise HTTPException(status_code=500, detail="更新失败")
    
    return {"success": True, "message": "会话更新成功"}


@router.delete("/sessions/{session_id}", summary="删除会话")
async def delete_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """删除指定会话"""
    # 验证会话所有权
    session = await chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    if session['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="无权访问此会话")
    
    success = await chat_service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=500, detail="删除失败")
    
    return {"success": True, "message": "会话删除成功"}


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessage], summary="获取会话消息")
async def get_messages(
    session_id: str,
    limit: Optional[int] = None,
    user_id: str = Depends(get_current_user_id)
):
    """获取指定会话的消息列表"""
    # 验证会话所有权
    session = await chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    if session['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="无权访问此会话")
    
    messages = await chat_service.get_session_messages(session_id, limit)
    return messages


@router.delete("/sessions/{session_id}/messages", summary="清空会话消息")
async def clear_messages(
    session_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """清空指定会话的所有消息"""
    # 验证会话所有权
    session = await chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    if session['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="无权访问此会话")
    
    success = await chat_service.clear_session_messages(session_id)
    if not success:
        raise HTTPException(status_code=500, detail="清空失败")
    
    return {"success": True, "message": "消息已清空"}


@router.post("/chat", response_model=ChatResponse, summary="发送对话消息")
async def chat(
    chat_request: ChatRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id)
):
    """
    发送对话消息（非流式）
    
    - **session_id**: 会话ID
    - **message**: 用户消息内容
    - **stream**: 是否使用流式输出（此接口固定为false）
    
    集成Mem0记忆系统：
    - 自动检索相关历史记忆增强上下文
    - 后台异步提取对话中的关键事实
    """
    # 验证会话所有权
    session = await chat_service.get_session(chat_request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    if session['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="无权访问此会话")
    
    try:
        response = await chat_service.chat(chat_request, background_tasks)
        return response
    except Exception as e:
        logger.error(f"对话失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream", summary="发送对话消息（流式）")
async def chat_stream(
    chat_request: ChatRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    发送对话消息（流式输出）
    
    - **session_id**: 会话ID
    - **message**: 用户消息内容
    - **stream**: 是否使用流式输出（此接口固定为true）
    """
    # 验证会话所有权
    session = await chat_service.get_session(chat_request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    if session['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="无权访问此会话")
    
    try:
        return StreamingResponse(
            chat_service.chat_stream(chat_request),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"流式对话失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", response_model=ModelListResponse, summary="获取可用模型列表")
async def get_models():
    """
    获取所有可用的LLM模型列表
    
    返回支持的提供商和模型信息，包括：
    - 模型名称和显示名称
    - 模型描述
    - 上下文长度
    - 支持的能力
    """
    return chat_service.get_available_models()


@router.post("/chat/web-search", response_model=ChatResponse, summary="联网搜索对话")
async def chat_web_search(
    chat_request: ChatRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    发送对话消息（联网搜索模式）
    
    流程：
    1. LLM生成5-10个搜索查询
    2. 执行网络搜索
    3. LLM整合搜索结果回答问题
    
    - **session_id**: 会话ID
    - **message**: 用户消息内容
    """
    # 验证会话所有权
    session = await chat_service.get_session(chat_request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    if session['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="无权访问此会话")
    
    try:
        # 获取API密钥（用于网络搜索）
        import os
        api_key = os.getenv("BIGMODEL_API_KEY")
        
        response = await chat_service.web_search_chat(chat_request, api_key)
        return response
    except Exception as e:
        logger.error(f"联网搜索对话失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
