# -*- coding: utf-8 -*-
"""
文件上传 API
提供文件上传、处理和管理功能
"""

import logging
import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from .deps import require_auth
from ..sqlmodel.models import User
from ..core.db import get_async_session
from ..services.ocr_service import get_ocr_service
from ..config.config_loader import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/files", tags=["files"])


# ==================== 请求/响应模型 ====================

class FileUploadResponse(BaseModel):
    """文件上传响应"""
    file_id: str
    filename: str
    file_path: str
    file_size: int
    file_type: str
    status: str
    message: str


class FileProcessResponse(BaseModel):
    """文件处理响应"""
    file_id: str
    status: str
    extracted_text: Optional[str] = None
    error: Optional[str] = None


# ==================== 辅助函数 ====================

def get_upload_path(user_id: str, filename: str) -> Path:
    """
    获取文件上传路径
    
    Args:
        user_id: 用户ID
        filename: 文件名
    
    Returns:
        文件路径
    """
    # 创建用户专属目录
    user_dir = Path(settings.upload_dir) / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成唯一文件名
    file_ext = Path(filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    
    return user_dir / unique_filename


async def process_file_background(file_path: str, file_id: str, user_id: str):
    """
    后台处理文件
    
    Args:
        file_path: 文件路径
        file_id: 文件ID
        user_id: 用户ID
    """
    try:
        logger.info(f"开始处理文件: {file_path}")
        
        # 使用 OCR 服务提取文本
        ocr_service = get_ocr_service()
        result = await ocr_service.process_document(file_path)
        
        if result["success"]:
            # TODO: 存储到 RAG 系统
            # TODO: 更新数据库记录
            logger.info(f"文件处理成功: {file_id}")
        else:
            logger.error(f"文件处理失败: {result.get('error')}")
    
    except Exception as e:
        logger.error(f"后台处理文件失败: {e}", exc_info=True)


# ==================== API 端点 ====================

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(require_auth),
    session: AsyncSession = Depends(get_async_session)
):
    """
    上传文件
    
    支持的格式：PDF, PPT, PPTX, DOC, DOCX, TXT, MD
    """
    try:
        logger.info(f"用户 {current_user.id} 上传文件: {file.filename}")
        
        # 检查文件类型
        file_ext = Path(file.filename).suffix.lower()
        allowed_types = settings.allowed_file_types.split(',')
        
        if file_ext not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file_ext}。支持的类型: {', '.join(allowed_types)}"
            )
        
        # 读取文件内容
        content = await file.read()
        file_size = len(content)
        
        # 检查文件大小
        if file_size > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"文件过大。最大允许: {settings.max_file_size / 1024 / 1024:.1f}MB"
            )
        
        # 保存文件
        file_path = get_upload_path(str(current_user.id), file.filename)
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # 生成文件ID
        file_id = str(uuid.uuid4())
        
        # 创建数据库记录
        from ..sqlmodel.models import DocumentProcessingJob
        
        job = DocumentProcessingJob(
            id=file_id,
            user_id=current_user.id,
            filename=file.filename,
            file_path=str(file_path),
            status="pending"
        )
        
        session.add(job)
        await session.commit()
        
        # 添加后台处理任务
        background_tasks.add_task(
            process_file_background,
            str(file_path),
            file_id,
            str(current_user.id)
        )
        
        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            file_type=file_ext,
            status="processing",
            message="文件上传成功，正在处理中"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.get("/{file_id}/status", response_model=FileProcessResponse)
async def get_file_status(
    file_id: str,
    current_user: User = Depends(require_auth),
    session: AsyncSession = Depends(get_async_session)
):
    """获取文件处理状态"""
    try:
        from ..sqlmodel.models import DocumentProcessingJob
        from sqlalchemy import select
        
        # 查询文件记录
        result = await session.execute(
            select(DocumentProcessingJob).where(
                DocumentProcessingJob.id == file_id,
                DocumentProcessingJob.user_id == current_user.id
            )
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileProcessResponse(
            file_id=file_id,
            status=job.status,
            extracted_text=job.extracted_text if hasattr(job, 'extracted_text') else None,
            error=job.error_message
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_user_files(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_auth),
    session: AsyncSession = Depends(get_async_session)
):
    """获取用户的文件列表"""
    try:
        from ..sqlmodel.models import DocumentProcessingJob
        from sqlalchemy import select
        
        # 查询用户的文件
        query = select(DocumentProcessingJob).where(
            DocumentProcessingJob.user_id == current_user.id
        ).order_by(DocumentProcessingJob.created_at.desc()).offset(skip).limit(limit)
        
        result = await session.execute(query)
        jobs = result.scalars().all()
        
        return {
            "total": len(jobs),
            "files": [
                {
                    "file_id": str(job.id),
                    "filename": job.filename,
                    "status": job.status,
                    "created_at": job.created_at.isoformat(),
                    "updated_at": job.updated_at.isoformat() if job.updated_at else None
                }
                for job in jobs
            ]
        }
    
    except Exception as e:
        logger.error(f"获取文件列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(require_auth),
    session: AsyncSession = Depends(get_async_session)
):
    """删除文件"""
    try:
        from ..sqlmodel.models import DocumentProcessingJob
        from sqlalchemy import select
        
        # 查询文件记录
        result = await session.execute(
            select(DocumentProcessingJob).where(
                DocumentProcessingJob.id == file_id,
                DocumentProcessingJob.user_id == current_user.id
            )
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 删除物理文件
        if job.file_path and os.path.exists(job.file_path):
            os.remove(job.file_path)
        
        # 删除数据库记录
        await session.delete(job)
        await session.commit()
        
        return {
            "success": True,
            "message": "文件已删除"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件失败: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
