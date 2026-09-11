"""Regression checks for research ownership, lifecycle and provider boundaries."""
import asyncio
import json
from collections import OrderedDict
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from agentscope.message import Msg
from agentscope.formatter import OpenAIChatFormatter

from backend.config.memory_config import MemoryConfig
from backend.core.agentscope.config import ConfigManager, ToolConfig
from backend.core.agentscope.llm_adapter import AgentScopeLLMAdapter
from backend.core.agentscope.research_agent import DeepResearchAgent
from backend.core.agentscope.tools.arxiv_tool import ArXivTool
from backend.core.agentscope.tools.image_analysis_tool import ImageAnalysisTool
from backend.core.agentscope.tools.web_search_tool import WebSearchTool
from backend.core.llm.base_llm import APIError, BaseLLM
from backend.core.llm.deepseek_llm import DeepSeekLLM
from backend.core.memory.memory_manager import Mem0MemoryManager
from backend.core.agentscope.memory.research_memory import ResearchMemoryManager
from backend.schemas.chat import ChatRequest
from backend.services.chat_service import ChatService
from backend.services.web_search_service import WebSearchService
from backend.services.agentscope_research_service import AgentScopeResearchService


def run(awaitable):
    return asyncio.run(awaitable)


def research_service():
    service = AgentScopeResearchService.__new__(AgentScopeResearchService)
    service._lifecycle_lock = asyncio.Lock()
    service.active_researchers = {}
    service.session_cache = OrderedDict()
    service.report_cache = OrderedDict()
    service.cache_limit = 2
    service.max_active_sessions = 2
    service.research_dao = SimpleNamespace(
        get_research_session=AsyncMock(return_value={"id": "session", "status": "active", "user_id": "owner"}),
        update_session_status=AsyncMock(),
        save_message_to_long_term=AsyncMock(),
        search_research_content=AsyncMock(return_value=[]),
    )
    return service


def test_search_without_identity_never_queries_content():
    service = research_service()
    assert run(service.search_research_content("secret")) == []
    service.research_dao.search_research_content.assert_not_called()


def test_search_uses_authenticated_user_filter_even_without_sessions():
    service = research_service()
    assert run(service.search_research_content("secret", user_id="new-user")) == []
    service.research_dao.search_research_content.assert_awaited_once_with(query="secret", limit=20, user_id="new-user")


def test_orphaned_research_becomes_interrupted_after_restart():
    service = research_service()
    assert run(service.get_research_status("session"))["status"] == "interrupted"
    assert service.research_dao.update_session_status.await_args.args[1] == "interrupted"


def test_concurrent_completed_status_polls_are_read_only():
    async def scenario():
        service = research_service()
        service.research_dao.get_research_session.return_value["status"] = "completed"
        statuses = await asyncio.gather(*(service.get_research_status("session") for _ in range(12)))
        assert {status["status"] for status in statuses} == {"completed"}
        service.research_dao.update_session_status.assert_not_awaited()
    run(scenario())


def test_interrupt_cancels_and_waits_for_research_before_checkpoint():
    async def scenario():
        service = research_service()
        started = asyncio.Event()
        stopped = asyncio.Event()

        async def conduct(**kwargs):
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                stopped.set()

        async def export():
            assert stopped.is_set()
            return {"short_memory": []}

        researcher = SimpleNamespace(conduct_research=conduct, export_session_data=export,
                                     memory_manager=SimpleNamespace(active_sessions={}))
        service.active_researchers["session"] = researcher
        researcher._research_task = asyncio.create_task(service._run_research("session", researcher, {"query": "test"}))
        await started.wait()
        result = await service.interrupt_research("session")
        assert result["success"] and researcher._research_task.cancelled()
        assert not service.active_researchers
        assert all(call.args[1] == "interrupted" for call in service.research_dao.update_session_status.await_args_list)
    run(scenario())


def test_failed_research_is_not_marked_completed():
    async def scenario():
        service = research_service()
        researcher = SimpleNamespace(conduct_research=AsyncMock(return_value={"error": "provider failed"}),
                                     memory_manager=SimpleNamespace(active_sessions={}))
        service.active_researchers["session"] = researcher
        with pytest.raises(RuntimeError):
            await service._run_research("session", researcher, {"query": "q"})
        assert service.research_dao.update_session_status.await_args.args[1] == "failed"
        assert not service.active_researchers
    run(scenario())


