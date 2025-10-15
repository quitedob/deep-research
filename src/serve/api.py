from typing import List, Optional, Literal
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from src.api.deps import require_auth
from src.sqlmodel.models import User

from src.llms.router import ModelRouter, LLMMessage
from src.config.config_loader import get_settings
from src.export.markdown import MarkdownExporter
from src.export.ppt import PPTExporter

# 可选导出器 - 在缺少依赖时优雅降级
try:
    from src.export.pptx import PPTXExporter
    PPTX_AVAILABLE = True
except ImportError:
    PPTXExporter = None
    PPTX_AVAILABLE = False

try:
    from src.export.tts import TTSExporter
    TTS_AVAILABLE = True
except ImportError:
    TTSExporter = None
    TTS_AVAILABLE = False

try:
    from src.export.tts_edge import EdgeTTSExporter
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EdgeTTSExporter = None
    EDGE_TTS_AVAILABLE = False
from src.serve.chat_stream import router as stream_router
from src.api.auth import router as auth_router
from src.api.quota import router as quota_router
from src.api.deps import require_quota
 
from src.serve.session_store import store
from src.serve.sanitizer import sanitize_model_output


api_router = APIRouter()


class ChatItem(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatReq(BaseModel):
    task: Literal["triage", "simple_chat", "code", "reasoning", "research", "creative"] = "general"
    size: Literal["small", "medium", "large"] = "medium"
    messages: List[ChatItem] = Field(min_items=1)
    temperature: float = 0.7
    max_tokens: Optional[int] = None


class ChatResp(BaseModel):
    model: str
    content: str


class MDExportReq(BaseModel):
    title: str
    content: str
    out_path: Optional[str] = None


_router = ModelRouter.from_conf(Path("conf.yaml"))
_settings = get_settings()


@api_router.get("/health")
async def health():
    return await _router.health()


@api_router.get("/providers")
async def providers():
    info = await _router.health()
    return {"available": [name for name, st in info.get("providers", {}).items() if st.get("ok")], "details": info}


@api_router.post("/llm/chat", response_model=ChatResp, dependencies=[Depends(require_quota("chat"))])
async def llm_chat(req: ChatReq):
    try:
        msgs = [LLMMessage(role=m.role, content=m.content) for m in req.messages]
        result = await _router.chat(task=req.task, size=req.size, messages=msgs, temperature=req.temperature, max_tokens=req.max_tokens)
        return ChatResp(model=result["model"], content=sanitize_model_output(result["content"]))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/chat", response_model=ChatResp)
async def simple_chat(payload: dict):
    """兼容前端简单聊天接口：接受 {message, session_id} 并调用统一聊天，带会话记忆。"""
    message = payload.get("message", "")
    session_id = payload.get("session_id")
    if not message:
        raise HTTPException(status_code=400, detail="message is required")
    try:
        session_id = await store.ensure_session(session_id)
        history = await store.get_messages(session_id)
        await store.append_message(session_id, "user", message)

        # 将历史拼接发送（简单策略：直接传历史）
        msgs = [LLMMessage(role=m["role"], content=m["content"]) for m in history]
        msgs.append(LLMMessage(role="user", content=message))

        result = await _router.chat(task="general", size="medium", messages=msgs, temperature=0.7)
        final = sanitize_model_output(result["content"]) 
        await store.append_message(session_id, "assistant", final)
        return ChatResp(model=result["model"], content=final)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/export/markdown")
async def export_markdown(req: MDExportReq):
    exporter = MarkdownExporter()
    out = Path(req.out_path) if req.out_path else Path("outputs") / f"{req.title}.md"
    saved = exporter.save_to_file(content=req.content, title=req.title, output_path=out)
    return {"ok": True, "path": str(saved)}


class PPTExportReq(BaseModel):
    title: str
    content: str
    out_path: Optional[str] = None


@api_router.post("/export/ppt")
async def export_ppt(req: PPTExportReq):
    # 使用真实 .pptx 导出器
    if not PPTX_AVAILABLE:
        raise HTTPException(status_code=501, detail="PPT导出功能不可用：python-pptx库未安装")
    
    pptx_exporter = PPTXExporter()
    out = Path(req.out_path) if req.out_path else Path("outputs") / f"{req.title}.pptx"
    saved = pptx_exporter.save_to_file(content=req.content, title=req.title, output_path=out)
    return {"ok": True, "path": str(saved)}


class TTSExportReq(BaseModel):
    title: str
    content: str
    out_path: Optional[str] = None
    voice: Optional[str] = None
    speed: Optional[float] = None
    language: Optional[str] = None
    stream: bool = False


@api_router.post("/export/tts")
async def export_tts(req: TTSExportReq):
    # 如请求流式，则使用 EdgeTTSExporter 流式返回 audio/mpeg
    if req.stream:
        voice = req.voice or None
        lang = req.language or "zh-CN"
        gender = "female" if (req.voice or "").lower() == "female" else "male"
        
        if not EDGE_TTS_AVAILABLE:
            raise HTTPException(status_code=501, detail="TTS流式功能不可用：edge-tts库未安装")
        
        edge = EdgeTTSExporter()
        from fastapi.responses import StreamingResponse
        rate = f"{int(((req.speed or 1.0)-1.0)*100)}%"
        async def gen():
            async for chunk in edge.astream(req.content, voice=voice or edge.export.__self__ if False else (voice or "zh-CN-XiaoxiaoNeural"), rate=rate):
                yield chunk
        return StreamingResponse(gen(), media_type="audio/mpeg")

    # 否则写盘保存（占位或真实 edge-tts 可切换）
    # 优先使用 EdgeTTSExporter 生成 mp3；如未安装 edge-tts 则回退到占位 TTSExporter
    try:
        if not EDGE_TTS_AVAILABLE:
            raise ImportError("edge-tts not available")
        edge = EdgeTTSExporter()
        mp3_bytes = await edge._aexport_bytes(
            req.content,
            voice=req.voice or "zh-CN-XiaoxiaoNeural",
            rate=f"{int(((req.speed or 1.0)-1.0)*100)}%",
        )
        out = Path(req.out_path) if req.out_path else Path("outputs") / f"{req.title}.mp3"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(mp3_bytes)
        return {"ok": True, "path": str(out)}
    except Exception:
        exporter = TTSExporter()
        out = Path(req.out_path) if req.out_path else Path("outputs") / f"{req.title}.tts.txt"
        saved = exporter.save_to_file(
            content=req.content,
            title=req.title,
            output_path=out,
            voice=req.voice,
            speed=req.speed,
            language=req.language,
        )
        return {"ok": True, "path": str(saved)}


# 子路由：SSE 流式聊天
api_router.include_router(stream_router)

# 新增：认证与配额路由
api_router.include_router(auth_router)
api_router.include_router(quota_router)

# 新增：反馈路由
from src.api.feedback import router as feedback_router
api_router.include_router(feedback_router)

# 新增：内容审核路由
from src.api.moderation import router as moderation_router
api_router.include_router(moderation_router)

# 新增：系统监控路由
from src.api.monitoring import router as monitoring_router
api_router.include_router(monitoring_router)
 


# === 研究工作流最小打通（非流式）：与前端 API 对齐 ===

class ResearchReq(BaseModel):
    query: str
    session_id: Optional[str] = None


@api_router.post("/research")
async def start_research(req: ResearchReq):
    """多智能体研究端点：使用LangGraph工作流进行深度研究。"""
    try:
        session_id = await store.ensure_session(req.session_id)

        # 导入多智能体工作流
        from src.graph.builder import agent_graph

        # 初始化工作流状态
        initial_state = {
            "original_query": req.query,
            "iteration_count": 0,
            "error_log": [],
            "retrieved_documents": [],
            "analysis_results": {},
            "draft_report": None,
            "next_action": "supervisor",
            "human_review_required": False,
            "feedback_request": None,
            "user_feedback": None
        }

        # 运行多智能体工作流
        print(f"Starting research workflow for query: {req.query}")

        # 使用astream进行异步流式处理
        final_state = None
        async for state in agent_graph.astream(initial_state):
            final_state = state
            print(f"Workflow step completed. Next action: {state.get('next_action', 'unknown')}")

            # 如果工作流完成，退出循环
            if state.get("next_action") == "finish":
                break

        # 获取最终报告
        if final_state and final_state.get("draft_report"):
            report_content = final_state["draft_report"]
            print(f"Research completed successfully. Report length: {len(report_content)}")

            # 保存研究报告到会话存储
            await store.set_research_report(session_id, req.query, report_content)

            return {
                "session_id": session_id,
                "status": "completed",
                "documents_found": len(final_state.get("retrieved_documents", [])),
                "iterations": final_state.get("iteration_count", 0)
            }
        else:
            # 如果没有生成报告，创建一个错误报告
            error_report = f"# 研究失败\n\n查询: {req.query}\n\n错误: 工作流未能生成有效报告。请检查系统配置和日志。"
            await store.set_research_report(session_id, req.query, error_report)

            return {
                "session_id": session_id,
                "status": "failed",
                "error": "工作流未能生成有效报告"
            }

    except Exception as e:
        print(f"Research workflow error: {e}")
        import traceback
        traceback.print_exc()

        # 即使出错也要创建会话和基础报告
        try:
            session_id = await store.ensure_session(req.session_id)
            error_report = f"# 研究错误\n\n查询: {req.query}\n\n系统错误: {str(e)}\n\n请稍后重试或联系管理员。"
            await store.set_research_report(session_id, req.query, error_report)

            return {
                "session_id": session_id,
                "status": "error",
                "error": str(e)
            }
        except Exception as inner_e:
            raise HTTPException(status_code=500, detail=f"研究失败: {str(e)}")


@api_router.get("/research/{session_id}")
async def get_research_report(session_id: str):
    doc = await store.get_research_report(session_id)
    if not doc:
        raise HTTPException(status_code=404, detail="report not ready")
    return doc


@api_router.get("/research/stream/{session_id}")
async def research_stream(session_id: str):
    """最小可用研究流式端点：发送若干进度事件，最后发送 completed 状态。
    前端收到 completed 后会调用 /api/research/{session_id} 拉取最终报告。
    """
    from fastapi.responses import StreamingResponse
    import asyncio

    async def _gen():
        try:
            yield "data: {\"phase\":\"planning\",\"message\":\"生成研究计划...\"}\n\n".encode("utf-8")
            await asyncio.sleep(0.05)
            yield "data: {\"phase\":\"collecting\",\"message\":\"检索与收集资料...\"}\n\n".encode("utf-8")
            await asyncio.sleep(0.05)
            yield "data: {\"phase\":\"synthesizing\",\"message\":\"撰写报告...\"}\n\n".encode("utf-8")
            await asyncio.sleep(0.05)
            yield "data: {\"status\":\"completed\"}\n\n".encode("utf-8")
        except Exception as e:
            yield f"data: {{\"status\":\"failed\",\"error\":{str(e)!r}}}\n\n".encode("utf-8")

    return StreamingResponse(_gen(), media_type="text/event-stream")


# === 历史记录（最小实现，供前端侧边栏使用） ===

@api_router.get("/histories")
async def list_histories():
    sessions = await store.list_sessions()
    items = []
    for sid in sessions:
        msgs = await store.get_messages(sid)
        # 标题来源：第一条用户消息或 session_id 简短形式
        title = None
        for m in msgs:
            if m.get("role") == "user" and m.get("content"):
                title = m["content"][:24]
                break
        if not title:
            title = f"会话 {sid[:8]}"
        items.append({"session_id": sid, "title": title})
    return items


@api_router.get("/histories/{session_id}")
async def get_history_messages(session_id: str):
    return await store.get_messages(session_id)


@api_router.delete("/histories")
async def delete_all_histories():
    await store.clear_all()
    return {"ok": True}


# === 对话历史搜索功能 ===

class ConversationSearchRequest(BaseModel):
    """对话搜索请求"""
    query: str
    session_id: Optional[str] = None
    limit: int = Field(20, le=100, description="返回结果数量限制")
    offset: int = Field(0, ge=0, description="偏移量")
    filters: Optional[dict] = Field(default_factory=dict)

class ConversationSearchResponse(BaseModel):
    """对话搜索响应"""
    total: int
    results: List[dict]
    query: str
    suggestions: List[str] = []
    search_time: float


@api_router.post("/search/conversations", response_model=ConversationSearchResponse)
async def search_conversations(
    request: ConversationSearchRequest,
    current_user: User = Depends(require_auth)
):
    """
    搜索对话历史

    支持全文搜索、过滤和排序
    """
    try:
        import time
        start_time = time.time()

        # 获取所有会话
        sessions = await store.list_sessions()
        all_results = []

        # 解析过滤条件
        filters = request.filters or {}
        date_from = filters.get("date_from")
        date_to = filters.get("date_to")
        role = filters.get("role")
        feedback_status = filters.get("feedback_status")

        # 搜索每个会话
        for session_id in sessions:
            # 如果指定了session_id，只搜索该会话
            if request.session_id and session_id != request.session_id:
                continue

            messages = await store.get_messages(session_id)
            session_title = None

            for msg in messages:
                # 获取会话标题（第一条用户消息）
                if not session_title and msg.get("role") == "user":
                    session_title = msg["content"][:50]

                # 角色过滤
                if role and msg.get("role") != role:
                    continue

                # 简单的文本匹配搜索
                content = msg.get("content", "").lower()
                query_lower = request.query.lower()

                if query_lower in content:
                    # 创建搜索结果片段
                    result_msg = msg.copy()
                    result_msg["session_id"] = session_id
                    result_msg["session_title"] = session_title or f"会话 {session_id[:8]}"

                    # 添加高亮信息
                    content_lower = result_msg["content"].lower()
                    query_index = content_lower.find(query_lower)
                    if query_index != -1:
                        start = max(0, query_index - 50)
                        end = min(len(result_msg["content"]), query_index + len(request.query) + 50)
                        highlight = result_msg["content"][start:end]
                        if start > 0:
                            highlight = "..." + highlight
                        if end < len(result_msg["content"]):
                            highlight = highlight + "..."
                        result_msg["highlight"] = highlight

                    # 计算相关性分数（简单的匹配度）
                    score = content.count(query_lower) * len(request.query) / len(content) if content else 0
                    result_msg["relevance_score"] = score

                    all_results.append(result_msg)

        # 排序结果（按相关性分数）
        all_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        # 分页
        total = len(all_results)
        paginated_results = all_results[request.offset:request.offset + request.limit]

        # 生成搜索建议（基于常见词）
        suggestions = []
        if total > 0:
            # 简单的建议生成逻辑
            common_words = ["模型", "API", "配置", "错误", "功能", "系统", "数据", "用户"]
            for word in common_words:
                if word not in request.query and word in request.query:
                    suggestions.append(f"{request.query} {word}")
            suggestions = suggestions[:3]

        search_time = time.time() - start_time

        return ConversationSearchResponse(
            total=total,
            results=paginated_results,
            query=request.query,
            suggestions=suggestions,
            search_time=search_time
        )

    except Exception as e:
        logger.error(f"对话搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/search/suggestions")
async def get_search_suggestions(
    q: str = Query(..., description="搜索查询前缀"),
    current_user: User = Depends(require_auth)
):
    """
    获取搜索建议

    基于历史搜索和常见模式提供建议
    """
    try:
        # 简单的建议逻辑
        suggestions = []

        # 常见搜索前缀
        common_prefixes = [
            "配置", "模型", "API", "错误", "功能", "系统", "数据", "用户",
            "设置", "问题", "解决", "方法", "代码", "示例", "文档"
        ]

        # 基于输入前缀匹配
        for prefix in common_prefixes:
            if prefix.startswith(q) or q in prefix:
                suggestions.append(prefix)

        # 基于可能的完整查询建议
        if len(q) > 2:
            extended_suggestions = [
                f"{q}配置",
                f"{q}设置",
                f"{q}问题",
                f"{q}解决方案",
                f"{q}示例"
            ]
            suggestions.extend(extended_suggestions)

        # 去重并限制数量
        suggestions = list(set(suggestions))[:10]

        return {"suggestions": suggestions}

    except Exception as e:
        logger.error(f"获取搜索建议失败: {e}")
        return {"suggestions": []}


@api_router.get("/search/recent")
async def get_recent_searches(
    limit: int = Query(5, le=20, description="返回数量限制"),
    current_user: User = Depends(require_auth)
):
    """
    获取最近的搜索历史

    注意：这是一个简化实现，实际应用中可能需要持久化存储
    """
    try:
        # 这里返回一些默认的"最近搜索"
        # 在实际应用中，应该从数据库或缓存中获取真实的搜索历史
        recent_searches = [
            "API配置",
            "模型设置",
            "错误处理",
            "功能介绍",
            "系统使用"
        ]

        return {"recent_searches": recent_searches[:limit]}

    except Exception as e:
        logger.error(f"获取最近搜索失败: {e}")
        return {"recent_searches": []}


# === 对话分享功能 ===

class ShareConversationRequest(BaseModel):
    """对话分享请求"""
    session_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    expire_days: int = Field(30, ge=1, le=365, description="分享链接有效期（天）")

class ShareConversationResponse(BaseModel):
    """对话分享响应"""
    share_id: str
    public_url: str
    title: str
    expires_at: str
    created_at: str

class PublicConversationResponse(BaseModel):
    """公开对话响应"""
    share_id: str
    title: str
    description: Optional[str]
    messages: List[dict]
    created_at: str
    expires_at: str
    view_count: int


# 简单的内存存储（实际应用中应使用数据库）
_conversation_shares = {}


@api_router.post("/share/conversation", response_model=ShareConversationResponse)
async def share_conversation(
    request: ShareConversationRequest,
    current_user: User = Depends(require_auth)
):
    """
    创建对话分享链接

    生成公开链接，允许他人查看对话内容
    """
    try:
        import secrets
        import hashlib
        from datetime import datetime, timedelta

        # 验证会话是否存在
        messages = await store.get_messages(request.session_id)
        if not messages:
            raise HTTPException(status_code=404, detail="会话不存在")

        # 生成唯一的分享ID
        share_id = secrets.token_urlsafe(16)

        # 设置过期时间
        expires_at = datetime.utcnow() + timedelta(days=request.expire_days)

        # 获取会话标题
        title = request.title
        if not title:
            # 使用第一条用户消息作为标题
            for msg in messages:
                if msg.get("role") == "user":
                    title = msg["content"][:50] + ("..." if len(msg["content"]) > 50 else "")
                    break
        if not title:
            title = f"对话分享 {share_id[:8]}"

        # 创建分享记录
        share_record = {
            "share_id": share_id,
            "session_id": request.session_id,
            "owner_user_id": current_user.id,
            "title": title,
            "description": request.description,
            "messages": messages,  # 存储消息快照
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat(),
            "view_count": 0,
            "is_active": True
        }

        # 存储分享记录（实际应用中应使用数据库）
        _conversation_shares[share_id] = share_record

        # 生成公开URL
        public_url = f"/public/conversation/{share_id}"

        logger.info(f"用户 {current_user.id} 创建了对话分享: {share_id}")

        return ShareConversationResponse(
            share_id=share_id,
            public_url=public_url,
            title=title,
            expires_at=expires_at.isoformat(),
            created_at=share_record["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建对话分享失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/share/my-shares")
async def get_my_shares(
    current_user: User = Depends(require_auth)
):
    """
    获取我的对话分享列表

    显示当前用户创建的所有分享链接
    """
    try:
        from datetime import datetime

        my_shares = []
        current_time = datetime.utcnow()

        for share_id, share in _conversation_shares.items():
            if share.get("owner_user_id") == current_user.id:
                # 检查是否过期
                expires_at = datetime.fromisoformat(share["expires_at"])
                is_expired = current_time > expires_at

                share_info = {
                    "share_id": share_id,
                    "title": share["title"],
                    "public_url": f"/public/conversation/{share_id}",
                    "created_at": share["created_at"],
                    "expires_at": share["expires_at"],
                    "view_count": share.get("view_count", 0),
                    "is_expired": is_expired,
                    "is_active": share.get("is_active", False) and not is_expired
                }
                my_shares.append(share_info)

        # 按创建时间倒序排列
        my_shares.sort(key=lambda x: x["created_at"], reverse=True)

        return {"shares": my_shares}

    except Exception as e:
        logger.error(f"获取分享列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/share/{share_id}")
async def delete_share(
    share_id: str,
    current_user: User = Depends(require_auth)
):
    """
    删除对话分享链接

    立即失效分享链接
    """
    try:
        if share_id not in _conversation_shares:
            raise HTTPException(status_code=404, detail="分享不存在")

        share = _conversation_shares[share_id]
        if share.get("owner_user_id") != current_user.id:
            raise HTTPException(status_code=403, detail="无权限删除此分享")

        # 删除分享记录
        del _conversation_shares[share_id]

        logger.info(f"用户 {current_user.id} 删除了对话分享: {share_id}")

        return {"message": "分享链接已删除"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除分享失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 公开访问端点（不需要认证）
@api_router.get("/public/conversation/{share_id}", response_model=PublicConversationResponse)
async def get_public_conversation(share_id: str):
    """
    获取公开对话内容

    通过分享链接访问对话内容
    """
    try:
        from datetime import datetime

        if share_id not in _conversation_shares:
            raise HTTPException(status_code=404, detail="分享不存在或已过期")

        share = _conversation_shares[share_id]

        # 检查分享是否有效
        if not share.get("is_active", False):
            raise HTTPException(status_code=403, detail="分享已失效")

        # 检查是否过期
        expires_at = datetime.fromisoformat(share["expires_at"])
        current_time = datetime.utcnow()
        if current_time > expires_at:
            raise HTTPException(status_code=403, detail="分享已过期")

        # 增加访问计数
        share["view_count"] = share.get("view_count", 0) + 1

        return PublicConversationResponse(
            share_id=share_id,
            title=share["title"],
            description=share.get("description"),
            messages=share["messages"],
            created_at=share["created_at"],
            expires_at=share["expires_at"],
            view_count=share["view_count"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取公开对话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


