# -*- coding: utf-8 -*-
"""
聊天API路由（学习模式）并记录数据库日志  # 模块说明
"""
import uuid  # 会话ID
import logging  # 日志
from typing import Optional  # 类型注解
from fastapi import APIRouter, HTTPException, Header  # FastAPI
from pydantic import BaseModel  # 模型
from langgraph.graph.message import HumanMessage  # 消息类型
from src.graph.builder import agent_graph  # 工作流图
from src.memory.conversation_buffer import get_conversation_buffer  # 对话缓冲
from src.server.routers.auth import verify_token  # Token校验
from src.server.db import insert_chat_log, insert_usage_log, get_user_by_username  # DB
from src.server.utils.sanitizer import strip_reasoning  # 输出清洗

logger = logging.getLogger(__name__)  # 日志器
router = APIRouter(prefix="/api", tags=["学习与研究模式"])  # 路由器


class ChatRequest(BaseModel):  # 请求模型
    message: str  # 用户消息
    session_id: Optional[str] = None  # 会话ID


class ChatResponse(BaseModel):  # 响应模型
    message: str  # 助手回复
    session_id: str  # 会话ID


@router.post("/chat", response_model=ChatResponse)
async def chat_handler(request: ChatRequest, authorization: str | None = Header(default=None)):
    """处理聊天请求并记录数据库日志（如提供Token）"""  # 函数说明
    session_id = request.session_id or f"chat-session-{uuid.uuid4()}"  # 会话ID
    buffer = get_conversation_buffer(session_id)  # 获取缓冲
    buffer.add_user_message(request.message)  # 写入用户消息

    inputs = [HumanMessage(content=m["content"]) for m in buffer.get_messages()]  # LangGraph输入
    config = {"configurable": {"thread_id": session_id}}  # 线程ID

    try:  # 执行工作流
        final_state = await agent_graph.ainvoke({"messages": inputs}, config)  # 运行
        ai_msg = final_state["messages"][-1]  # 取最后一条
        ai_text = getattr(ai_msg, "content", None) or ai_msg.get("content", "")  # 提取内容
        ai_text = strip_reasoning(ai_text)  # 过滤<think>/<reasoning>等
        buffer.add_assistant_message(ai_text)  # 写入助手消息

        # Token->UserID（可选）
        user_id = None
        if authorization and authorization.startswith("Bearer "):
            username = verify_token(authorization.split(" ", 1)[1])
            if username:
                user = get_user_by_username(username)
                user_id = user["id"] if user else None

        # 写入DB日志
        insert_chat_log(user_id, session_id, "user", request.message, None)
        insert_chat_log(user_id, session_id, "assistant", ai_text, None)
        insert_usage_log(user_id, endpoint="/api/chat", model=None, tokens_in=len(request.message), tokens_out=len(ai_text))

        return ChatResponse(message=ai_text, session_id=session_id)  # 返回
    except Exception as e:
        logger.error(f"聊天处理失败(session={session_id}): {e}", exc_info=True)  # 记录错误
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {e}")  # 返回500


