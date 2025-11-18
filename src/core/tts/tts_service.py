# -*- coding: utf-8 -*-
"""
TTS服务 - 向后兼容的服务层
TTS Service - Backward compatible service layer

这是对TTSManager的简单封装，保持向后兼容
"""

from typing import Optional, AsyncIterator
from pathlib import Path

from .tts_manager import TTSManager, TTSEngine
from ...config.logging.logging import get_logger
logger = get_logger("tts_service")


class TTSService:
    """
    TTS服务（向后兼容）
    封装TTSManager，提供简单的接口
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        初始化TTS服务
        
        Args:
            output_dir: 音频输出目录
        """
        self.manager = TTSManager(output_dir=output_dir)
        self.output_dir = self.manager.output_dir
    
    async def generate_audio(
        self,
        text: str,
        voice: str = "zh-CN-XiaoxiaoNeural",
        output_format: str = "mp3",
        rate: str = "+0%",
        volume: str = "+0%"
    ) -> str:
        """
        生成音频文件
        
        Args:
            text: 要转换的文本
            voice: 语音名称
            output_format: 输出格式
            rate: 语速调整
            volume: 音量调整
            
        Returns:
            音频文件路径
        """
        return await self.manager.generate_audio(
            text=text,
            voice=voice,
            rate=rate,
            volume=volume,
            output_format=output_format
        )
    
    async def generate_audio_stream(
        self,
        text: str,
        voice: str = "zh-CN-XiaoxiaoNeural",
        rate: str = "+0%",
        volume: str = "+0%"
    ) -> AsyncIterator[bytes]:
        """
        生成音频流
        
        Args:
            text: 要转换的文本
            voice: 语音名称
            rate: 语速调整
            volume: 音量调整
            
        Yields:
            音频数据块
        """
        async for chunk in self.manager.generate_audio_stream(
            text=text,
            voice=voice,
            rate=rate,
            volume=volume
        ):
            yield chunk
    
    def get_available_voices(self) -> dict:
        """获取可用语音列表"""
        return self.manager.get_available_voices()
    
    def clear_cache(self, older_than_days: Optional[int] = None) -> int:
        """清理缓存"""
        return self.manager.clear_cache(older_than_days)
    
    def get_cache_size(self) -> tuple[int, int]:
        """获取缓存大小"""
        return self.manager.get_cache_size()
    
    def _generate_cache_key(self, text: str, voice: str, rate: str, volume: str) -> str:
        """生成缓存键（向后兼容）"""
        return self.manager._generate_cache_key(text, voice, rate, volume)
    
    # 属性别名（向后兼容）
    @property
    def AVAILABLE_VOICES(self):
        """可用语音列表（向后兼容）"""
        return self.manager.EDGE_VOICES
