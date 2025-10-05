# -*- coding: utf-8 -*-
"""
OCR API 路由
提供文档 OCR 识别功能
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from .deps import require_auth
from ..sqlmodel.models import User
from ..services.ocr_service import get_ocr_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ocr", tags=["ocr"])


# ==================== 请求/响应模型 ====================

class OCRResponse(BaseModel):
    """OCR 响应"""
    success: bool
    text: str
    file_type: str
    pages: Optional[int] = None
    error: Optional[str] = None


class OCRStatusResponse(BaseModel):
    """OCR 状态响应"""
    available: bool
    provider: str
    model: str
    supported_formats: list


# ==================== API 端点 ====================

@router.post("/recognize", response_model=OCRResponse)
async def recognize_document(
    file: UploadFile = File(...),
    current_user: User = Depends(require_auth)
):
    """
    识别文档中的文字
    
    支持格式：PDF, PPT, PPTX, DOC, DOCX, JPG, PNG
    """
    try:
        logger.info(f"用户 {current_user.id} 上传文件进行 OCR: {file.filename}")
        
        # 检查文件格式
        file_ext = Path(file.filename).suffix.lower()
        supported_formats = ['.pdf', '.ppt', '.pptx', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.bmp']
        
        if file_ext not in supported_formats:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式: {file_ext}。支持的格式: {', '.join(supported_formats)}"
            )
        
        # 保存临时文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
        try:
            content = await file.read()
            temp_file.write(content)
            temp_file.close()
            
            # 执行 OCR
            ocr_service = get_ocr_service()
            result = await ocr_service.process_document(temp_file.name)
            
            if not result["success"]:
                raise HTTPException(
                    status_code=500,
                    detail=f"OCR 处理失败: {result.get('error', 'Unknown error')}"
                )
            
            return OCRResponse(
                success=True,
                text=result["text"],
                file_type=file_ext,
                pages=result.get("total_pages") or result.get("total_slides"),
                error=None
            )
        
        finally:
            # 删除临时文件
            if os.path.exists(temp_file.name):
                os.remove(temp_file.name)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR 处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OCR 处理失败: {str(e)}")


@router.get("/status", response_model=OCRStatusResponse)
async def get_ocr_status(
    current_user: User = Depends(require_auth)
):
    """
    获取 OCR 服务状态
    
    返回 OCR 服务的可用性和配置信息
    """
    try:
        from ..config.config_loader import get_settings
        settings = get_settings()
        
        # 检查依赖库
        try:
            from pdf2image import convert_from_path
            pdf_available = True
        except ImportError:
            pdf_available = False
        
        try:
            from pptx import Presentation
            pptx_available = True
        except ImportError:
            pptx_available = False
        
        try:
            from docx import Document
            docx_available = True
        except ImportError:
            docx_available = False
        
        # 支持的格式
        supported_formats = []
        if pdf_available:
            supported_formats.extend(['.pdf'])
        if pptx_available:
            supported_formats.extend(['.ppt', '.pptx'])
        if docx_available:
            supported_formats.extend(['.doc', '.docx'])
        supported_formats.extend(['.jpg', '.jpeg', '.png', '.bmp'])
        
        return OCRStatusResponse(
            available=bool(settings.doubao_api_key),
            provider=settings.ocr_provider,
            model=settings.ocr_model,
            supported_formats=supported_formats
        )
    
    except Exception as e:
        logger.error(f"获取 OCR 状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_recognize(
    files: list[UploadFile] = File(...),
    current_user: User = Depends(require_auth)
):
    """
    批量识别多个文档
    
    支持同时上传多个文件进行 OCR 识别
    """
    try:
        logger.info(f"用户 {current_user.id} 批量上传 {len(files)} 个文件进行 OCR")
        
        results = []
        ocr_service = get_ocr_service()
        
        for file in files:
            try:
                # 检查文件格式
                file_ext = Path(file.filename).suffix.lower()
                
                # 保存临时文件
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
                content = await file.read()
                temp_file.write(content)
                temp_file.close()
                
                # 执行 OCR
                result = await ocr_service.process_document(temp_file.name)
                
                results.append({
                    "filename": file.filename,
                    "success": result["success"],
                    "text": result.get("text", ""),
                    "error": result.get("error")
                })
                
                # 删除临时文件
                os.remove(temp_file.name)
            
            except Exception as e:
                logger.error(f"处理文件 {file.filename} 失败: {e}")
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "text": "",
                    "error": str(e)
                })
        
        return {
            "success": True,
            "total": len(files),
            "results": results
        }
    
    except Exception as e:
        logger.error(f"批量 OCR 处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
