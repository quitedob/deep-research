"""The research web search adapter uses the provider's supported async HTTP API."""
import os
import pytest
from backend.core.agentscope.tools.web_search_tool import WebSearchTool


@pytest.mark.live
async def test_research_web_search_returns_sources():
    key = os.getenv("WEB_SEARCH_API_KEY") or os.getenv("BIGMODEL_API_KEY")
    assert key, "Configure a provider search key before running live checks"
    tool = WebSearchTool(key)
    try:
        result = await tool.web_search("Python official documentation", max_results=2)
        assert result.content
        assert result.metadata.get("sources")
    finally:
        await tool.close()
