from io import BytesIO
from unittest.mock import AsyncMock

from fastapi import HTTPException, UploadFile
import pytest

from backend.repositories.chat_dao import ChatDAO
from backend.repositories.interaction_dao import InteractionDAO
from backend.services.interaction_service import upload_document


async def create_chat():
    dao = ChatDAO()
    session = await dao.create_session("alice", "Private title", "deepseek", "deepseek-flash")
    message_id = await dao.add_message(session["id"], "assistant", "Private response")
    return session, {"id": message_id}


@pytest.mark.database
async def test_branch_enforces_owner_and_valid_user_pivot(postgres_pool):
    from backend.api.chat import branch_session
    from backend.schemas.chat import ChatBranchRequest
    dao = ChatDAO()
    session, assistant = await create_chat()
    user_id = await dao.add_message(session["id"], "user", "A user turn")
    for owner, pivot in [("bob", user_id), ("alice", assistant["id"]), ("alice", user_id + 100)]:
        with pytest.raises(HTTPException) as exc:
            await branch_session(session["id"], ChatBranchRequest(before_message_id=pivot), user_id=owner)
        assert exc.value.status_code == 404
    assert len(await dao.get_user_sessions("alice")) == 1
    assert len(await dao.get_session_messages(session["id"])) == 2


@pytest.mark.database
async def test_share_persists_snapshot_expires_and_can_be_revoked(postgres_pool):
    session, message = await create_chat()
    dao = InteractionDAO()
    assert await dao.create_share("bob", session["id"], None, None, 1) is None
    share = await dao.create_share("alice", session["id"], "Shared", "Description", 1)
    assert len(share["id"]) >= 32
    await postgres_pool.execute("UPDATE chat_messages SET content='Later private edit' WHERE id=$1", message["id"])
    result = await dao.get_public_share(share["id"])
    assert result["messages"][0]["content"] == "Private response"
    assert result["view_count"] == 1
    assert result["title"] == "Shared"
    assert await dao.revoke_share(share["id"], "bob") is None
    await postgres_pool.execute("UPDATE conversation_shares SET expires_at='2000-01-01' WHERE id=$1", share["id"])
    assert await dao.get_public_share(share["id"]) is None
    assert await dao.revoke_share(share["id"], "alice")


@pytest.mark.database
async def test_reports_feedback_and_evidence_updates_enforce_owner(postgres_pool):
    session, message = await create_chat()
    dao = InteractionDAO()
    assert await dao.report_message("bob", message["id"], "spam", "") is None
    assert await dao.report_message("alice", message["id"], "spam", "details")
    assert await dao.save_feedback("bob", message["id"], 1, None) is None
    await dao.save_feedback("alice", message["id"], 1, "useful")
    await dao.save_feedback("alice", message["id"], -1, "correction")
    assert (await dao.get_feedback("alice", message["id"]))[0]["rating"] == -1
    assert await dao.get_feedback("bob", message["id"]) == []
    await postgres_pool.execute("INSERT INTO research_sessions(id,user_id,title) VALUES('research','alice','Topic')")
    citation_id = await postgres_pool.fetchval(
        "INSERT INTO research_citations(session_id,title,authors,source_url) VALUES('research','Paper',$1,'https://example.test') RETURNING id",
        ["Author"],
    )
    assert await dao.update_evidence(citation_id, "bob", verified=True) is None
    await dao.update_evidence(citation_id, "alice", verified=True)
    await dao.update_evidence(citation_id, "alice", used=True)
    evidence = (await dao.session_evidence("research", "alice", 10, 0))[0]
    assert evidence["verified_by_user"] and evidence["used_in_response"]
    assert await dao.session_evidence("research", "bob", 10, 0) == []


@pytest.mark.database
async def test_upload_persists_content_and_scopes_retrieval(postgres_pool):
    result = await upload_document(UploadFile(filename="../../notes.md", file=BytesIO(b"quasars and galaxies")), "alice")
    assert result["filename"] == "notes.md"
    assert result["processed_content"] == "quasars and galaxies"
    dao = InteractionDAO()
    assert (await dao.get_document(result["document_id"], "alice"))["content"] == result["processed_content"]
    assert await dao.get_document(result["document_id"], "bob") is None
    assert await dao.search_documents("quasars", "alice", 10)
    assert await dao.search_documents("quasars", "bob", 10) == []
    assert await dao.delete_document(result["document_id"], "bob") is None


@pytest.mark.parametrize("filename,content,status", [("run.exe", b"binary", 415), ("notes.txt", b"\xff", 422), ("notes.txt", b"", 422)])
async def test_upload_rejects_bad_input_before_persistence(filename, content, status):
    dao = AsyncMock()
    with pytest.raises(HTTPException) as exc:
        await upload_document(UploadFile(filename=filename, file=BytesIO(content)), "alice", dao)
    assert exc.value.status_code == status
    dao.save_document.assert_not_awaited()


async def test_image_upload_uses_default_vlm_and_preserves_image_blocks(monkeypatch):
    from PIL import Image
    from backend.core.llm.factory import LLMFactory
    from backend.config.llm_config import get_config
    from backend.services.interaction_service import describe_image
    image = BytesIO()
    Image.new("RGB", (2, 2), "blue").save(image, format="PNG")
    llm = AsyncMock()
    llm.chat_completion.return_value = {"choices": [{"message": {"content": "A blue square"}}]}
    monkeypatch.setattr(LLMFactory, "create_llm", lambda provider: llm)
    monkeypatch.setattr(get_config().deepseek, "default_model", "deepseek-flash")
    assert await describe_image(image.getvalue()) == "A blue square"
    request = llm.chat_completion.await_args.kwargs
    assert request["model"] == "deepseek-flash"
    assert request["messages"][0]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")
    llm.close.assert_awaited_once()
