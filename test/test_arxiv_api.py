#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arXiv API 测试工具
用于测试和演示arXiv预印本检索API的功能
"""

import aiohttp
import asyncio
from typing import Optional, Dict, Any, List
from urllib.parse import urlencode, quote
import xml.etree.ElementTree as ET
import time

# 只有在作为测试文件运行时才导入pytest
try:
    import pytest
except ImportError:
    pytest = None


class ArXivAPIFetcher:
    """
    arXiv API 检索器

    注意：此实现为测试环境禁用SSL验证。
    在生产环境中，请移除verify_ssl=False并确保系统SSL证书正确配置。
    """

    def __init__(self):
        """初始化arXiv API检索器"""
        self.base_url = "http://export.arxiv.org/api/query"
        self.session: Optional[aiohttp.ClientSession] = None
        # 设置User-Agent头
        self.headers = {
            'User-Agent': 'ArXivFetcher/1.0 (https://github.com/deep-research; contact@example.com)'
        }

    async def __aenter__(self):
        """异步上下文管理器入口"""
        # 创建SSL连接器，禁用证书验证（仅用于测试环境）
        connector = aiohttp.TCPConnector(verify_ssl=False)
        self.session = aiohttp.ClientSession(connector=connector)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    async def _make_request(self, params: Dict[str, Any], max_retries: int = 3) -> str:
        """发送API请求，包含重试逻辑"""
        if not self.session:
            raise RuntimeError("Session未初始化，请使用async context manager")

        url = f"{self.base_url}?{urlencode(params)}"

        for attempt in range(max_retries):
            try:
                async with self.session.get(url, headers=self.headers) as response:
                    response.raise_for_status()
                    return await response.text()
            except aiohttp.ClientResponseError as e:
                if e.status == 429:  # 请求过于频繁
                    wait_time = 2 ** attempt
                    print(f"请求过于频繁，等待 {wait_time} 秒后重试...")
                    await asyncio.sleep(wait_time)
                    continue
                elif e.status == 500:  # 服务器错误
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        print(f"服务器错误，等待 {wait_time} 秒后重试...")
                        await asyncio.sleep(wait_time)
                        continue
                raise Exception(f"API请求失败 (HTTP {e.status}): {e}")
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"网络错误，等待 {wait_time} 秒后重试...")
                    await asyncio.sleep(wait_time)
                    continue
                raise Exception(f"请求失败: {e}")

        raise Exception("达到最大重试次数")

    def _parse_atom_response(self, xml_content: str) -> Dict[str, Any]:
        """解析Atom XML响应"""
        try:
            # 定义命名空间
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom',
                'opensearch': 'http://a9.com/-/spec/opensearch/1.1/'
            }

            root = ET.fromstring(xml_content)

            # 解析基本信息
            result = {
                'total_results': 0,
                'start_index': 0,
                'items_per_page': 0,
                'papers': []
            }

            # 获取总数等信息
            total_elem = root.find('.//opensearch:totalResults', namespaces)
            if total_elem is not None:
                result['total_results'] = int(total_elem.text)

            start_elem = root.find('.//opensearch:startIndex', namespaces)
            if start_elem is not None:
                result['start_index'] = int(start_elem.text)

            items_elem = root.find('.//opensearch:itemsPerPage', namespaces)
            if items_elem is not None:
                result['items_per_page'] = int(items_elem.text)

            # 解析论文条目
            for entry in root.findall('.//atom:entry', namespaces):
                paper = self._parse_paper_entry(entry, namespaces)
                if paper:
                    result['papers'].append(paper)

            return result

        except ET.ParseError as e:
            raise Exception(f"XML解析错误: {e}")
        except Exception as e:
            raise Exception(f"响应解析错误: {e}")

    def _parse_paper_entry(self, entry, namespaces) -> Optional[Dict[str, Any]]:
        """解析单个论文条目"""
        try:
            paper = {}

            # 基本信息
            id_elem = entry.find('atom:id', namespaces)
            if id_elem is not None:
                paper['id'] = id_elem.text.replace('http://arxiv.org/abs/', '')

            title_elem = entry.find('atom:title', namespaces)
            if title_elem is not None:
                paper['title'] = title_elem.text.strip()

            summary_elem = entry.find('atom:summary', namespaces)
            if summary_elem is not None:
                paper['summary'] = summary_elem.text.strip()

            # 发布时间
            published_elem = entry.find('atom:published', namespaces)
            if published_elem is not None:
                paper['published'] = published_elem.text

            updated_elem = entry.find('atom:updated', namespaces)
            if updated_elem is not None:
                paper['updated'] = updated_elem.text

            # 作者
            authors = []
            for author_elem in entry.findall('atom:author', namespaces):
                name_elem = author_elem.find('atom:name', namespaces)
                if name_elem is not None:
                    authors.append(name_elem.text)
            paper['authors'] = authors

            # arXiv特定信息
            comment_elem = entry.find('arxiv:comment', namespaces)
            if comment_elem is not None:
                paper['comment'] = comment_elem.text

            journal_elem = entry.find('arxiv:journal_ref', namespaces)
            if journal_elem is not None:
                paper['journal_ref'] = journal_elem.text

            # 分类
            categories = []
            for cat_elem in entry.findall('atom:category', namespaces):
                term = cat_elem.get('term')
                if term:
                    categories.append(term)
            paper['categories'] = categories

            # 主要分类
            primary_cat_elem = entry.find('arxiv:primary_category', namespaces)
            if primary_cat_elem is not None:
                paper['primary_category'] = primary_cat_elem.get('term')

            # 链接
            links = {}
            for link_elem in entry.findall('atom:link', namespaces):
                rel = link_elem.get('rel')
                href = link_elem.get('href')
                title = link_elem.get('title')
                if rel and href:
                    links[rel] = {
                        'href': href,
                        'title': title
                    }
            paper['links'] = links

            return paper

        except Exception as e:
            print(f"解析论文条目时出错: {e}")
            return None

    async def search_papers(self,
                           query: str,
                           start: int = 0,
                           max_results: int = 10,
                           sort_by: str = "relevance",
                           sort_order: str = "descending") -> Dict[str, Any]:
        """
        搜索论文

        Args:
            query: 搜索查询 (例如: "all:electron", "cat:cs.AI", "au:Smith")
            start: 起始位置 (从0开始)
            max_results: 最大结果数量 (最大10000)
            sort_by: 排序方式 ("relevance", "lastUpdatedDate", "submittedDate")
            sort_order: 排序顺序 ("ascending", "descending")

        Returns:
            包含搜索结果的字典
        """
        params = {
            'search_query': query,
            'start': str(start),
            'max_results': str(min(max_results, 100)),  # API限制每次最多100个结果
            'sortBy': sort_by,
            'sortOrder': sort_order
        }

        xml_response = await self._make_request(params)
        return self._parse_atom_response(xml_response)

    async def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        通过ID获取论文信息

        Args:
            paper_id: 论文ID (例如: "hep-ex/0307015" 或 "0307015")

        Returns:
            论文详细信息
        """
        params = {
            'id_list': paper_id,
            'max_results': '1'
        }

        xml_response = await self._make_request(params)
        result = self._parse_atom_response(xml_response)

        if result['papers']:
            return result['papers'][0]
        return None

    async def search_by_category(self,
                                category: str,
                                start: int = 0,
                                max_results: int = 10) -> Dict[str, Any]:
        """
        按分类搜索论文

        Args:
            category: arXiv分类 (例如: "cs.AI", "physics.optics")
            start: 起始位置
            max_results: 最大结果数量

        Returns:
            搜索结果
        """
        query = f"cat:{category}"
        return await self.search_papers(query, start, max_results)

    async def search_by_author(self,
                              author: str,
                              start: int = 0,
                              max_results: int = 10) -> Dict[str, Any]:
        """
        按作者搜索论文

        Args:
            author: 作者姓名
            start: 起始位置
            max_results: 最大结果数量

        Returns:
            搜索结果
        """
        query = f"au:{author}"
        return await self.search_papers(query, start, max_results)


