#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MediaWiki 页面内容获取器
专门用于获取维基百科页面的纯文本内容
"""

import aiohttp
import asyncio
from typing import Optional, Dict, Any
from urllib.parse import urlencode

# 只有在作为测试文件运行时才导入pytest
try:
    import pytest
except ImportError:
    pytest = None


class WikiPageContentFetcher:
    """维基百科页面内容获取器"""

    def __init__(self, lang: str = "en"):
        """
        初始化内容获取器

        Args:
            lang: 维基百科语言代码，默认英文 'en'
        """
        self.base_url = f"https://{lang}.wikipedia.org/w/api.php"
        self.session: Optional[aiohttp.ClientSession] = None
        # 设置User-Agent头，避免403错误
        self.headers = {
            'User-Agent': 'WikiContentFetcher/1.0 (https://github.com/deep-research; contact@example.com)'
        }

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    async def _make_request(self, params: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """发送API请求到MediaWiki，包含重试逻辑"""
        if not self.session:
            raise RuntimeError("Session未初始化，请使用async context manager")

        # 设置默认参数
        default_params = {
            'format': 'json',
            'formatversion': '2'
        }
        params.update(default_params)

        url = f"{self.base_url}?{urlencode(params)}"

        for attempt in range(max_retries):
            try:
                async with self.session.get(url, headers=self.headers) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientResponseError as e:
                if e.status == 429:  # 请求过于频繁
                    wait_time = 2 ** attempt
                    print(f"请求过于频繁，等待 {wait_time} 秒后重试...")
                    await asyncio.sleep(wait_time)
                    continue
                elif e.status == 403:
                    raise Exception(f"API访问被拒绝: {e}")
                else:
                    raise Exception(f"API请求失败 (HTTP {e.status}): {e}")
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"网络错误，等待 {wait_time} 秒后重试...")
                    await asyncio.sleep(wait_time)
                    continue
                raise Exception(f"请求失败: {e}")

        raise Exception("达到最大重试次数")

    async def get_page_content(self, page_title: str) -> Optional[str]:
        """
        获取页面的纯文本内容

        Args:
            page_title: 页面标题

        Returns:
            页面纯文本内容，如果页面不存在返回None
        """
        params = {
            'action': 'query',
            'titles': page_title,
            'prop': 'extracts',  # 获取页面摘要/内容
            'explaintext': 'true',  # 以纯文本格式返回
            'exsectionformat': 'plain'  # 章节格式为纯文本
        }

        result = await self._make_request(params)

        if 'query' not in result or 'pages' not in result['query']:
            return None

        pages = result['query']['pages']
        if not pages:
            return None

        # 获取第一个页面 (pages可能是列表或字典)
        if isinstance(pages, list):
            page = pages[0] if pages else None
            page_id = page.get('pageid', '-1') if page else '-1'
        else:
            # pages是字典的情况
            page_id = list(pages.keys())[0]
            page = pages[page_id]

        # 检查页面是否存在
        if page_id == '-1' or 'missing' in page:
            return None

        # 返回页面内容
        return page.get('extract', '')

    async def get_page_content_detailed(self, page_title: str) -> Optional[Dict[str, Any]]:
        """
        获取页面的详细信息，包括内容、元数据等

        Args:
            page_title: 页面标题

        Returns:
            包含页面详细信息的字典
        """
        params = {
            'action': 'query',
            'titles': page_title,
            'prop': 'extracts|info|categories|links',
            'inprop': 'url|length|displaytitle|watchers',
            'explaintext': 'true',
            'cllimit': '20',  # 分类数量限制
            'pllimit': '20'   # 链接数量限制
        }

        result = await self._make_request(params)

        if 'query' not in result or 'pages' not in result['query']:
            return None

        pages = result['query']['pages']
        if not pages:
            return None

        # 获取第一个页面 (pages可能是列表或字典)
        if isinstance(pages, list):
            page = pages[0] if pages else None
            page_id = page.get('pageid', '-1') if page else '-1'
        else:
            # pages是字典的情况
            page_id = list(pages.keys())[0]
            page = pages[page_id]

        if page_id == '-1' or 'missing' in page:
            return None

        return {
            'title': page.get('title', ''),
            'content': page.get('extract', ''),
            'url': page.get('fullurl', ''),
            'length': page.get('length', 0),
            'categories': [cat['title'] for cat in page.get('categories', [])],
            'links': [link['title'] for link in page.get('links', [])] if 'links' in page else []
        }


def create_test_function():
    """创建测试函数"""
    async def test_wiki_content_fetcher():
        """测试维基百科页面内容获取功能"""
        async with WikiPageContentFetcher() as fetcher:

            # 测试1: 获取简单页面内容
            content = await fetcher.get_page_content("Python (programming language)")
            assert content is not None, "应该能够获取Python页面内容"
            assert len(content) > 100, "页面内容应该足够长"
            print(f"✅ 获取Python页面内容成功 - 长度: {len(content)} 字符")

            # 在请求之间添加延时
            await asyncio.sleep(1)

            # 测试2: 获取详细信息
            details = await fetcher.get_page_content_detailed("Artificial intelligence")
            assert details is not None, "应该能够获取AI页面详细信息"
            assert 'title' in details, "应该包含标题"
            assert 'content' in details, "应该包含内容"
            assert 'categories' in details, "应该包含分类"
            print(f"✅ 获取AI页面详细信息成功 - 标题: {details['title']}, 分类数: {len(details['categories'])}")

            # 在请求之间添加延时
            await asyncio.sleep(1)

            # 测试3: 测试不存在的页面
            nonexistent = await fetcher.get_page_content("ThisPageDoesNotExist12345")
            assert nonexistent is None, "不存在的页面应该返回None"
            print("✅ 不存在页面测试成功 - 正确返回None")

            print("\n" + "="*60)
            print("维基百科页面内容获取器测试完成！")
            print("="*60)
            print("功能特点:")
            print("- 自动处理速率限制和重试")
            print("- 支持多语言维基百科")
            print("- 提供纯文本和详细信息两种模式")
            print("- 优雅处理不存在的页面")
            print("="*60)

            return {
                'python_content': content[:200] + "...",  # 只返回前200字符作为示例
                'ai_details': details,
                'nonexistent_result': nonexistent
            }

    # 如果有pytest，使用装饰器
    if pytest:
        test_wiki_content_fetcher = pytest.mark.asyncio(test_wiki_content_fetcher)

    return test_wiki_content_fetcher

# 创建测试函数
test_wiki_content_fetcher = create_test_function()


async def demo_page_fetching():
    """演示页面内容获取功能"""
    print(">>> 维基百科页面内容获取器演示")
    print("="*50)

    async with WikiPageContentFetcher() as fetcher:
        # 示例1: 获取Python页面的纯文本内容
        print("[BOOK] 获取Python编程语言页面的内容...")
        content = await fetcher.get_page_content("Python (programming language)")
        if content:
            print(f"[OK] 成功获取内容 (长度: {len(content)} 字符)")
            print("内容预览 (前500字符):")
            print("-" * 30)
            print(content[:500] + "..." if len(content) > 500 else content)
            print("-" * 30)

        await asyncio.sleep(1)  # 避免请求过于频繁

        # 示例2: 获取详细信息
        print("\n[SEARCH] 获取人工智能页面的详细信息...")
        details = await fetcher.get_page_content_detailed("Artificial intelligence")
        if details:
            print(f"[OK] 成功获取详细信息")
            print(f"标题: {details['title']}")
            print(f"URL: {details['url']}")
            print(f"内容长度: {len(details['content'])} 字符")
            print(f"分类数量: {len(details['categories'])}")
            print(f"链接数量: {len(details['links'])}")

            print("前5个分类:")
            for cat in details['categories'][:5]:
                print(f"  - {cat}")

            print("前5个链接:")
            for link in details['links'][:5]:
                print(f"  - {link}")

    print("\n>>> 演示完成！")


if __name__ == "__main__":
    """直接运行演示"""
    asyncio.run(demo_page_fetching())
