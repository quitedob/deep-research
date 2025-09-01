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

from pkg.db import get_db_session
from src.sqlmodel.models import User, DocumentProcessingJob
from src.service.auth import get_current_user
from src.tasks.queue import enqueue_task, get_task_status, TaskPriority
from src.tasks.document_processor import process_document_task
from src.config.settings import get_settings

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
    try:
        # 检查文件大小
        if file.size > settings.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件大小超过限制：{settings.max_file_size} 字节"
            )
        
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
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档上传失败：{str(e)}"
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
        # 查询任务记录
        result = await db.execute(
            "SELECT * FROM document_processing_jobs WHERE id = :job_id AND user_id = :user_id",
            {"job_id": job_id, "user_id": current_user.id}
        )
        job_data = result.fetchone()
        
        if not job_data:
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
            result=None  # TODO: 从任务队列获取结果
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档状态失败：{str(e)}"
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
        
        # 查询总数
        count_result = await db.execute(
            "SELECT COUNT(*) FROM document_processing_jobs WHERE user_id = :user_id",
            {"user_id": current_user.id}
        )
        total = count_result.scalar()
        
        # 查询文档列表
        result = await db.execute(
            """
            SELECT * FROM document_processing_jobs 
            WHERE user_id = :user_id 
            ORDER BY created_at DESC 
            LIMIT :limit OFFSET :offset
            """,
            {"user_id": current_user.id, "limit": page_size, "offset": offset}
        )
        
        documents = []
        for row in result.fetchall():
            documents.append(DocumentStatusResp(
                job_id=str(row.id),
                status=row.status,
                filename=row.filename,
                created_at=row.created_at.isoformat(),
                started_at=row.started_at.isoformat() if row.started_at else None,
                completed_at=row.completed_at.isoformat() if row.completed_at else None,
                error_message=row.error_message,
                result=None
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
        # 查询任务记录
        result = await db.execute(
            "SELECT * FROM document_processing_jobs WHERE id = :job_id AND user_id = :user_id",
            {"job_id": job_id, "user_id": current_user.id}
        )
        job_data = result.fetchone()
        
        if not job_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档处理任务不存在或无权限访问"
            )
        
        # 删除文件
        if os.path.exists(job_data.file_path):
            os.remove(job_data.file_path)
        
        # 删除数据库记录
        await db.execute(
            "DELETE FROM document_processing_jobs WHERE id = :job_id",
            {"job_id": job_id}
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    重试失败的文档处理任务
    """
    try:
        # 查询任务记录
        result = await db.execute(
            "SELECT * FROM document_processing_jobs WHERE id = :job_id AND user_id = :user_id",
            {"job_id": job_id, "user_id": current_user.id}
        )
        job_data = result.fetchone()
        
        if not job_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档处理任务不存在或无权限访问"
            )
        
        if job_data.status != "failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只有失败的任务才能重试"
            )
        
        # 更新任务状态为待处理
        await db.execute(
            "UPDATE document_processing_jobs SET status = 'pending', error_message = NULL WHERE id = :job_id",
            {"job_id": job_id}
        )
        await db.commit()
        
        # 重新加入处理队列
        background_tasks = BackgroundTasks()
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
    score_threshold: float = 0.0
):
    """
    在用户的文档中进行语义搜索
    """
    try:
        from src.rag.pgvector_store import get_pgvector_store
        from src.api.evidence import EvidenceResponse

        # 获取pgvector存储实例
        pgvector_store = get_pgvector_store()

        # 执行向量搜索
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
                "source_url": doc.metadata.get("source_url"),
                "filename": doc.metadata.get("filename"),
                "snippet": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                "citation_id": doc.metadata.get("citation_id"),
                "metadata": doc.metadata
            }
            results.append(result)

        # 同时记录到证据链
        if results:
            evidence_results = await pgvector_store.search_with_evidence(
                query=query,
                top_k=limit,
                conversation_id=None,  # 可以从请求参数获取
                research_session_id=None  # 可以从请求参数获取
            )

        return {
            "query": query,
            "results": results,
            "total": len(results),
            "message": "向量搜索完成"
        }

    except Exception as e:
        # 如果pgvector搜索失败，尝试回退到其他搜索方法
        try:
            from src.rag.retriever import create_default_retriever

            retriever = create_default_retriever()
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
                "message": "使用备用搜索方法完成"
            }

        except Exception as fallback_error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"搜索失败：{str(e)}，备用方法也失败：{str(fallback_error)}"
            )
