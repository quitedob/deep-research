# -*- coding: utf-8 -*-
"""
导出功能API端点
"""

from typing import Optional
from pathlib import Path
import logging

from fastapi import APIRouter, HTTPException
from src.export.markdown import MarkdownExporter
from src.export.ppt import PPTExporter
from src.schemas.export import MDExportReq, PPTExportReq, TTSExportReq

logger = logging.getLogger(__name__)

router = APIRouter()

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

@router.post("/export/markdown")
async def export_markdown(req: MDExportReq):
    """导出Markdown文件"""
    try:
        exporter = MarkdownExporter()
        out = Path(req.out_path) if req.out_path else Path("outputs") / f"{req.title}.md"
        saved = exporter.save_to_file(content=req.content, title=req.title, output_path=out)
        return {"ok": True, "path": str(saved)}
    except Exception as e:
        logger.error(f"Markdown导出失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export/ppt")
async def export_ppt(req: PPTExportReq):
    """导出PPT文件"""
    try:
        # 使用真实 .pptx 导出器
        if not PPTX_AVAILABLE:
            raise HTTPException(status_code=501, detail="PPT导出功能不可用：python-pptx库未安装")

        pptx_exporter = PPTXExporter()
        out = Path(req.out_path) if req.out_path else Path("outputs") / f"{req.title}.pptx"
        saved = pptx_exporter.save_to_file(content=req.content, title=req.title, output_path=out)
        return {"ok": True, "path": str(saved)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PPT导出失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export/tts")
async def export_tts(req: TTSExportReq):
    """TTS语音导出"""
    try:
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS导出失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))