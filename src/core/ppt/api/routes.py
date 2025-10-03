# -*- coding: utf-8 -*-
"""
PPT API路由

提供PPT生成、文件上传、编辑等API端点。
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel, Field

from src.api.deps import require_auth
from src.core.ppt.generator import create_presentation
from src.sqlmodel.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ppt", tags=["ppt"])


# ==================== 请求/响应模型 ====================

class PresentationCreateRequest(BaseModel):
    """创建演示文稿请求"""
    title: str = Field(..., description="演示文稿标题")
    topic: Optional[str] = Field(None, description="主题（如果没有outline）")
    outline: Optional[List[str]] = Field(None, description="大纲列表")
    n_slides: int = Field(10, ge=3, le=50, description="幻灯片数量")
    language: str = Field("Chinese", description="语言")
    tone: str = Field("professional", description="语气")
    template: Optional[str] = Field(None, description="模板名称")


class PresentationResponse(BaseModel):
    """演示文稿响应"""
    presentation_id: str
    path: str
    edit_path: str
    title: str
    slides_count: int
    created_at: str


class SlideEditRequest(BaseModel):
    """幻灯片编辑请求"""
    slide_id: int = Field(..., description="幻灯片ID")
    prompt: str = Field(..., description="编辑提示")


class FileUploadResponse(BaseModel):
    """文件上传响应"""
    file_id: str
    filename: str
    status: str
    message: str


# ==================== API端点 ====================

@router.post("/presentation/create", response_model=PresentationResponse)
async def create_presentation_endpoint(
    request: PresentationCreateRequest,
    current_user: User = Depends(require_auth)
):
    """
    创建演示文稿

    根据标题、大纲或主题生成完整的PPT文件。
    """
    try:
        logger.info(f"用户 {current_user.id} 请求创建PPT: {request.title}")

        # 构建参数
        params = {
            "title": request.title,
            "n_slides": request.n_slides,
            "language": request.language,
            "tone": request.tone
        }

        if request.outline:
            params["outline"] = request.outline
        elif request.topic:
            params["topic"] = request.topic
        else:
            params["topic"] = request.title

        if request.template:
            params["template"] = request.template

        # 生成PPT
        result = await create_presentation(params)

        return PresentationResponse(**result)

    except Exception as e:
        logger.error(f"创建PPT失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建PPT失败: {str(e)}")


@router.post("/files/upload", response_model=FileUploadResponse)
async def upload_file_endpoint(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(require_auth)
):
    """
    上传文件用于PPT生成

    支持上传文档、PDF等文件，系统会提取内容用于增强PPT生成。
    """
    try:
        logger.info(f"用户 {current_user.id} 上传文件: {file.filename}")

        # TODO: 实现文件上传和处理逻辑
        # 1. 保存文件
        # 2. 提取内容
        # 3. 存储到RAG系统

        file_id = "temp_file_id"

        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            status="processing",
            message="文件上传成功，正在处理中"
        )

    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.post("/files/decompose")
async def decompose_file_endpoint(
    file_id: str,
    current_user: User = Depends(require_auth)
):
    """
    分解文件内容

    将上传的文件分解为可用于PPT生成的结构化内容。
    """
    try:
        logger.info(f"用户 {current_user.id} 请求分解文件: {file_id}")

        # TODO: 实现文件分解逻辑
        # 1. 读取文件
        # 2. OCR/文本提取
        # 3. 结构化处理
        # 4. 返回分解结果

        return {
            "file_id": file_id,
            "status": "completed",
            "sections": [],
            "message": "文件分解完成"
        }

    except Exception as e:
        logger.error(f"文件分解失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"文件分解失败: {str(e)}")


@router.post("/slide/edit")
async def edit_slide_endpoint(
    request: SlideEditRequest,
    current_user: User = Depends(require_auth)
):
    """
    编辑单个幻灯片

    根据提示重新生成指定幻灯片的内容。
    """
    try:
        logger.info(f"用户 {current_user.id} 请求编辑幻灯片: {request.slide_id}")

        # TODO: 实现幻灯片编辑逻辑
        # 1. 获取原幻灯片内容
        # 2. 根据prompt重新生成
        # 3. 更新幻灯片
        # 4. 返回新内容

        return {
            "slide_id": request.slide_id,
            "status": "updated",
            "content": "更新后的内容",
            "message": "幻灯片更新成功"
        }

    except Exception as e:
        logger.error(f"编辑幻灯片失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"编辑幻灯片失败: {str(e)}")


@router.get("/presentation/{presentation_id}")
async def get_presentation_endpoint(
    presentation_id: str,
    current_user: User = Depends(require_auth)
):
    """
    获取演示文稿信息

    返回指定演示文稿的详细信息。
    """
    try:
        logger.info(f"用户 {current_user.id} 请求获取PPT: {presentation_id}")

        # TODO: 实现获取PPT信息逻辑
        # 1. 从数据库查询
        # 2. 返回详细信息

        return {
            "presentation_id": presentation_id,
            "title": "示例演示文稿",
            "status": "completed",
            "slides_count": 10,
            "created_at": "2025-01-01T00:00:00"
        }

    except Exception as e:
        logger.error(f"获取PPT信息失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取PPT信息失败: {str(e)}")


@router.get("/health")
async def health_check():
    """
    健康检查

    检查PPT生成服务的健康状态。
    """
    try:
        from src.core.ppt.adapters.deepseek_adapter import DeepSeekAdapter
        from src.core.ppt.adapters.ollama_adapter import OllamaAdapter

        deepseek = DeepSeekAdapter()
        ollama = OllamaAdapter()

        deepseek_health = await deepseek.health_check()
        ollama_health = await ollama.health_check()

        return {
            "status": "healthy",
            "providers": {
                "deepseek": {
                    "healthy": deepseek_health[0],
                    "message": deepseek_health[1]
                },
                "ollama": {
                    "healthy": ollama_health[0],
                    "message": ollama_health[1]
                }
            }
        }

    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
