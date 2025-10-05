from typing import List, Optional, Literal
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

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


