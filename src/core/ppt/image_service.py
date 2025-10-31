# -*- coding: utf-8 -*-
"""
图像服务

实现image_query到image_url的转换，支持多种图像源。
"""

import logging
import hashlib
import os
import json
from typing import Optional, Dict, Any
from pathlib import Path
import aiohttp
from urllib.parse import quote

logger = logging.getLogger(__name__)


class ImageService:
    """图像服务类"""

    def __init__(self):
        """初始化图像服务"""
        self.cache_dir = Path("./data/image_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "image_cache.json"
        self.cache: Dict[str, str] = {}
        self._load_cache()

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
                self._save_cache()

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
        access_key = os.getenv("UNSPLASH_ACCESS_KEY")
        if not access_key:
            logger.warning("UNSPLASH_ACCESS_KEY未配置，无法使用Unsplash")
            return None

        url = "https://api.unsplash.com/search/photos"
        headers = {
            "Authorization": f"Client-ID {access_key}"
        }
        params = {
            "query": query,
            "per_page": 1,
            "orientation": "landscape"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params, timeout=30) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Unsplash API错误: {response.status}, {error_text}")
                        return None

                    result = await response.json()
                    photos = result.get("results", [])

                    if photos:
                        photo = photos[0]
                        # 使用regular尺寸的图片
                        return photo["urls"]["regular"]
                    else:
                        logger.warning(f"Unsplash未找到图片: {query}")
                        return None

        except aiohttp.ClientError as e:
            logger.error(f"Unsplash网络错误: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unsplash API错误: {str(e)}")
            return None

    async def _search_pexels(self, query: str) -> Optional[str]:
        """
        从Pexels搜索图像

        参数:
            query: 搜索查询

        返回:
            图像URL或None
        """
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            logger.warning("PEXELS_API_KEY未配置，无法使用Pexels")
            return None

        url = "https://api.pexels.com/v1/search"
        headers = {
            "Authorization": api_key
        }
        params = {
            "query": query,
            "per_page": 1,
            "orientation": "landscape"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params, timeout=30) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Pexels API错误: {response.status}, {error_text}")
                        return None

                    result = await response.json()
                    photos = result.get("photos", [])

                    if photos:
                        photo = photos[0]
                        # 使用large尺寸的图片
                        return photo["src"]["large"]
                    else:
                        logger.warning(f"Pexels未找到图片: {query}")
                        return None

        except aiohttp.ClientError as e:
            logger.error(f"Pexels网络错误: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Pexels API错误: {str(e)}")
            return None

    def _load_cache(self):
        """从文件加载缓存"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cache = data.get("cache", {})
                logger.info(f"从文件加载了 {len(self.cache)} 条图像缓存")
        except Exception as e:
            logger.error(f"加载图像缓存失败: {str(e)}")
            self.cache = {}

    def _save_cache(self):
        """保存缓存到文件"""
        try:
            data = {"cache": self.cache}
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存图像缓存失败: {str(e)}")

    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
        except Exception as e:
            logger.error(f"删除缓存文件失败: {str(e)}")
        logger.info("图像缓存已清空")


# 全局实例
_image_service: Optional[ImageService] = None


def get_image_service() -> ImageService:
    """获取图像服务实例（单例模式）"""
    global _image_service
    if _image_service is None:
        _image_service = ImageService()
    return _image_service


