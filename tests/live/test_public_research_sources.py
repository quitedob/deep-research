import pytest
from backend.core.agentscope.tools.arxiv_tool import ArXivTool
from backend.core.agentscope.tools.wikipedia_tool import WikipediaTool


@pytest.mark.live
async def test_arxiv_search_finds_a_known_subject():
    result = await ArXivTool().search_arxiv_papers("cat:cs.AI", max_results=1)
    assert result.content


@pytest.mark.live
async def test_wikipedia_search_returns_content():
    result = await WikipediaTool().search_wikipedia("Python programming language", max_results=1)
    assert result.content