def test_cache_is_bounded_without_evicting_live_task_metadata():
    service = research_service()
    service.active_researchers["live"] = object()
    for key in ("live", "old", "new"):
        service._cache(service.session_cache, key, {"id": key})
    assert list(service.session_cache) == ["live", "new"]


def test_config_loading_never_writes_and_explicit_save_omits_nested_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-secret-key")
    path = tmp_path / "settings.json"
    manager = ConfigManager(str(path))
    config = manager.load_config()
    assert config.llm.api_key == "test-secret-key"
    assert not path.exists()
    config.tools["secret"] = ToolConfig(name="secret", custom_params={"api_key": "nested-key", "enabled": True})
    manager.save_config()
    serialized = path.read_text(encoding="utf-8")
    assert "test-secret-key" not in serialized and "nested-key" not in serialized
    assert "api_key" not in serialized
    assert json.loads(serialized)["llm"]["max_tokens"] == config.llm.max_tokens


class Response:
    def __init__(self, status=200, payload=None, lines=()):
        self.status = status
        self.payload = payload or {"choices": [{"message": {"content": "ok"}}]}
        self.lines = lines
        self.content = self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def json(self):
        return self.payload

    def __aiter__(self):
        async def iterator():
            for line in self.lines:
                if isinstance(line, Exception):
                    raise line
                yield line
        return iterator()


def test_provider_retries_transient_failure_on_same_pooled_session(monkeypatch):
    import backend.core.llm.base_llm as module
    client = SimpleNamespace(closed=False, post=Mock(side_effect=[Response(503), Response()]), close=AsyncMock())
    factory = Mock(return_value=client)
    monkeypatch.setattr(module.aiohttp, "ClientSession", factory)
    llm = DeepSeekLLM(api_key="test", max_retries=1, retry_delay=0)

    async def scenario():
        assert (await llm.chat_completion([], "deepseek-flash"))["choices"]
        assert await llm._get_session() is client
        await llm.close()
    run(scenario())
    assert client.post.call_count == 2 and factory.call_count == 1
    client.close.assert_awaited_once()


def test_provider_does_not_retry_auth_failure_or_repeat_partial_stream():
    async def scenario():
        llm = DeepSeekLLM(api_key="test", max_retries=3, retry_delay=0)
        client = SimpleNamespace(closed=False, post=Mock(return_value=Response(401)))
        llm._session = client
        with pytest.raises(APIError):
            await llm.chat_completion([], "deepseek-flash")
        assert client.post.call_count == 1
        client.post = Mock(return_value=Response(lines=[b'data: {"choices":[{"delta":{"content":"partial"}}]}\n', APIError("broken")]))
        chunks = []
        with pytest.raises(APIError):
            async for chunk in llm.chat_completion_stream([], "deepseek-flash"):
                chunks.append(chunk)
        assert chunks == ["partial"] and client.post.call_count == 1
    run(scenario())


def test_formatter_adapter_preserves_tool_history_and_multimodal_blocks():
    async def scenario():
        llm = DeepSeekLLM(api_key="test", model="deepseek-flash")
        llm.chat_completion = AsyncMock(return_value={"choices": [{"message": {"content": "ok"}}]})
        adapter = AgentScopeLLMAdapter(llm, "deepseek-flash")
        messages = [
            Msg("assistant", [{"type": "tool_use", "id": "call", "name": "search", "input": {"query": "q"}}], "assistant"),
            Msg("tool", [{"type": "tool_result", "id": "call", "name": "search", "output": [{"type": "text", "text": "result"}]}], "system"),
            Msg("user", [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "YWJj"}}], "user"),
        ]
        formatted = await OpenAIChatFormatter().format(messages)
        await adapter(formatted, tools=[{"type": "function", "function": {"name": "search"}}])
        sent = llm.chat_completion.await_args.kwargs
        assert sent["messages"] == formatted
        assert any(message.get("tool_call_id") == "call" for message in sent["messages"])
        assert sent["tools"]
    run(scenario())


