# -*- coding: utf-8 -*-
"""
图像服务

实现image_query到image_url的转换，支持多种图像源。
"""

import logging
import hashlib
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ImageService:
    """图像服务类"""

    def __init__(self):
        """初始化图像服务"""
        self.cache_dir = Path("./data/image_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache: Dict[str, str] = {}

    async def get_image_url(
        self,
        image_query: str,
        preferred_source: str = "placeholder"
    ) -> Optional[str]:
        """
        根据查询获取图像URL

        参数:
            image_query: 图像查询描述
            preferred_source: 优先图像源（placeholder/unsplash/pexels）

        返回:
            图像URL或None
        """
        # 检查缓存
        cache_key = self._get_cache_key(image_query)
        if cache_key in self.cache:
            logger.info(f"从缓存获取图像: {image_query[:50]}")
            return self.cache[cache_key]

        try:
            if preferred_source == "placeholder":
                url = self._get_placeholder_image(image_query)
            elif preferred_source == "unsplash":
                url = await self._search_unsplash(image_query)
            elif preferred_source == "pexels":
                url = await self._search_pexels(image_query)
            else:
                url = self._get_placeholder_image(image_query)

            # 缓存结果
            if url:
                self.cache[cache_key] = url

            return url

        except Exception as e:
            logger.error(f"获取图像失败: {str(e)}")
            return self._get_placeholder_image(image_query)

    def _get_cache_key(self, query: str) -> str:
        """生成缓存键"""
        return hashlib.md5(query.encode()).hexdigest()

    def _get_placeholder_image(self, query: str) -> str:
        """
        获取占位符图像URL

        参数:
            query: 查询文本

        返回:
            占位符图像URL
        """
        # 使用placeholder.com或类似服务
        # 这里使用简单的灰色占位符
        width = 800
        height = 600
        text = query[:30].replace(" ", "+")
        return f"https://via.placeholder.com/{width}x{height}/CCCCCC/666666?text={text}"

    async def _search_unsplash(self, query: str) -> Optional[str]:
        """
        从Unsplash搜索图像

        参数:
            query: 搜索查询

        返回:
            图像URL或None
        """
        # TODO: 实现Unsplash API集成
        # 需要UNSPLASH_ACCESS_KEY环境变量
        logger.info(f"Unsplash搜索暂未实现: {query}")
        return None

    async def _search_pexels(self, query: str) -> Optional[str]:
        """
        从Pexels搜索图像

        参数:
            query: 搜索查询

        返回:
            图像URL或None
        """
        # TODO: 实现Pexels API集成
        # 需要PEXELS_API_KEY环境变量
        logger.info(f"Pexels搜索暂未实现: {query}")
        return None

    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        logger.info("图像缓存已清空")


# 全局实例
_image_service: Optional[ImageService] = None


def get_image_service() -> ImageService:
    """获取图像服务实例（单例模式）"""
    global _image_service
    if _image_service is None:
        _image_service = ImageService()
    return _image_service
