import asyncio
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from backend.api import deep_research, chat
from backend.core.security.quota import enforce_request_quota
from backend.middleware.auth import get_current_user


def api_client(router, authenticated=False):
    app = FastAPI()
    app.include_router(router)
    if authenticated:
        app.dependency_overrides[get_current_user] = lambda: {"user_id": "alice"}
        from backend.api.user import get_current_user_id
        app.dependency_overrides[get_current_user_id] = lambda: "alice"
        app.dependency_overrides[enforce_request_quota] = lambda: None
    return TestClient(app)


@pytest.mark.parametrize("route", [
    "/status/secret", "/export/secret", "/stream/secret", "/sessions", "/search?query=test", "/statistics",
])
def test_research_reads_require_authentication(route):
    response = api_client(deep_research.router).get("/api/research" + route)
    assert response.status_code == 401


@pytest.mark.parametrize("route", ["/status/secret", "/export/secret", "/stream/secret"])
def test_research_rejects_other_users_session(route, monkeypatch):
    access = AsyncMock(return_value=False)
    monkeypatch.setattr(deep_research.research_service, "validate_session_access", access)
    response = api_client(deep_research.router, True).get("/api/research" + route)
    assert response.status_code == 403
    access.assert_awaited_once_with("secret", "alice")


@pytest.mark.parametrize("route", ["/sessions?", "/search?query=test&", "/statistics?"])
def test_query_parameter_cannot_impersonate_other_user(route):
    response = api_client(deep_research.router, True).get("/api/research" + route + "user_id=bob")
    assert response.status_code == 403


@pytest.mark.parametrize("status", ["failed", "error", "interrupted", "not_found"])
async def test_all_unsuccessful_terminal_research_states_end_stream(status, monkeypatch):
    monkeypatch.setattr(deep_research.research_service, "get_research_status", AsyncMock(return_value={"status": status}))
    events = await asyncio.wait_for(collect(deep_research.research_events("session")), timeout=1)
    assert events[-1]["type"] == "error"
    assert events[-1]["status"] == status


async def collect(events):
    return [event async for event in events]


async def test_stuck_research_stream_has_deadline(monkeypatch):
    monkeypatch.setattr(deep_research, "STREAM_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(deep_research.research_service, "get_research_status", AsyncMock(return_value={"status": "active"}))
    events = await asyncio.wait_for(collect(deep_research.research_events("session")), timeout=1)
    assert events[-1]["status"] == "timeout"


def test_citation_scores_are_unknown_until_measured():
    evidence = deep_research.citation_evidence([{"id": 7, "title": "Paper", "source_url": "https://arxiv.org/abs/123"}])
    assert evidence[0]["id"] == 7
    assert evidence[0]["confidence_score"] is None
    assert evidence[0]["relevance_score"] is None


def test_websocket_authenticates_before_disclosing_progress(monkeypatch):
    status = AsyncMock()
    monkeypatch.setattr(deep_research.research_service, "get_research_status", status)
    from starlette.websockets import WebSocketDisconnect
    with api_client(deep_research.router).websocket_connect("/api/research/ws/progress/secret") as socket:
        socket.send_json({"token": "bad"})
        with pytest.raises(WebSocketDisconnect) as exc:
            socket.receive_json()
        assert exc.value.code == 1008
    status.assert_not_awaited()


def test_stream_provider_failure_emits_error_without_done(monkeypatch):
    monkeypatch.setattr(chat.chat_service, "get_session", AsyncMock(return_value={"user_id": "alice"}))
    monkeypatch.setattr(chat.chat_service, "prepare_chat", AsyncMock())
    async def broken_stream(request):
        yield 'data: {"type":"chunk","content":"partial"}\n\n'
        raise RuntimeError("private-provider-response")
    monkeypatch.setattr(chat.chat_service, "chat_stream", broken_stream)
    response = api_client(chat.router, True).post("/api/chat/chat/stream", json={"session_id": "session", "message": "hi"})
    assert response.status_code == 200
    assert '"type": "error"' in response.text
    assert '"done"' not in response.text
    assert "private-provider-response" not in response.text


def test_global_error_and_cors_do_not_disclose_to_untrusted_origin():
    from backend.main import app
    from starlette.requests import Request
    from backend.main import global_exception_handler
    result = asyncio.run(global_exception_handler(Request({"type": "http"}), RuntimeError("secret-dsn")))
    assert b"secret-dsn" not in result.body
    response = TestClient(app).get("/health", headers={"Origin": "https://untrusted.invalid", "Cookie": "session=value"})
    assert "access-control-allow-origin" not in response.headers
    assert "access-control-allow-credentials" not in response.headers