def test_deepseek_sends_tools_and_image_blocks_without_stringifying():
    llm = DeepSeekLLM(api_key="test")
    llm._make_request = AsyncMock(return_value={"choices": []})
    messages = [{"role": "user", "content": [{"type": "image_url", "image_url": {"url": "data:image/png;base64,YWJj"}}]}]
    run(llm.chat_completion(messages, "deepseek-flash", tools=[{"type": "function"}]))
    payload = llm._make_request.await_args.args[1]
    assert payload["messages"] == messages and payload["tools"] == [{"type": "function"}]


def test_multi_image_analysis_uses_default_vlm_and_sends_images_together(tmp_path):
    first, second = tmp_path / "first.png", tmp_path / "second.png"
    first.write_bytes(b"first-image")
    second.write_bytes(b"second-image")
    llm = SimpleNamespace(model="deepseek-flash", get_provider_name=lambda: "deepseek",
                          chat_completion=AsyncMock(return_value={"choices": [{"message": {"content": "images compared"}}]}))
    result = run(ImageAnalysisTool(llm_instance=llm).analyze_multiple_images([str(first), str(second)]))
    assert result.content[0]["text"] == "images compared"
    sent = llm.chat_completion.await_args.kwargs
    assert sent["model"] == "deepseek-flash"
    assert len(sent["messages"][0]["content"]) == 3


def test_web_search_uses_each_request_key_and_propagates_provider_errors(monkeypatch):
    monkeypatch.setenv("BIGMODEL_API_KEY", "environment-key")
    first, second = WebSearchTool("first-key"), WebSearchTool("second-key")
    assert first._llm.api_key == "first-key" and second._llm.api_key == "second-key"
    first._llm.web_search = AsyncMock(side_effect=APIError("unavailable"))
    with pytest.raises(APIError):
        run(first.web_search("q"))


def test_search_query_prompt_executes_model_and_validates_json():
    service = WebSearchService()
    model = SimpleNamespace(chat_completion=AsyncMock(return_value={"choices": [{"message": {"content": '{"queries":["one","two","three","four","five"]}'}}]}))
    service._get_llm = Mock(return_value=model)
    assert run(service.generate_search_queries("question")) == ["one", "two", "three", "four", "five"]
    model.chat_completion.assert_awaited_once()


def test_failed_web_chat_never_persists_an_assistant_message():
    service = ChatService.__new__(ChatService)
    service.chat_dao = SimpleNamespace(add_message=AsyncMock(return_value=1))
    service.prepare_chat = AsyncMock(return_value={"llm_provider": "deepseek", "model_name": "deepseek-flash"})
    service.web_search_service = SimpleNamespace(web_search_chat=AsyncMock(side_effect=APIError("failed")))
    with pytest.raises(APIError):
        run(service.web_search_chat(ChatRequest(session_id="session", message="q")))
    assert [call.kwargs["role"] for call in service.chat_dao.add_message.await_args_list] == ["user"]


def test_stream_error_propagates_without_persisting_partial_assistant():
    async def scenario():
        service = ChatService.__new__(ChatService)
        service.prepare_chat = AsyncMock(return_value={"llm_provider": "deepseek", "model_name": "deepseek-flash"})
        service.chat_dao = SimpleNamespace(add_message=AsyncMock(return_value=1), get_recent_messages=AsyncMock(return_value=[]))

        async def streaming(**kwargs):
            yield "partial"
            raise APIError("failed")

        service._get_llm_instance = Mock(return_value=SimpleNamespace(chat_completion_stream=streaming))
        chunks = []
        with pytest.raises(APIError):
            async for chunk in service.chat_stream(ChatRequest(session_id="session", message="q")):
                chunks.append(chunk)
        assert "partial" in chunks[0]
        assert [call.kwargs["role"] for call in service.chat_dao.add_message.await_args_list] == ["user"]
    run(scenario())


