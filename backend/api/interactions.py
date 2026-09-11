"""Authenticated report, share, upload, feedback, and evidence endpoints."""

from collections import Counter
from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from backend.api.deep_research import citation_evidence, research_service
from backend.repositories.chat_dao import ChatDAO
from backend.repositories.interaction_dao import InteractionDAO
from backend.middleware.auth import get_current_user
from backend.core.security.quota import enforce_request_quota
from backend.services.interaction_service import document_response, upload_document

router = APIRouter(prefix="/api", tags=["interactions"])
interaction_dao = InteractionDAO()
chat_dao = ChatDAO()


class ReportRequest(BaseModel):
    message_id: int = Field(gt=0)
    report_reason: str = Field(min_length=1, max_length=200)
    report_description: str = Field(default="", max_length=5000)


class ShareRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=255)
    title: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = Field(default=None, max_length=5000)
    expire_days: int = Field(default=30, ge=1, le=365)


class FeedbackRequest(BaseModel):
    message_id: int = Field(gt=0)
    rating: Literal[-1, 1]
    comment: Optional[str] = Field(default=None, max_length=5000)


class UsedRequest(BaseModel):
    used: bool


class VerifiedRequest(BaseModel):
    verified: bool


def require_result(result):
    if result is None:
        raise HTTPException(status_code=404, detail="数据不存在或无权访问")
    return result


@router.post("/moderation/report", status_code=201)
async def report_message(request: ReportRequest, user=Depends(get_current_user)):
    result = await interaction_dao.report_message(
        user["user_id"], request.message_id, request.report_reason, request.report_description,
    )
    return {"success": True, "report": require_result(result)}


@router.post("/share/conversation", status_code=201)
async def share_conversation(request: ShareRequest, user=Depends(get_current_user)):
    result = require_result(await interaction_dao.create_share(
        user["user_id"], request.session_id, request.title, request.description, request.expire_days,
    ))
    return {**result, "success": True, "public_url": f"/share/{result['id']}"}


@router.delete("/share/{share_id}")
async def revoke_share(share_id: str, user=Depends(get_current_user)):
    require_result(await interaction_dao.revoke_share(share_id, user["user_id"]))
    return {"success": True}


@router.get("/public/conversation/{share_id}")
async def public_conversation(share_id: str):
    return require_result(await interaction_dao.get_public_share(share_id))


@router.post("/feedback/submit")
async def submit_feedback(request: FeedbackRequest, user=Depends(get_current_user)):
    return require_result(await interaction_dao.save_feedback(
        user["user_id"], request.message_id, request.rating, request.comment,
    ))


@router.get("/feedback/message/{message_id}")
async def message_feedback(message_id: int, user=Depends(get_current_user)):
    require_result(await interaction_dao.owned_message(message_id, user["user_id"]))
    feedbacks = await interaction_dao.get_feedback(user["user_id"], message_id)
    return {"feedbacks": feedbacks, "total_feedbacks": len(feedbacks)}


@router.delete("/feedback/message/{message_id}")
async def delete_feedback(message_id: int, user=Depends(get_current_user)):
    require_result(await interaction_dao.owned_message(message_id, user["user_id"]))
    await interaction_dao.delete_feedback(user["user_id"], message_id)
    return {"success": True}


@router.post("/rag/upload-document", status_code=201, dependencies=[Depends(enforce_request_quota)])
@router.post("/files/upload", status_code=201, dependencies=[Depends(enforce_request_quota)])
async def upload(file: UploadFile = File(...), user=Depends(get_current_user)):
    return await upload_document(file, user["user_id"], interaction_dao)


@router.post("/rag/upload-multiple", status_code=201, dependencies=[Depends(enforce_request_quota)])
async def upload_multiple(files: list[UploadFile] = File(...), user=Depends(get_current_user)):
    if not 1 <= len(files) <= 10:
        raise HTTPException(status_code=422, detail="一次上传 1 到 10 个文件")
    results = []
    for file in files:
        results.append(await upload_document(file, user["user_id"], interaction_dao))
    return {"success": True, "files": results}


@router.get("/rag/documents")
@router.get("/files/list")
async def list_documents(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100),
    user=Depends(get_current_user),
):
    documents = await interaction_dao.list_documents(user["user_id"], page_size, (page - 1) * page_size)
    return {"documents": [document_response(document) for document in documents]}


@router.get("/rag/document/{document_id}")
@router.get("/files/{document_id}/status")
async def get_document(document_id: str, user=Depends(get_current_user)):
    return document_response(require_result(await interaction_dao.get_document(document_id, user["user_id"])))


@router.delete("/rag/document/{document_id}")
@router.delete("/files/{document_id}")
async def delete_document(document_id: str, user=Depends(get_current_user)):
    require_result(await interaction_dao.delete_document(document_id, user["user_id"]))
    return {"success": True}


@router.get("/rag/search")
async def search_documents(
    query: str = Query(..., min_length=1, max_length=500), limit: int = Query(20, ge=1, le=100),
    user=Depends(get_current_user),
):
    return {"results": await interaction_dao.search_documents(query, user["user_id"], limit)}


@router.get("/evidence/stats")
async def evidence_stats(days: int = Query(30, ge=1, le=3650), user=Depends(get_current_user)):
    stats = await interaction_dao.evidence_stats(user["user_id"], days)
    return {**stats, "avg_relevance_score": None}


async def evidence_for_session(session_id, user_id, limit, offset):
    citations = await interaction_dao.session_evidence(session_id, user_id, limit, offset)
    evidence = citation_evidence(citations)
    for entry, citation in zip(evidence, citations):
        entry.update({key: citation[key] for key in ("used_in_response", "verified_by_user")})
    return {"evidence_list": evidence, "total_evidence": len(evidence),
            "evidence_by_type": dict(Counter(entry["source_type"] for entry in evidence))}


@router.get("/evidence/research/{session_id}")
async def research_evidence(
    session_id: str, limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0),
    user=Depends(get_current_user),
):
    if not await research_service.validate_session_access(session_id, user["user_id"]):
        raise HTTPException(status_code=404, detail="研究会话不存在或无权访问")
    return await evidence_for_session(session_id, user["user_id"], limit, offset)


@router.get("/evidence/conversation/{session_id}")
async def conversation_evidence(
    session_id: str, limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0),
    user=Depends(get_current_user),
):
    session = require_result(await chat_dao.get_session(session_id))
    if session["user_id"] != user["user_id"]:
        raise HTTPException(status_code=404, detail="会话不存在或无权访问")
    messages = await chat_dao.get_session_messages(session_id)
    research_ids = {message.get("metadata", {}).get("session_id")
                    for message in messages if isinstance(message.get("metadata"), dict)}
    evidence = []
    for research_id in research_ids - {None}:
        result = await evidence_for_session(research_id, user["user_id"], 500, 0)
        evidence.extend(result["evidence_list"])
    return {"evidence_list": evidence[offset:offset + limit], "total_evidence": len(evidence),
            "evidence_by_type": dict(Counter(entry["source_type"] for entry in evidence))}


@router.put("/evidence/{citation_id}/mark_used")
async def mark_used(citation_id: int, request: UsedRequest, user=Depends(get_current_user)):
    return require_result(await interaction_dao.update_evidence(citation_id, user["user_id"], used=request.used))


@router.put("/evidence/{citation_id}/verify")
async def verify_evidence(citation_id: int, request: VerifiedRequest, user=Depends(get_current_user)):
    return require_result(await interaction_dao.update_evidence(citation_id, user["user_id"], verified=request.verified))