def create_test_function():
    """创建测试函数"""
    async def test_arxiv_api():
        """测试arXiv API功能"""
        async with ArXivAPIFetcher() as fetcher:

            # 测试1: 基本搜索
            print(">>> 测试1: 搜索'quantum computing'相关论文")
            results = await fetcher.search_papers("all:quantum computing", max_results=3)
            print(f"[OK] 找到 {results['total_results']} 个结果，返回 {len(results['papers'])} 个")

            if results['papers']:
                paper = results['papers'][0]
                print(f"第一篇论文:")
                print(f"  标题: {paper['title']}")
                print(f"  作者: {', '.join(paper['authors'][:3])}")
                print(f"  摘要: {paper['summary'][:200]}...")

            await asyncio.sleep(1)

            # 测试2: 按分类搜索
            print("\n>>> 测试2: 搜索计算机科学AI分类的论文")
            cs_results = await fetcher.search_by_category("cs.AI", max_results=2)
            print(f"[OK] AI分类找到 {cs_results['total_results']} 个结果，返回 {len(cs_results['papers'])} 个")

            if cs_results['papers']:
                paper = cs_results['papers'][0]
                print(f"AI论文示例:")
                print(f"  ID: {paper['id']}")
                print(f"  标题: {paper['title'][:100]}...")

            await asyncio.sleep(1)

            # 测试3: 通过ID获取论文
            print("\n>>> 测试3: 通过ID获取特定论文")
            if results['papers']:
                paper_id = results['papers'][0]['id']
                paper_detail = await fetcher.get_paper_by_id(paper_id)
                if paper_detail:
                    print(f"[OK] 成功获取论文详情")
                    print(f"  分类: {paper_detail.get('primary_category', 'N/A')}")
                    print(f"  发布时间: {paper_detail.get('published', 'N/A')}")
                    if 'links' in paper_detail and 'alternate' in paper_detail['links']:
                        print(f"  链接: {paper_detail['links']['alternate']['href']}")
                else:
                    print("[ERROR] 获取论文详情失败")
            else:
                print("[SKIP] 没有可用的论文ID进行测试")

            await asyncio.sleep(1)

            # 测试4: 按作者搜索
            print("\n>>> 测试4: 搜索特定作者的论文")
            author_results = await fetcher.search_by_author("Turing", max_results=2)
            print(f"[OK] 作者搜索找到 {author_results['total_results']} 个结果")

            print("\n" + "="*70)
            print("arXiv API测试完成！")
            print("="*70)
            print("功能特点:")
            print("- 支持多种搜索方式（关键词、分类、作者、ID）")
            print("- 自动处理API限制和重试")
            print("- 解析Atom XML响应为结构化数据")
            print("- 支持分页查询")
            print("="*70)

            return {
                'search_results': results,
                'category_results': cs_results,
                'author_results': author_results
            }

    # 如果有pytest，使用装饰器
    if pytest:
        test_arxiv_api = pytest.mark.asyncio(test_arxiv_api)

    return test_arxiv_api