def test_research_memory_creation_does_not_overwrite_owner():
    dao = SimpleNamespace(get_research_session=AsyncMock(return_value={"user_id": "owner"}),
                          get_long_term_memory=AsyncMock(return_value=[{"message_role": "user", "message_name": "user", "message_content": "saved context"}]),
                          create_research_session=AsyncMock())
    manager = ResearchMemoryManager(dao)
    async def scenario():
        one, two = await asyncio.gather(manager.create_session("session"), manager.create_session("session"))
        assert one is two and (await one.get_memory())[0].content == "saved context"
    run(scenario())
    dao.create_research_session.assert_not_called()


def test_memory_cache_covers_query_options_and_invalidates_generation(monkeypatch):
    import backend.core.memory.memory_manager as module
    values = {}

    async def get(key):
        return values.get(key)

    async def set_value(key, value, **kwargs):
        values[key] = value

    async def increment(key):
        values[key] = str(int(values.get(key, 0)) + 1)

    cache = SimpleNamespace(get=get, get_json=get, set_json=AsyncMock(side_effect=set_value),
                            incr=increment, delete=AsyncMock())
    monkeypatch.setattr(module, "redis_client", cache)
    manager = Mem0MemoryManager.__new__(Mem0MemoryManager)
    manager.enabled = True
    manager.settings = MemoryConfig(query_cache_ttl=19)
    manager.hyde_retriever = SimpleNamespace(embed_query_with_hyde=AsyncMock(return_value=[1.0]))
    manager.vector_store = SimpleNamespace(search_memories=Mock(return_value=[{"content": "fact"}]))

    async def scenario():
        await manager.retrieve_memories("q", "u", top_k=1)
        await manager.retrieve_memories("q", "u", top_k=1)
        assert manager.vector_store.search_memories.call_count == 1
        await manager.retrieve_memories("q", "u", top_k=2)
        assert manager.vector_store.search_memories.call_count == 2
        await manager._invalidate_user_cache("u")
        await manager.retrieve_memories("q", "u", top_k=1)
        assert manager.vector_store.search_memories.call_count == 3
        assert all(call.kwargs["expire"] == 19 for call in cache.set_json.await_args_list)
    run(scenario())


def test_arxiv_preserves_field_queries_and_emits_pdf_links(monkeypatch):
    import backend.core.agentscope.tools.arxiv_tool as module
    xml = '''<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>https://arxiv.org/abs/1234</id><title>Title</title><summary>Abstract</summary><published>2026-01-01</published><author><name>Author</name></author><category term="cs.AI"/><link title="pdf" href="https://arxiv.org/pdf/1234"/></entry></feed>'''
    response = SimpleNamespace(raise_for_status=lambda: None, text=AsyncMock(return_value=xml))

    class Context:
        async def __aenter__(self):
            return response
        async def __aexit__(self, *args):
            pass

    class Client(Context):
        def __init__(self, **kwargs):
            assert kwargs["timeout"].total == 30
        async def __aenter__(self):
            return self
        def get(self, url):
            from urllib.parse import urlparse, parse_qs
            assert parse_qs(urlparse(url).query)["search_query"] == ["cat:cs.AI"]
            return Context()

    monkeypatch.setattr(module.aiohttp, "ClientSession", Client)
    tool = ArXivTool()
    papers = run(tool._search_arxiv("cat:cs.AI"))
    assert papers[0]["categories"] == ["cs.AI"]
    assert "https://arxiv.org/pdf/1234" in tool._format_papers(papers, "q")


def test_transport_failure_uses_fallback_report_instead_of_policy_message():
    agent = DeepResearchAgent.__new__(DeepResearchAgent)
    agent.session_memory = SimpleNamespace(get_research_findings=AsyncMock(return_value=[{"content": "collected evidence", "source_type": "web", "relevance_score": None}]),
                                           get_citations=AsyncMock(return_value=[]))
    agent.llm_manager = AsyncMock(side_effect=APIError("network unavailable"))
    agent.findings_count = 1
    agent.current_tools_used = []
    report = run(agent._generate_research_report("q"))
    assert "collected evidence" in report
    assert "内容安全限制" not in report


