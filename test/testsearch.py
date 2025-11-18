"""
使用官方 MCP Python SDK 调用 BigModel 搜索服务
需要安装: pip install mcp httpx
"""

import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client  # ← 修正：去掉下划线

async def test_with_mcp_sdk():
    """使用官方 MCP SDK 测试"""

    API_KEY = "f4799605de6d45cca97bafd25e1abfdf.rpo5rizn684an7Ym"  # 替换为您的实际 API Key
    MCP_URL = "https://open.bigmodel.cn/api/mcp/web_search_prime/mcp"

    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    print("=" * 60)
    print("使用官方 MCP SDK 测试 BigModel Web Search Prime")
    print("=" * 60)
    
    try:
        # ← 修正：使用 streamablehttp_client（没有下划线）
        async with streamablehttp_client(MCP_URL, headers=headers) as (read, write, _):
            async with ClientSession(read, write) as session:
                # 1. 初始化连接
                print("\n1. 初始化连接...")
                await session.initialize()
                print("✓ 连接初始化成功")
                
                # 2. 列出可用工具
                print("\n2. 列出可用工具...")
                tools_result = await session.list_tools()
                print(f"可用工具数量: {len(tools_result.tools)}")
                
                for tool in tools_result.tools:
                    print(f"  - {tool.name}: {tool.description}")
                    if hasattr(tool, 'inputSchema'):
                        print(f"    参数: {tool.inputSchema}")
                
                # 3. 调用搜索工具
                if tools_result.tools:
                    print("\n3. 调用搜索工具...")
                    tool_name = tools_result.tools[0].name
                    
                    search_result = await session.call_tool(
                        name=tool_name,
                        arguments={"search_query": "Python 异步编程最佳实践"}
                    )
                    
                    print(f"\n搜索结果:")
                    for content in search_result.content:
                        if hasattr(content, 'text'):
                            print(content.text)
                
                print("\n✓ 测试完成！")
                
    except Exception as e:
        print(f"\n✗ 发生错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_with_mcp_sdk())