# 创建测试函数
test_arxiv_api = create_test_function()


async def demo_arxiv_api():
    """演示arXiv API功能"""
    print(">>> arXiv API 演示")
    print("="*50)

    async with ArXivAPIFetcher() as fetcher:
        # 示例1: 搜索机器学习论文
        print("[SEARCH] 搜索机器学习相关论文...")
        ml_results = await fetcher.search_papers("all:machine learning", max_results=5)
        if ml_results['papers']:
            print(f"[OK] 找到 {ml_results['total_results']} 篇相关论文")
            print("最新5篇论文:")

            for i, paper in enumerate(ml_results['papers'], 1):
                print(f"{i}. {paper['title'][:80]}...")
                print(f"   作者: {', '.join(paper['authors'][:2])}")
                print(f"   分类: {paper.get('primary_category', 'N/A')}")
                print(f"   发布时间: {paper.get('published', 'N/A')[:10]}")
                print()

        await asyncio.sleep(1)

        # 示例2: 搜索特定领域
        print("[SEARCH] 搜索量子物理论文...")
        quantum_results = await fetcher.search_by_category("quant-ph", max_results=3)
        if quantum_results['papers']:
            print(f"[OK] 量子物理分类找到 {len(quantum_results['papers'])} 篇论文")
            for paper in quantum_results['papers'][:2]:
                print(f"- {paper['title'][:60]}...")
                print(f"  ID: {paper['id']}")

        await asyncio.sleep(1)

        # 示例3: 获取论文完整信息
        if ml_results['papers']:
            paper_id = ml_results['papers'][0]['id']
            print(f"\n[DETAIL] 获取论文 {paper_id} 的详细信息...")
            paper_detail = await fetcher.get_paper_by_id(paper_id)
            if paper_detail:
                print("[OK] 论文详情获取成功")
                print(f"标题: {paper_detail['title']}")
                print(f"作者: {', '.join(paper_detail['authors'])}")
                print(f"摘要长度: {len(paper_detail['summary'])} 字符")
                if 'journal_ref' in paper_detail:
                    print(f"期刊: {paper_detail['journal_ref']}")
                print(f"所有分类: {', '.join(paper_detail['categories'])}")

    print("\n>>> 演示完成！")


if __name__ == "__main__":
    """直接运行演示"""
    asyncio.run(demo_arxiv_api())
