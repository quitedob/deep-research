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
from ..services.document_service import DocumentService
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
    上传文件 - 通过DocumentService处理业务逻辑

    支持的格式：PDF, PPT, PPTX, DOC, DOCX, TXT, MD
    """
    try:
        document_service = DocumentService(session)

        logger.info(f"用户 {current_user.id} 上传文件: {file.filename}")

        # 读取文件内容
        content = await file.read()

        # 通过服务层上传文档
        result = await document_service.upload_document(
            user_id=str(current_user.id),
            filename=file.filename,
            file_content=content
        )

        if not result.get("success"):
            error_type = result.get("error_type", "upload_failed")
            if error_type == "validation_failed":
                raise HTTPException(
                    status_code=400,
                    detail=result.get("error", "文件验证失败")
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=result.get("error", "文件上传失败")
                )

        # 添加后台处理任务
        background_tasks.add_task(
            process_file_background,
            result.get("file_path"),  # 使用服务层返回的文件路径
            str(result.get("job_id")),
            str(current_user.id)
        )

        return FileUploadResponse(
            file_id=str(result.get("job_id")),
            filename=file.filename,
            file_path=result.get("file_path", ""),
            file_size=result.get("file_size", len(content)),
            file_type=Path(file.filename).suffix.lower(),
            status=result.get("status", "pending"),
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
    """获取文件处理状态 - 通过DocumentService处理业务逻辑"""
    try:
        document_service = DocumentService(session)

        # 通过服务层获取文档状态
        job_info = await document_service.get_document_status(
            user_id=str(current_user.id),
            job_id=int(file_id)
        )

        if not job_info:
            raise HTTPException(status_code=404, detail="文件不存在")

        return FileProcessResponse(
            file_id=file_id,
            status=job_info.get("status"),
            extracted_text=job_info.get("result", {}).get("extracted_text") if job_info.get("result") else None,
            error=job_info.get("error_message")
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
    """获取用户的文件列表 - 通过DocumentService处理业务逻辑"""
    try:
        document_service = DocumentService(session)

        # 通过服务层获取用户文档列表
        result = await document_service.get_user_documents(
            user_id=str(current_user.id),
            skip=skip,
            limit=limit
        )

        documents = result.get("documents", [])

        return {
            "total": result.get("total", len(documents)),
            "files": [
                {
                    "file_id": str(doc.get("job_id")),
                    "filename": doc.get("filename"),
                    "status": doc.get("status"),
                    "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
                    "updated_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,  # 简化处理
                    "progress": doc.get("progress"),
                    "error_message": doc.get("error_message")
                }
                for doc in documents
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
    """删除文件 - 通过DocumentService处理业务逻辑"""
    try:
        document_service = DocumentService(session)

        # 通过服务层删除文档
        result = await document_service.delete_document(
            user_id=str(current_user.id),
            job_id=int(file_id)
        )

        if not result.get("success"):
            error_message = result.get("error", "删除文件失败")
            if "不存在或无权限访问" in error_message:
                raise HTTPException(status_code=404, detail="文件不存在")
            else:
                raise HTTPException(status_code=500, detail=error_message)

        return {
            "success": True,
            "message": result.get("message", "文件已删除")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