def test_report_does_not_fabricate_evidence_scores_or_support_relations():
    service = research_service()
    findings = [{"content": "finding", "source_type": "web", "relevance_score": None}]
    report = run(service.format_final_report("session", {"findings": findings, "citations": []}))
    assert report["metadata"]["quality_score"] is None
    assert report["key_findings"][0]["relevance_score"] is None
    assert report["evidence_chain"]["relationships"] == []


def test_provider_detects_truncated_success_response():
    async def scenario():
        llm = DeepSeekLLM(api_key="test", max_retries=0)
        llm._session = SimpleNamespace(closed=False, post=Mock(return_value=Response(lines=[
            b'data: {"choices":[{"delta":{"content":"partial"}}]}\n'
        ])))
        with pytest.raises(APIError):
            async for _ in llm.chat_completion_stream([], "deepseek-flash"):
                pass
    run(scenario())


def test_real_http_pool_retries_and_reuses_connection():
    from aiohttp import web

    async def scenario():
        transports = []

        async def handler(request):
            transports.append(request.transport)
            await request.json()
            if len(transports) == 1:
                return web.json_response({"error": "busy"}, status=503)
            return web.json_response({"choices": [{"message": {"content": "ok"}}]})

        app = web.Application()
        app.router.add_post("/chat", handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        port = site._server.sockets[0].getsockname()[1]
        llm = DeepSeekLLM(api_key="test", max_retries=1, retry_delay=0)
        try:
            await llm._request_json(f"http://127.0.0.1:{port}/chat", {})
            await llm._request_json(f"http://127.0.0.1:{port}/chat", {})
            assert len(transports) == 3 and len(set(transports)) == 1
        finally:
            await llm.close()
            await runner.cleanup()
    run(scenario())


def test_tool_result_blocks_are_persisted_and_citation_failure_propagates():
    agent = DeepResearchAgent.__new__(DeepResearchAgent)
    message = Msg("tool", [{"type": "tool_result", "id": "search-call", "name": "search_arxiv_papers",
                            "output": [{"type": "text", "text": "1. Paper title\n作者: Alice, Bob\nID: https://arxiv.org/abs/1234\n发布时间: 2026-01-01\n摘要: useful evidence"}]}], "system")
    agent.memory = SimpleNamespace(get_memory=AsyncMock(return_value=[message]))
    agent.session_memory = SimpleNamespace(add_citation=AsyncMock(return_value=1), add_research_finding=AsyncMock(return_value=2))
    agent.current_tools_used = []
    agent.findings_count = 0

    async def scenario():
        await agent._extract_tools_and_findings_from_memory()
        await agent._extract_tools_and_findings_from_memory()
        assert agent.findings_count == 1
        assert agent.session_memory.add_citation.await_args.kwargs["authors"] == ["Alice", "Bob"]
        assert agent.session_memory.add_research_finding.await_args.kwargs["relevance_score"] is None
        agent.session_memory.add_citation.side_effect = RuntimeError("database unavailable")
        with pytest.raises(RuntimeError):
            await agent._save_arxiv_citation({"title": "paper", "url": "https://arxiv.org/abs/1234"})
    run(scenario())


def test_zhipu_search_calls_real_endpoint_with_filters():
    from backend.core.llm.zhipu_llm import ZhipuLLM
    llm = ZhipuLLM(api_key="test")
    llm._make_request = AsyncMock(return_value={"search_result": []})
    run(llm.web_search("q", count=4, search_domain_filter="arxiv.org", search_recency_filter="oneWeek"))
    endpoint, body = llm._make_request.await_args.args
    assert endpoint == "web_search"
    assert body["count"] == 4 and body["search_domain_filter"] == "arxiv.org"


def test_memory_disabled_creates_no_vector_or_model_clients(monkeypatch):
    import backend.core.memory.memory_manager as module
    monkeypatch.setattr(module, "get_memory_config", lambda: MemoryConfig(enabled=False))
    vector = Mock()
    retriever = Mock()
    monkeypatch.setattr(module, "VectorStore", vector)
    monkeypatch.setattr(module, "HyDERetriever", retriever)
    memory = Mem0MemoryManager()
    assert not memory.enabled and run(memory.retrieve_memories("q", "u")) == []
    vector.assert_not_called()
    retriever.assert_not_called()


@pytest.mark.asyncio
async def test_completed_research_report_and_ownership_survive_service_restart(postgres_pool, monkeypatch):
    import io
    import sys
    from backend.repositories.research_dao import ResearchDAO
    from backend.repositories.chat_dao import ChatDAO
    import backend.services.agentscope_research_service as module

    class Agent:
        def __init__(self, session_id, **kwargs):
            self.session_id = session_id
            self.memory_manager = ResearchMemoryManager(ResearchDAO())

        async def async_init(self):
            self.session_memory = await self.memory_manager.create_session(self.session_id)

        async def conduct_research(self, **kwargs):
            await self.session_memory.add_research_finding("web", "https://example.org/paper", "persisted research evidence", None)
            await self.session_memory.add_citation("Paper", ["Alice", "Bob"], "https://example.org/paper")
            return {"report": "Persisted full research report"}

        async def export_session_data(self):
            return {**(await self.session_memory.export_session_data()), "report": "Persisted full research report", "tools_used": ["web_search"]}

    monkeypatch.setattr(module, "DeepResearchAgent", Agent)
    service = research_service()
    service.research_dao = ResearchDAO()
    service.chat_dao = ChatDAO()
    service.llm_provider = "deepseek"
    service.default_llm = SimpleNamespace(model="deepseek-flash")
    service.default_multimodal_llm = service.default_llm
    service._get_web_search_api_key = AsyncMock(return_value="test")
    started = await service.start_research("research topic", user_id="alice")
    assert started["success"]
    task = service.active_researchers[started["session_id"]]._research_task
    # Windows pipes default to GBK. Logging must never change task completion.
    with monkeypatch.context() as output_patch:
        output_patch.setattr(sys, "stdout", io.TextIOWrapper(io.BytesIO(), encoding="gbk", errors="strict"))
        await task
    session_id = started["session_id"]
    assert (await service.get_research_status(session_id))["status"] == "completed"
    fresh = research_service()
    fresh.research_dao = ResearchDAO()
    export = await fresh.export_session_data(session_id)
    assert export["report"] == "Persisted full research report"
    assert export["citations"][0]["authors"] == ["Alice", "Bob"]
    assert len(export["findings"]) == 1
    assert export["findings"][0]["content"] == "persisted research evidence"
    assert export["findings"][0]["relevance_score"] is None
    assert await fresh.validate_session_access(session_id, "alice")
    assert not await fresh.validate_session_access(session_id, "bob")
    assert await fresh.search_research_content("persisted", "bob") == []
    sessions = await service.chat_dao.get_user_sessions("alice")
    assert sessions[0]["llm_provider"] == "deepseek" and sessions[0]["model_name"] == "deepseek-flash"
    assert export["session_info"]["chat_session_id"] == sessions[0]["id"]
    from backend.api.chat import get_messages
    from backend.api.interactions import conversation_evidence
    from backend.schemas.chat import ChatMessage
    history = await get_messages(sessions[0]["id"], limit=None, user_id="alice")
    saved = ChatMessage.model_validate(history[-1]).model_dump()
    assert saved["metadata"]["session_id"] == session_id
    assert saved["metadata"]["type"] == "research"
    assert saved["metadata"]["evidence"][0]["source_url"] == "https://example.org/paper"
    evidence = await conversation_evidence(sessions[0]["id"], limit=100, offset=0, user={"user_id": "alice"})
    assert evidence["total_evidence"] == 1
    assert evidence["evidence_list"][0]["confidence_score"] is None


@pytest.mark.asyncio
async def test_enabled_memory_persists_in_chroma_and_invalidates_real_redis(postgres_pool, redis_store, tmp_path, monkeypatch):
    import uuid
    import backend.core.memory.memory_manager as module
    from backend.core.memory.hyde_retriever import HyDERetriever

    owner, other = f"memory-{uuid.uuid4().hex}", f"memory-{uuid.uuid4().hex}"
    async with postgres_pool.acquire() as conn:
        await conn.executemany(
            "INSERT INTO users(id,username,email,password_hash) VALUES($1,$1,$2,'test')",
            [(owner, owner + "@testing.invalid"), (other, other + "@testing.invalid")],
        )
    settings = MemoryConfig(enabled=True, chroma_persist_dir=str(tmp_path / "chroma"),
                            chroma_collection_name="regression_memories", hyde_enabled=False,
                            query_cache_ttl=37, cache_ttl=43)
    monkeypatch.setattr(module, "get_memory_config", lambda: settings)
    monkeypatch.setattr(module, "redis_client", redis_store)
    monkeypatch.setattr(HyDERetriever, "embed_text", AsyncMock(return_value=[1.0, 0.0, 0.0]))
    embed_query = AsyncMock(return_value=[1.0, 0.0, 0.0])
    monkeypatch.setattr(HyDERetriever, "embed_query_with_hyde", embed_query)
    manager = Mem0MemoryManager()
    assert manager.vector_store is not None
    first_id = await manager.add_memory(owner, "Owner's persistent preference", validity_score=0.95)
    other_id = await manager.add_memory(other, "Other user's private preference", validity_score=0.95)
    assert first_id and other_id
    reopened = Mem0MemoryManager()
    first = await reopened.retrieve_memories("preference", owner, top_k=5, use_hyde=False)
    second = await reopened.retrieve_memories("preference", owner, top_k=5, use_hyde=False)
    assert first == second and [item["id"] for item in first] == [first_id]
    assert embed_query.await_count == 1
    cached_keys = [key async for key in redis_store._redis.scan_iter(match=f"memory:query:{owner}:*")]
    assert cached_keys and 0 < await redis_store.ttl(cached_keys[0]) <= 37
    assert "persistent preference" in await reopened.get_user_context(owner)
    second_id = await reopened.add_memory(owner, "Owner's new persistent preference", validity_score=0.95)
    after_write = await reopened.retrieve_memories("preference", owner, top_k=5, use_hyde=False)
    assert {item["id"] for item in after_write} == {first_id, second_id}
    assert "new persistent preference" in await reopened.get_user_context(owner)
    assert embed_query.await_count == 2
    assert not await reopened.delete_memory(first_id, other)
    assert await reopened.delete_memory(first_id, owner)
    after_delete = await reopened.retrieve_memories("preference", owner, top_k=5, use_hyde=False)
    assert [item["id"] for item in after_delete] == [second_id]
    # Extra filters cannot replace the owner's mandatory vector filter.
    scoped = await asyncio.to_thread(reopened.vector_store.search_memories, [1.0, 0.0, 0.0], owner, 5, {"user_id": other})
    assert all(item["metadata"]["user_id"] == owner for item in scoped)
    for user_id in (owner, other):
        keys = [key async for key in redis_store._redis.scan_iter(match=f"memory:*:{user_id}*")]
        if keys:
            await redis_store._redis.delete(*keys)


def test_tts_supported_engine_and_atomic_cache(tmp_path, monkeypatch):
    import edge_tts
    from backend.core.tts import TTSManager, TTSEngine
    assert list(TTSEngine) == [TTSEngine.EDGE]
    with pytest.raises(ValueError):
        TTSManager(output_dir=str(tmp_path), default_engine="unimplemented")
    manager = TTSManager(output_dir=str(tmp_path))
    calls = []

    class Communicate:
        def __init__(self, **kwargs):
            pass
        async def save(self, path):
            calls.append(path)
            assert Path(path).suffix == ".tmp"
            Path(path).write_bytes(b"valid-mp3-bytes")

    monkeypatch.setattr(edge_tts, "Communicate", Communicate)

    async def scenario():
        with pytest.raises(ValueError):
            await manager.generate_audio("hello", output_format="../../escape")
        path = await manager.generate_audio("hello")
        assert Path(path).read_bytes() == b"valid-mp3-bytes"
        assert await manager.generate_audio("hello") == path
        assert len(calls) == 1 and not list(tmp_path.glob("*.tmp"))
        keep = tmp_path / "unrelated.mp3"
        keep.write_bytes(b"keep")
        assert manager.clear_cache() == 1 and keep.exists()
    run(scenario())


@pytest.mark.asyncio
async def test_interrupted_research_resumes_real_agent_checkpoint_in_new_service(postgres_pool, monkeypatch):
    from backend.repositories.research_dao import ResearchDAO
    from backend.repositories.chat_dao import ChatDAO
    import backend.services.agentscope_research_service as module

    started = asyncio.Event()

    class PausingAgent(DeepResearchAgent):
        executions = 0

        async def conduct_research(self, **kwargs):
            type(self).executions += 1
            if type(self).executions == 1:
                await self.session_memory.add_message(Msg("user", "checkpoint context", "user"))
                started.set()
                await asyncio.Event().wait()
            messages = await self.session_memory.get_memory()
            assert any(message.content == "checkpoint context" for message in messages)
            self.research_result = {"report": "resumed report"}
            return self.research_result

    monkeypatch.setattr(module, "DeepResearchAgent", PausingAgent)

    def create_service():
        service = research_service()
        service.research_dao = ResearchDAO()
        service.chat_dao = ChatDAO()
        service.llm_provider = "deepseek"
        service.default_llm = DeepSeekLLM(api_key="test", model="deepseek-flash")
        service.default_multimodal_llm = service.default_llm
        service._get_web_search_api_key = AsyncMock(return_value="test")
        return service

    service = create_service()
    result = await service.start_research("topic", user_id="alice")
    assert result["success"]
    await started.wait()
    session_id = result["session_id"]
    assert (await service.interrupt_research(session_id))["success"]
    assert (await service.get_research_status(session_id))["status"] == "interrupted"
    resumed = create_service()
    assert (await resumed.resume_research(session_id))["success"]
    await resumed.active_researchers[session_id]._research_task
    assert (await resumed.get_research_status(session_id))["status"] == "completed"
    assert (await resumed.export_session_data(session_id))["report"] == "resumed report"


@pytest.mark.parametrize("endpoint,terminal", [("chat", {"done": True, "message": {"content": "final"}}), ("pull", {"status": "success"})])
@pytest.mark.parametrize("complete", [False, True])
async def test_ollama_requires_endpoint_terminal_over_real_http(endpoint, terminal, complete):
    from aiohttp import web
    from backend.core.llm.ollama_llm import OllamaLLM
    chunks = [{"done": False, "message": {"content": "partial"}, "status": "downloading"}]
    if complete:
        chunks.append(terminal)
    async def handler(request):
        return web.Response(text="\n".join(json.dumps(chunk) for chunk in chunks) + "\n", content_type="application/x-ndjson")
    app = web.Application()
    app.router.add_post(f"/api/{endpoint}", handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    llm = OllamaLLM(base_url=f"http://127.0.0.1:{site._server.sockets[0].getsockname()[1]}", max_retries=0)
    try:
        stream = llm.chat_completion_stream([], "test") if endpoint == "chat" else llm.pull_model("test")
        received = []
        async def consume():
            async for chunk in stream:
                received.append(chunk)
        if complete:
            await consume()
            assert received == (["partial", "final"] if endpoint == "chat" else chunks)
        else:
            with pytest.raises(APIError, match="terminal"):
                await consume()
            assert len(received) == 1
    finally:
        await llm.close()
        await runner.cleanup()


async def test_real_research_agent_constructs_and_generates_report_under_gbk(monkeypatch):
    import io
    import sys
    llm = DeepSeekLLM(api_key="test", model="deepseek-flash")
    llm.chat_completion = AsyncMock(return_value={"choices": [{"message": {"content": "Real adapter report"}}]})
    with monkeypatch.context() as output_patch:
        output_patch.setattr(sys, "stdout", io.TextIOWrapper(io.BytesIO(), encoding="gbk", errors="strict"))
        agent = DeepResearchAgent("gbk-regression", llm, web_search_api_key="test")
        agent.session_memory = SimpleNamespace(get_research_findings=AsyncMock(return_value=[]), get_citations=AsyncMock(return_value=[]))
        try:
            report = await agent._generate_research_report("Encoding-safe research")
            assert "Real adapter report" in report
            llm.chat_completion.assert_awaited_once()
        finally:
            await agent.close()
            await llm.close()
