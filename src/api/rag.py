# -*- coding: utf-8 -*-
"""
RAG 文档处理 API：支持文档上传、异步处理和状态查询。
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.db import get_db_session
from src.sqlmodel.models import User
from src.dao import DocumentProcessingJobDAO
from src.services.auth_service import get_current_user
from src.tasks.queue import enqueue_task, get_task_status, TaskPriority
from src.tasks.document_processor import process_document_task
from src.config.config_loader import get_settings
from src.config.logging import get_logger
from .errors import (
    handle_database_error,
    handle_file_error,
    handle_validation_error,
    handle_not_found_error,
    create_success_response,
    ErrorCodes
)

# 导入新的RAG功能
from src.core.rag import KnowledgeBase, FileProcessor, RAGCore
from src.core.rag.config import KB_NAME_PATTERN, MAX_KBS, MAX_FILE_SIZE_MB

logger = get_logger("rag")

settings = get_settings()

router = APIRouter(prefix="/rag", tags=["rag"])


class DocumentUploadResp(BaseModel):
    """文档上传响应"""
    job_id: str
    status: str
    message: str


class DocumentStatusResp(BaseModel):
    """文档处理状态响应"""
    job_id: str
    status: str
    filename: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    result: Optional[dict] = None


class DocumentListResp(BaseModel):
    """文档列表响应"""
    documents: List[DocumentStatusResp]
    total: int


@router.post("/upload-document", response_model=DocumentUploadResp)
async def upload_document_for_rag(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    上传文档进行 RAG 处理

    支持的文件格式：.docx, .doc, .txt, .md, .pdf
    """
    # Temporarily disabled due to missing DocumentProcessingJob model
    return create_error_response(
        code=ErrorCodes.BUSINESS_LOGIC_ERROR,
        message="文档上传功能暂时不可用，正在维护中",
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE
    )

    try:
        # 检查文件大小（UploadFile没有size属性，需要读取内容）
        file_content = await file.read()
        file_size = len(file_content)

        if file_size > settings.max_file_size:
            return create_error_response(
                code=ErrorCodes.VALIDATION_ERROR,
                message=f"文件大小超过限制：{settings.max_file_size} 字节",
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                details={"file_size": file_size, "max_size": settings.max_file_size}
            )

        # 重置文件指针以便后续读取
        await file.seek(0)
        
        # 检查文件类型
        file_extension = Path(file.filename).suffix.lower()
        allowed_types = settings.allowed_file_types.split(',')
        if file_extension not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型：{file_extension}。支持的类型：{', '.join(allowed_types)}"
            )
        
        # 创建上传目录
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}_{file.filename}"
        file_path = upload_dir / safe_filename
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 创建数据库记录
        job = DocumentProcessingJob(
            user_id=current_user.id,
            filename=file.filename,
            file_path=str(file_path),
            status="pending"
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        
        # 将处理任务添加到后台队列
        background_tasks.add_task(
            _process_document_background,
            str(job.id),
            str(file_path),
            str(current_user.id)
        )
        
        return DocumentUploadResp(
            job_id=str(job.id),
            status="pending",
            message="文档上传成功，正在后台处理"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # 清理已上传的文件
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

        logger.error(f"文档上传失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文档上传失败，请稍后重试"
        )


async def _process_document_background(job_id: str, file_path: str, user_id: str):
    """后台处理文档"""
    try:
        # 将任务加入队列
        task_id = await enqueue_task(
            "process_document",
            job_id,
            file_path,
            user_id,
            priority=TaskPriority.NORMAL
        )
        
        print(f"文档处理任务已加入队列：{task_id}")
        
    except Exception as e:
        print(f"后台处理文档失败：{str(e)}")
        # 更新任务状态为失败
        await _update_job_status_failed(job_id, str(e))


async def _update_job_status_failed(job_id: str, error_message: str):
    """更新任务状态为失败"""
    try:
        async for session in get_db_session():
            # 查询任务记录
            stmt = select(DocumentProcessingJob).where(DocumentProcessingJob.id == int(job_id))
            result = await session.execute(stmt)
            job = result.scalar_one_or_none()

            if job:
                job.status = "failed"
                job.error_message = error_message
                job.completed_at = datetime.utcnow()
                await session.commit()
                logger.info(f"任务 {job_id} 状态更新为失败: {error_message}")
            else:
                logger.warning(f"任务 {job_id} 不存在")

    except Exception as e:
        logger.error(f"更新任务状态失败: {e}")
        # 回退到直接SQL执行
        try:
            async for session in get_db_session():
                from sqlalchemy import text
                await session.execute(
                    text("UPDATE document_processing_jobs SET status = :status, error_message = :error, completed_at = :completed_at WHERE id = :job_id"),
                    {
                        "status": "failed",
                        "error": error_message,
                        "completed_at": datetime.utcnow(),
                        "job_id": int(job_id)
                    }
                )
                await session.commit()
                logger.info(f"使用SQL回退方式更新任务 {job_id} 状态为失败")
        except Exception as fallback_error:
            logger.error(f"SQL回退也失败: {fallback_error}")


@router.get("/document/{job_id}", response_model=DocumentStatusResp)
async def get_document_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取文档处理状态
    """
    try:
        # 使用 DAO 查询任务记录
        doc_dao = DocumentProcessingJobDAO(db)
        job_data = await doc_dao.get_job_status(int(job_id))

        if not job_data or str(job_data.user_id) != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档处理任务不存在或无权限访问"
            )

        return DocumentStatusResp(
            job_id=str(job_data.id),
            status=job_data.status,
            filename=job_data.filename,
            created_at=job_data.created_at.isoformat(),
            started_at=job_data.started_at.isoformat() if job_data.started_at else None,
            completed_at=job_data.completed_at.isoformat() if job_data.completed_at else None,
            error_message=job_data.error_message,
            result=job_data.result  # 从数据库获取结果
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取文档状态失败，请稍后重试"
        )


@router.get("/documents", response_model=DocumentListResp)
async def list_user_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    page: int = 1,
    page_size: int = 20
):
    """
    获取用户的文档列表
    """
    try:
        # 计算偏移量
        offset = (page - 1) * page_size

        # 使用 DAO 查询文档
        doc_dao = DocumentProcessingJobDAO(db)

        # 获取文档列表
        jobs = await doc_dao.get_user_jobs(
            user_id=current_user.id,
            skip=offset,
            limit=page_size
        )

        # 获取总数（简化实现，实际应该在 DAO 中添加 count 方法）
        total = len(jobs) + offset  # 简化实现

        documents = []
        for job in jobs:
            documents.append(DocumentStatusResp(
                job_id=str(job.id),
                status=job.status,
                filename=job.filename,
                created_at=job.created_at.isoformat(),
                started_at=job.started_at.isoformat() if job.started_at else None,
                completed_at=job.completed_at.isoformat() if job.completed_at else None,
                error_message=job.error_message,
                result=job.result
            ))

        return DocumentListResp(
            documents=documents,
            total=total
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档列表失败：{str(e)}"
        )


@router.delete("/document/{job_id}")
async def delete_document(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    删除文档处理任务
    """
    try:
        # 使用 DAO 查询任务记录
        doc_dao = DocumentProcessingJobDAO(db)
        job_data = await doc_dao.get_job_status(int(job_id))

        if not job_data or str(job_data.user_id) != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档处理任务不存在或无权限访问"
            )

        # 删除文件
        if os.path.exists(job_data.file_path):
            os.remove(job_data.file_path)

        # 使用 DAO 删除数据库记录
        success = await doc_dao.delete(job_id=int(job_id))

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除数据库记录失败"
            )

        await db.commit()

        return {"message": "文档删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除文档失败：{str(e)}"
        )


