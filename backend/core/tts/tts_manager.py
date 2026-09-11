# -*- coding: utf-8 -*-
"""
TTS管理器 - 统一管理所有TTS引擎
TTS Manager - Unified management for all TTS engines
"""

import asyncio
from enum import Enum
from pathlib import Path
from typing import Optional, AsyncIterator
import hashlib
import json
import re
import uuid

from logging import getLogger as get_logger
logger = get_logger("tts")


class TTSEngine(str, Enum):
    """TTS引擎类型"""
    EDGE = "edge"           # EdgeTTS (微软)



class TTSManager:
    """
    TTS管理器
    统一管理所有TTS引擎，提供统一的接口
    """
    
    # 可用的语音列表（EdgeTTS）
    EDGE_VOICES = {
        "zh-CN-XiaoxiaoNeural": "中文女声",
        "zh-CN-YunxiNeural": "中文男声",
        "zh-CN-XiaoyiNeural": "中文女声（温柔）",
        "zh-CN-YunjianNeural": "中文男声（新闻）",
        "en-US-AriaNeural": "英文女声",
        "en-US-GuyNeural": "英文男声",
        "en-US-JennyNeural": "英文女声（助手）",
        "en-US-ChristopherNeural": "英文男声（新闻）"
    }
    
    def __init__(
        self,
        output_dir: Optional[str] = None,
        default_engine: TTSEngine = TTSEngine.EDGE
    ):
        """
        初始化TTS管理器
        
        Args:
            output_dir: 音频输出目录
            default_engine: 默认TTS引擎
        """
        self.default_engine = TTSEngine(default_engine)
        self.output_dir = Path(output_dir or "./data/tts_output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 缓存已加载的引擎
        self._engines = {}
        
        logger.info(f"TTSManager initialized with engine: {default_engine}")
    
    async def generate_audio(
        self,
        text: str,
        voice: Optional[str] = None,
        engine: Optional[TTSEngine] = None,
        rate: str = "+0%",
        volume: str = "+0%",
        output_format: str = "mp3"
    ) -> str:
        """
        生成音频文件
        
        Args:
            text: 要转换的文本
            voice: 语音名称
            engine: TTS引擎，默认使用EdgeTTS
            rate: 语速调整
            volume: 音量调整
            output_format: 输出格式
            
        Returns:
            音频文件路径
        """
        engine = TTSEngine(engine or self.default_engine)
        
        if output_format.lower() != "mp3":
            raise ValueError("Edge TTS supports MP3 output only")
        return await self._generate_edge_tts(text, voice, rate, volume, "mp3")
    
    async def generate_audio_stream(
        self,
        text: str,
        voice: Optional[str] = None,
        engine: Optional[TTSEngine] = None,
        rate: str = "+0%",
        volume: str = "+0%"
    ) -> AsyncIterator[bytes]:
        """
        生成音频流
        
        Args:
            text: 要转换的文本
            voice: 语音名称
            engine: TTS引擎
            rate: 语速调整
            volume: 音量调整
            
        Yields:
            音频数据块
        """
        engine = TTSEngine(engine or self.default_engine)
        
        async for chunk in self._stream_edge_tts(text, voice, rate, volume):
            yield chunk
    
    async def _generate_edge_tts(
        self,
        text: str,
        voice: Optional[str],
        rate: str,
        volume: str,
        output_format: str
    ) -> str:
        """使用EdgeTTS生成音频"""
        try:
            import edge_tts
        except ImportError:
            raise RuntimeError("edge-tts not installed. Install with: pip install edge-tts")
        
        # 默认语音
        voice = voice or "zh-CN-XiaoxiaoNeural"
        
        # 验证语音
        if voice not in self.EDGE_VOICES:
            logger.warning(f"Voice '{voice}' not in predefined list, using anyway")
        
        # 生成缓存键
        cache_key = self._generate_cache_key(text, voice, rate, volume)
        output_path = self.output_dir / f"{cache_key}.{output_format}"
        
        # 检查缓存
        if output_path.exists():
            logger.info(f"Audio found in cache: {output_path}")
            return str(output_path)
        
        # 生成音频
        logger.info(f"Generating audio with EdgeTTS: voice={voice}")
        
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            volume=volume
        )
        
        temporary_path = output_path.with_name(f"{output_path.stem}.{uuid.uuid4().hex}.tmp")
        try:
            await communicate.save(str(temporary_path))
            if not temporary_path.is_file() or temporary_path.stat().st_size == 0:
                raise RuntimeError("Edge TTS returned empty audio")
            temporary_path.replace(output_path)
        finally:
            temporary_path.unlink(missing_ok=True)
        
        logger.info(f"Audio generated: {output_path}")
        return str(output_path)
    
    async def _stream_edge_tts(
        self,
        text: str,
        voice: Optional[str],
        rate: str,
        volume: str
    ) -> AsyncIterator[bytes]:
        """使用EdgeTTS生成音频流"""
        try:
            import edge_tts
        except ImportError:
            raise RuntimeError("edge-tts not installed")
        
        voice = voice or "zh-CN-XiaoxiaoNeural"
        
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            volume=volume
        )
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]
    
    def _generate_cache_key(
        self,
        text: str,
        voice: str,
        rate: str,
        volume: str
    ) -> str:
        """生成缓存键"""
        key_string = json.dumps([text, voice, rate, volume], ensure_ascii=False)
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def get_available_voices(self, engine: Optional[TTSEngine] = None) -> dict:
        """获取可用语音列表"""
        engine = TTSEngine(engine or self.default_engine)
        
        if engine == TTSEngine.EDGE:
            return self.EDGE_VOICES.copy()
        else:
            return {}
    
    def clear_cache(self, older_than_days: Optional[int] = None) -> int:
        """清理缓存"""
        import time
        
        deleted_count = 0
        current_time = time.time()
        
        for file_path in self.output_dir.glob("*.mp3"):
            if file_path.is_file() and re.fullmatch(r"(?:[a-f0-9]{16}|[a-f0-9]{64})\.mp3", file_path.name):
                if older_than_days is not None:
                    file_age_days = (current_time - file_path.stat().st_mtime) / 86400
                    if file_age_days < older_than_days:
                        continue
                
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete {file_path}: {e}")
        
        logger.info(f"Cleared {deleted_count} cache files")
        return deleted_count
    
    def get_cache_size(self) -> tuple[int, int]:
        """获取缓存大小 (文件数, 总字节数)"""
        file_count = 0
        total_size = 0
        
        for file_path in self.output_dir.glob("*.mp3"):
            if file_path.is_file() and re.fullmatch(r"(?:[a-f0-9]{16}|[a-f0-9]{64})\.mp3", file_path.name):
                file_count += 1
                total_size += file_path.stat().st_size
        
        return file_count, total_size
