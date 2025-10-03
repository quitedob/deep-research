# -*- coding: utf-8 -*-
# 文件路径: D:\python_code\AgentWork\tests\check_tavily.py

"""
说明:
这是一个自动化执行脚本，用于检查 Tavily API 的核心功能, 包括 Search, Extract, Crawl, 和 Map。
它会从项目根目录的 .env 文件加载 TAVILY_API_KEY。

执行流程:
1. 加载 .env 文件中的配置并验证 API 密钥。
2. 调用 Tavily Search API。
3. 调用 Tavily Extract API。
4. 调用 Tavily Crawl API (BETA)。
5. 调用 Tavily Map API (BETA)。
"""
import os
import asyncio
import httpx
from dotenv import load_dotenv

# --- 全局配置 ---
# 加载项目根目录下的 .env 文件
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Tavily API 配置
TAVILY_API_BASE_URL = "https://api.tavily.com"


async def run_tavily_search_check(client: httpx.AsyncClient):
    """检查 Tavily 的搜索功能。"""
    print("\n-----------------------------------------")
    print("---      开始检查 Tavily Search API     ---")
    print("-----------------------------------------\n")
    try:
        payload = {"query": "广州二次元集中地是什么？如何看待当今中国二次元经济和文化？", "include_answer": True, "search_depth": "basic"}
        print(f"🔍 搜索查询: {payload['query']}\n")
        response = await client.post(f"{TAVILY_API_BASE_URL}/search", json=payload)
        response.raise_for_status()
        data = response.json()
        print(f"✅ [Search] AI 生成的答案:\n{data.get('answer', 'N/A')}\n")
        print("✅ [Search] 搜索到的部分结果:")
        for i, result in enumerate(data.get("results", [])[:2]):
            print(f"  - 结果 {i + 1}: {result.get('title')}\n    链接: {result.get('url')}")
    except Exception as e:
        print(f"❌ 错误: [Search] 检查过程中发生错误: {e}")


async def run_tavily_extract_check(client: httpx.AsyncClient):
    """检查 Tavily 的内容提取功能。"""
    print("\n-----------------------------------------")
    print("---     开始检查 Tavily Extract API     ---")
    print("-----------------------------------------\n")
    try:
        payload = {"urls": ["https://zh.wikipedia.org/wiki/%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD"]}
        print(f"🔍 待提取内容的 URL:\n - {payload['urls'][0]}\n")
        response = await client.post(f"{TAVILY_API_BASE_URL}/extract", json=payload)
        response.raise_for_status()
        data = response.json()
        print("✅ [Extract] 内容提取成功:")
        for result in data.get("results", []):
            full_content = result.get('content', '未能提取到有效内容。')
            print(f"  - 从 {result.get('url')} 提取的完整内容:\n\n{full_content}\n")
    except Exception as e:
        print(f"❌ 错误: [Extract] 检查过程中发生错误: {e}")


async def run_tavily_crawl_check(client: httpx.AsyncClient):
    """【新增】检查 Tavily 的网站爬取功能 (Crawl API)。"""
    print("\n-----------------------------------------")
    print("---  开始检查 Tavily Crawl API (BETA)   ---")
    print("-----------------------------------------\n")
    try:
        # 为了快速测试，我们设置一个较小的限制
        payload = {"url": "https://docs.tavily.com/welcome", "limit": 3}
        print(f"🔍 爬取根 URL: {payload['url']} (限制最多 {payload['limit']} 个页面)\n")

        response = await client.post(f"{TAVILY_API_BASE_URL}/crawl", json=payload)
        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])
        if results:
            print(f"✅ [Crawl] 网站爬取成功，共返回 {len(results)} 个页面结果:")
            for i, result in enumerate(results):
                content_preview = result.get('raw_content', '')[:200].replace('\n', ' ')
                print(f"  - 页面 {i + 1}: {result.get('url')}")
                print(f"    内容预览: {content_preview}...")
        else:
            print("⚠️ [Crawl] 未爬取到任何页面。")

    except Exception as e:
        print(f"❌ 错误: [Crawl] 检查过程中发生错误: {e}")


async def run_tavily_map_check(client: httpx.AsyncClient):
    """【新增】检查 Tavily 的站点地图功能 (Map API)。"""
    print("\n-----------------------------------------")
    print("---   开始检查 Tavily Map API (BETA)    ---")
    print("-----------------------------------------\n")
    try:
        # 同样设置限制以快速完成
        payload = {"url": "https://docs.tavily.com/welcome", "limit": 10}
        print(f"🔍 生成站点地图的根 URL: {payload['url']} (限制最多 {payload['limit']} 个链接)\n")

        response = await client.post(f"{TAVILY_API_BASE_URL}/map", json=payload)
        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])
        if results:
            print(f"✅ [Map] 站点地图生成成功，发现 {len(results)} 个链接:")
            for url in results:
                print(f"  - {url}")
        else:
            print("⚠️ [Map] 未发现任何链接。")

    except Exception as e:
        print(f"❌ 错误: [Map] 检查过程中发生错误: {e}")


async def main():
    """主函数，按顺序执行所有检查任务。"""
    print("=========================================")
    print("===         开始检查 Tavily API         ===")
    print("=========================================\n")

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("❌ 错误: 未在 .env 文件中找到 'TAVILY_API_KEY'。")
        print("   请在 D:\\python_code\\AgentWork\\.env 文件中进行配置。\n")
        return

    print(f"🔑 调试信息: 已从 .env 文件读取到 TAVILY_API_KEY，开头为: {api_key[:7]}...\n")

    headers = {"Authorization": f"Bearer {api_key}"}

    # 将超时时间延长，因为 Crawl 和 Map 可能耗时较长
    async with httpx.AsyncClient(headers=headers, timeout=120.0) as client:
        await run_tavily_search_check(client)
        await run_tavily_extract_check(client)
        await run_tavily_crawl_check(client)  # <-- 调用新增的 Crawl 检查
        await run_tavily_map_check(client)  # <-- 调用新增的 Map 检查

    print("\n=========================================")
    print("===        Tavily API 检查完成        ===")
    print("=========================================\n")


if __name__ == "__main__":
    asyncio.run(main())