@router.post("/document/{job_id}/retry")
async def retry_document_processing(
    job_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    重试失败的文档处理任务
    """
    try:
        # 使用 DAO 查询任务记录
        doc_dao = DocumentProcessingJobDAO(db)
        job_data = await doc_dao.get_job_status(int(job_id))

        if not job_data or str(job_data.user_id) != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档处理任务不存在或无权限访问"
            )

        if job_data.status != "failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只有失败的任务才能重试"
            )

        # 使用 DAO 更新任务状态为待处理
        updated_job = await doc_dao.update_job_status(
            job_id=int(job_id),
            status="pending",
            error_message=None
        )

        if not updated_job:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新任务状态失败"
            )

        await db.commit()

        # 重新加入处理队列
        background_tasks.add_task(
            _process_document_background,
            str(job_id),
            job_data.file_path,
            str(current_user.id)
        )

        return {"message": "任务已重新加入处理队列"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重试任务失败：{str(e)}"
        )


@router.get("/search")
async def search_documents(
    query: str,
    current_user: User = Depends(get_current_user),
    limit: int = 10,
    score_threshold: float = 0.0,
    use_reranking: bool = True
):
    """
    在用户的文档中进行语义搜索（支持两阶段检索和重排序）

    Args:
        query: 搜索查询
        current_user: 当前用户
        limit: 返回结果数量限制
        score_threshold: 分数阈值
        use_reranking: 是否使用重排序（默认True）
    """
    try:
        from src.core.rag.pgvector_store import get_pgvector_store
        from src.core.rag.reranker import TwoStageRAGRetriever, CrossEncoderReranker
        from src.api.evidence import EvidenceResponse

        # 获取pgvector存储实例
        pgvector_store = get_pgvector_store()

        # 使用两阶段检索器
        if use_reranking:
            # 创建重排序器
            reranker = CrossEncoderReranker()

            # 创建两阶段检索器
            retriever = TwoStageRAGRetriever(
                vector_store=pgvector_store,
                reranker=reranker,
                recall_top_k=min(50, limit * 5),  # 召回更多候选文档
                final_top_k=limit,
                min_score_threshold=max(score_threshold, 0.1)
            )

            # 执行两阶段检索
            search_results = await retriever.search(
                query=query,
                filter_metadata={"user_id": current_user.id},
                score_threshold=score_threshold
            )

            # 转换结果格式
            results = []
            for doc_score in search_results:
                result = {
                    "chunk_id": doc_score.document_id,
                    "document_id": doc_score.metadata.get("document_id"),
                    "content": doc_score.content,
                    "score": doc_score.final_score,
                    "recall_score": doc_score.recall_score,
                    "rerank_score": doc_score.rerank_score,
                    "source_url": doc_score.metadata.get("source_url"),
                    "filename": doc_score.metadata.get("filename"),
                    "snippet": doc_score.content[:200] + "..." if len(doc_score.content) > 200 else doc_score.content,
                    "citation_id": doc_score.metadata.get("citation_id"),
                    "metadata": doc_score.metadata
                }
                results.append(result)

            message = f"两阶段检索完成（召回50个候选，重排序后返回{len(results)}个）"

        else:
            # 传统单阶段搜索
            search_results = await pgvector_store.search(
                query=query,
                top_k=limit,
                filter_metadata={"user_id": current_user.id},
                score_threshold=score_threshold
            )

            # 转换结果格式
            results = []
            for doc, score in search_results:
                result = {
                    "chunk_id": doc.id,
                    "document_id": doc.metadata.get("document_id"),
                    "content": doc.content,
                    "score": score,
                    "recall_score": score,
                    "rerank_score": None,
                    "source_url": doc.metadata.get("source_url"),
                    "filename": doc.metadata.get("filename"),
                    "snippet": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                    "citation_id": doc.metadata.get("citation_id"),
                    "metadata": doc.metadata
                }
                results.append(result)

            message = "传统向量搜索完成"

        # 同时记录到证据链
        if results:
            try:
                evidence_results = await pgvector_store.search_with_evidence(
                    query=query,
                    top_k=limit,
                    conversation_id=None,  # 可以从请求参数获取
                    research_session_id=None  # 可以从请求参数获取
                )
            except Exception as e:
                logger.warning(f"记录证据链失败: {e}")

        return {
            "query": query,
            "results": results,
            "total": len(results),
            "search_method": "two_stage_reranking" if use_reranking else "traditional",
            "message": message
        }

    except Exception as e:
        logger.error(f"搜索失败: {e}")

        # 如果两阶段检索失败，尝试回退到传统搜索
        try:
            search_results = await pgvector_store.search(
                query=query,
                top_k=limit,
                filter_metadata={"user_id": current_user.id},
                score_threshold=score_threshold
            )

            # 转换结果格式
            results = []
            for doc, score in search_results:
                result = {
                    "chunk_id": doc.id,
                    "document_id": doc.metadata.get("document_id"),
                    "content": doc.content,
                    "score": score,
                    "recall_score": score,
                    "rerank_score": None,
                    "source_url": doc.metadata.get("source_url"),
                    "filename": doc.metadata.get("filename"),
                    "snippet": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                    "citation_id": doc.metadata.get("citation_id"),
                    "metadata": doc.metadata
                }
                results.append(result)

            return {
                "query": query,
                "results": results,
                "total": len(results),
                "search_method": "fallback_traditional",
                "message": "回退到传统搜索方法完成"
            }

        except Exception as fallback_error:
            logger.error(f"搜索完全失败: 主方法-{str(e)}, 备用方法-{str(fallback_error)}")

            # 最后的回退选项
            try:
                from src.core.rag.retrieval import get_retriever

                retriever = get_retriever()
                search_results = retriever.search(
                    query=query,
                    top_k=limit,
                    filter_metadata={"user_id": str(current_user.id)}
                )

                results = []
                for doc in search_results.documents:
                    if doc.metadata.get("user_id") == current_user.id:
                        result = {
                            "chunk_id": doc.id,
                            "document_id": doc.metadata.get("original_doc_id"),
                            "content": doc.content,
                            "score": search_results.scores[len(results)],
                            "recall_score": search_results.scores[len(results)],
                            "rerank_score": None,
                            "source_url": doc.metadata.get("source"),
                            "filename": doc.metadata.get("source", "unknown"),
                            "snippet": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                            "citation_id": doc.metadata.get("citation_id", str(uuid.uuid4())),
                            "metadata": doc.metadata
                        }
                        results.append(result)

                return {
                    "query": query,
                    "results": results,
                    "total": len(results),
                    "search_method": "last_resort",
                    "message": "使用最后备用搜索方法完成"
                }

            except Exception as final_fallback_error:
                logger.error(f"所有搜索方法都失败: {final_fallback_error}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="搜索服务暂时不可用，请稍后重试"
                )


# ===== 新增：知识库管理 API =====

class KnowledgeBaseCreateReq(BaseModel):
    """创建知识库请求"""
    name: str
    description: Optional[str] = None

class KnowledgeBaseResp(BaseModel):
    """知识库响应"""
    name: str
    description: Optional[str] = None
    created_at: str
    file_count: int = 0

class KnowledgeBaseListResp(BaseModel):
    """知识库列表响应"""
    knowledge_bases: List[KnowledgeBaseResp]
    total: int

class FileUploadToKBReq(BaseModel):
    """文件上传到知识库请求"""
    kb_name: str

class FileUploadToKBResp(BaseModel):
    """文件上传到知识库响应"""
    message: str
    filename: str
    kb_name: str
    status: str

class KBSearchReq(BaseModel):
    """知识库搜索请求"""
    query: str
    kb_name: str
    top_k: int = 5

class KBSearchResp(BaseModel):
    """知识库搜索响应"""
    query: str
    kb_name: str
    results: List[dict]
    total: int


@router.get("/knowledge-bases", response_model=KnowledgeBaseListResp)
async def list_knowledge_bases(
    current_user: User = Depends(get_current_user)
):
    """
    获取用户的知识库列表
    """
    try:
        kb_names = KnowledgeBase.list_kbs()
        
        knowledge_bases = []
        for kb_name in kb_names:
            # 这里可以添加更多的知识库元数据获取逻辑
            kb_resp = KnowledgeBaseResp(
                name=kb_name,
                description=f"知识库 {kb_name}",
                created_at=datetime.utcnow().isoformat(),
                file_count=0  # 可以实现文件计数逻辑
            )
            knowledge_bases.append(kb_resp)
        
        return KnowledgeBaseListResp(
            knowledge_bases=knowledge_bases,
            total=len(knowledge_bases)
        )
        
    except Exception as e:
        logger.error(f"获取知识库列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取知识库列表失败"
        )


@router.post("/knowledge-bases", response_model=KnowledgeBaseResp)
async def create_knowledge_base(
    request: KnowledgeBaseCreateReq,
    current_user: User = Depends(get_current_user)
):
    """
    创建新的知识库
    """
    try:
        # 验证知识库名称
        if not KB_NAME_PATTERN.match(request.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="知识库名称只能包含英文字母和数字，长度3-20个字符"
            )
        
        # 检查知识库数量限制
        existing_kbs = KnowledgeBase.list_kbs()
        if len(existing_kbs) >= MAX_KBS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"知识库数量已达到上限 {MAX_KBS}"
            )
        
        # 检查知识库是否已存在
        if request.name in existing_kbs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"知识库 '{request.name}' 已存在"
            )
        
        # 创建知识库实例（这会自动创建ChromaDB集合）
        kb = KnowledgeBase(request.name)
        
        return KnowledgeBaseResp(
            name=request.name,
            description=request.description or f"知识库 {request.name}",
            created_at=datetime.utcnow().isoformat(),
            file_count=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建知识库失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建知识库失败"
        )


@router.delete("/knowledge-bases/{kb_name}")
async def delete_knowledge_base(
    kb_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    删除知识库
    """
    try:
        # 检查知识库是否存在
        existing_kbs = KnowledgeBase.list_kbs()
        if kb_name not in existing_kbs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"知识库 '{kb_name}' 不存在"
            )
        
        # 删除知识库
        KnowledgeBase.delete_kb(kb_name)
        
        # 清理文件
        await FileProcessor.cleanup_kb_files(kb_name)
        
        return {"message": f"知识库 '{kb_name}' 已成功删除"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除知识库失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除知识库失败"
        )


@router.post("/knowledge-bases/{kb_name}/upload", response_model=FileUploadToKBResp)
async def upload_file_to_knowledge_base(
    kb_name: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    上传文件到指定知识库
    """
    try:
        # 检查知识库是否存在
        existing_kbs = KnowledgeBase.list_kbs()
        if kb_name not in existing_kbs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"知识库 '{kb_name}' 不存在"
            )
        
        # 读取文件内容并检查大小
        file_bytes = await file.read()
        file_size = len(file_bytes)

        if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
            return create_error_response(
                code=ErrorCodes.VALIDATION_ERROR,
                message=f"文件大小超过限制：{MAX_FILE_SIZE_MB}MB",
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                details={"file_size": file_size, "max_size": MAX_FILE_SIZE_MB * 1024 * 1024}
            )
        
        # 处理文件并获取文本路径
        txt_path = await FileProcessor.save_and_process_file(
            file_bytes, file.filename, kb_name
        )
        
        # 添加到知识库
        kb = KnowledgeBase(kb_name)
        await kb.add_txt_file(txt_path, file.filename)
        
        return FileUploadToKBResp(
            message="文件上传并处理成功",
            filename=file.filename,
            kb_name=kb_name,
            status="completed"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传文件到知识库失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传文件失败: {str(e)}"
        )


@router.post("/knowledge-bases/{kb_name}/search", response_model=KBSearchResp)
async def search_knowledge_base(
    kb_name: str,
    request: KBSearchReq,
    current_user: User = Depends(get_current_user)
):
    """
    在指定知识库中搜索
    """
    try:
        # 检查知识库是否存在
        existing_kbs = KnowledgeBase.list_kbs()
        if kb_name not in existing_kbs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"知识库 '{kb_name}' 不存在"
            )
        
        # 执行搜索
        kb = KnowledgeBase(kb_name)
        query_result = kb.search(request.query, top_k=request.top_k)
        
        # 转换结果格式
        results = []
        for hit in query_result.hits:
            result = {
                "id": hit.id,
                "text": hit.text,
                "metadata": hit.metadata,
                "score": hit.score
            }
            results.append(result)
        
        return KBSearchResp(
            query=request.query,
            kb_name=kb_name,
            results=results,
            total=len(results)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索知识库失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="搜索知识库失败"
        )
