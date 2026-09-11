"""Exercise actual routes, PostgreSQL, and Redis; only the billable model is replaced."""

import uuid
from unittest.mock import AsyncMock

import httpx
import pytest


@pytest.mark.database
async def test_register_chat_refresh_share_logout(postgres_pool, redis_store, monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "integration-test-secret-" + "x" * 32)
    from backend.main import app
    from backend.api.chat import chat_service
    from backend.core.llm.deepseek_llm import DeepSeekLLM

    monkeypatch.setattr(chat_service, "memory_enabled", False)
    provider = DeepSeekLLM(api_key="test-key", model="deepseek-flash")
    monkeypatch.setattr(provider, "chat_completion", AsyncMock(return_value={
        "choices": [{"message": {"content": "Verified model reply"}}],
        "usage": {"total_tokens": 5, "prompt_tokens_details": {"cached_tokens": 2}},
    }))
    monkeypatch.setattr(chat_service, "_get_llm_instance", lambda *args: provider)
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=(uuid.uuid4().hex, 1)), base_url="http://test")
    async with client:
        registration = await client.post("/api/users/register", json={
            "username": "new_user", "email": "new_user@example.com", "password": "Passw0rd!",
        })
        assert registration.status_code == 200, registration.text
        tokens = registration.json()
        client.headers["Authorization"] = "Bearer " + tokens["access_token"]
        preferences = await client.put("/api/users/preferences", json={"preferences": {"nested": {"enabled": True}}})
        assert preferences.status_code == 200, preferences.text
        assert (await client.get("/api/users/preferences")).json()["preferences"]["nested"]["enabled"]
        session = await client.post("/api/chat/sessions", json={"title": "Integration"})
        assert session.status_code == 200, session.text
        session_id = session.json()["id"]
        assert session.json()["model_name"] == "deepseek-flash"
        answer = await client.post("/api/chat/chat", json={"session_id": session_id, "message": "hello"})
        assert answer.status_code == 200, answer.text
        assert answer.json()["message"]["content"] == "Verified model reply"
        message_id = answer.json()["message"]["id"]
        assert (await client.post("/api/moderation/report", json={"message_id": message_id, "report_reason": "other"})).status_code == 201
        share = await client.post("/api/share/conversation", json={"session_id": session_id})
        assert share.status_code == 201, share.text
        public = await client.get("/api/public/conversation/" + share.json()["id"], headers={"Authorization": ""})
        assert public.status_code == 200
        assert public.json()["messages"][-1]["content"] == "Verified model reply"
        first_history = (await client.get(f"/api/chat/sessions/{session_id}/messages")).json()
        await client.post("/api/chat/chat", json={"session_id": session_id, "message": "Original later prompt"})
        original_history = (await client.get(f"/api/chat/sessions/{session_id}/messages")).json()
        branched = await client.post(f"/api/chat/sessions/{session_id}/branch", json={"before_message_id": original_history[2]["id"]})
        assert branched.status_code == 200, branched.text
        branch_id = branched.json()["id"]
        assert branch_id != session_id and branched.json()["message_count"] == 2
        prefix = (await client.get(f"/api/chat/sessions/{branch_id}/messages")).json()
        assert not {message["id"] for message in prefix} & {message["id"] for message in original_history}
        assert [message["content"] for message in prefix] == [message["content"] for message in first_history]
        edited = await client.post("/api/chat/chat", json={"session_id": branch_id, "message": "Edited prompt"})
        assert edited.status_code == 200, edited.text
        context = str(provider.chat_completion.await_args.kwargs["messages"])
        assert "Edited prompt" in context and "Original later prompt" not in context
        assert (await client.get(f"/api/chat/sessions/{session_id}/messages")).json() == original_history
        assert (await client.get("/api/users/me", headers={"Authorization": "Bearer " + tokens["refresh_token"]})).status_code == 401
        refreshed = await client.post("/api/users/refresh", json={"refresh_token": tokens["refresh_token"]})
        assert refreshed.status_code == 200, refreshed.text
        assert (await client.post("/api/users/refresh", json={"refresh_token": tokens["refresh_token"]})).status_code == 401
        client.headers["Authorization"] = "Bearer " + refreshed.json()["access_token"]
        assert (await client.post("/api/users/logout")).status_code == 200
        assert (await client.get("/api/users/me")).status_code == 401
        assert (await client.post("/api/users/refresh", json={"refresh_token": refreshed.json()["refresh_token"]})).status_code == 401
    await provider.close()
