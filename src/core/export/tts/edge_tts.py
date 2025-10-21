from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncIterator, Optional

from .base import Exporter


def _voice_name(language: str, gender: str) -> str:
    lang = (language or "zh-CN").lower()
    gen = (gender or "female").lower()
    if lang.startswith("zh"):
        return "zh-Cn-XiaoxiaoNeural" if gen == "female" else "zh-CN-YunxiNeural"
    return "en-US-JennyNeural" if gen == "female" else "en-US-GuyNeural"


def _rate_from_speed(speed: Optional[float]) -> str:
    try:
        s = float(speed) if speed is not None else 1.0
    except Exception:
        s = 1.0
    pct = int((s - 1.0) * 100)
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct}%"


class EdgeTTSExporter(Exporter):
    """Edge TTS 导出器：生成 mp3 字节；并提供异步流式接口。"""

    def export(self, content: str, title: str, **kwargs) -> bytes:
        voice = kwargs.get("voice") or _voice_name(kwargs.get("language", "zh-CN"), kwargs.get("gender", "female"))
        rate = kwargs.get("rate") or _rate_from_speed(kwargs.get("speed"))
        return asyncio.run(self._aexport_bytes(content, voice=voice, rate=rate))

    async def astream(self, content: str, *, voice: str, rate: str) -> AsyncIterator[bytes]:
        try:
            import edge_tts  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError("edge-tts is not installed") from e

        communicate = edge_tts.Communicate(content, voice=voice, rate=rate)
        async for chunk in communicate.stream():
            if chunk.get("type") == "audio" and chunk.get("data"):
                yield chunk["data"]

    async def _aexport_bytes(self, content: str, *, voice: str, rate: str) -> bytes:
        try:
            import edge_tts  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError("edge-tts is not installed") from e

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            communicate = edge_tts.Communicate(content, voice=voice, rate=rate)
            await communicate.save(tmp_path)
            return Path(tmp_path).read_bytes()
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass


