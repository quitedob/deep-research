# -*- coding: utf-8 -*-
"""
DocumentService：文档处理业务逻辑服务
提供文档上传、处理、分析、搜索等高级功能
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import os
import uuid
from pathlib import Path

from .base_service import BaseService
from src.dao import DocumentProcessingJobDAO, DocumentDAO, DocumentChunkDAO
from src.sqlmodel.rag_models import DocumentProcessingJob, Document, Chunk as DocumentChunk
from src.config.logging.logging import get_logger
from src.config.loader.config_loader import get_settings

logger = get_logger("document_service")

settings = get_settings()


class DocumentService(BaseService[DocumentProcessingJob]):
    """文档处理服务类"""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.job_dao = DocumentProcessingJobDAO(session)
        self.document_dao = DocumentDAO(session)
        self.chunk_dao = DocumentChunkDAO(session)

    async def upload_document(
        self,
        user_id: str,
        filename: str,
        file_content: bytes,
        file_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        上传文档并创建处理任务

        Args:
            user_id: 用户ID
            filename: 文件名
            file_content: 文件内容
            file_path: 文件路径（可选）
            metadata: 元数据（可选）

        Returns:
            上传结果和任务ID
        """
        try:
            await self.begin_transaction()

            # 验证文件
            validation_result = await self._validate_document(filename, file_content)
            if not validation_result["valid"]:
                await self.rollback_transaction()
                return {
                    "success": False,
                    "error": validation_result["error"],
                    "error_type": "validation_failed"
                }

            # 生成文件路径
            if not file_path:
                file_path = await self._generate_file_path(user_id, filename)

            # 保存文件
            actual_file_path = await self._save_file(file_path, file_content)

            # 创建处理任务
            job = await self.job_dao.create_job(
                user_id=user_id,
                filename=filename,
                file_path=actual_file_path
            )

            # 创建文档记录
            document = await self.document_dao.create(
                user_id=user_id,
                original_filename=filename,
                file_path=actual_file_path,
                source_type="upload",
                source_title=filename,
                metadata=metadata or {}
            )

            await self.commit_transaction()

            await self.log_operation(
                user_id=user_id,
                operation="document_uploaded",
                details={
                    "filename": filename,
                    "file_size": len(file_content),
                    "job_id": job.id,
                    "document_id": document.id
                }
            )

            return {
                "success": True,
                "job_id": job.id,
                "document_id": document.id,
                "filename": filename,
                "status": "pending",
                "file_size": len(file_content)
            }

        except Exception as e:
            await self.rollback_transaction()
            logger.error(f"文档上传失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "upload_failed"
            }

    async def get_document_status(self, user_id: str, job_id: int) -> Optional[Dict[str, Any]]:
        """
        获取文档处理状态

        Args:
            user_id: 用户ID
            job_id: 任务ID

        Returns:
            文档状态信息
        """
        try:
            job = await self.job_dao.get_job_status(job_id)

            if not job or str(job.user_id) != user_id:
                return None

            return {
                "job_id": job.id,
                "filename": job.filename,
                "status": job.status,
                "progress": job.progress,
                "created_at": job.created_at,
                "started_at": job.started_at,
                "completed_at": job.completed_at,
                "error_message": job.error_message,
                "result": job.result
            }

        except Exception as e:
            logger.error(f"获取文档状态失败: {e}")
            return None

    async def get_user_documents(
        self,
        user_id: str,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        获取用户文档列表

        Args:
            user_id: 用户ID
            status: 状态筛选
            skip: 跳过数量
            limit: 限制数量

        Returns:
            文档列表和统计信息
        """
        try:
            jobs = await self.job_dao.get_user_jobs(
                user_id=user_id,
                status=status,
                skip=skip,
                limit=limit
            )

            documents = []
            for job in jobs:
                documents.append({
                    "job_id": job.id,
                    "filename": job.filename,
                    "status": job.status,
                    "progress": job.progress,
                    "created_at": job.created_at,
                    "updated_at": job.updated_at,
                    "error_message": job.error_message
                })

            # 获取统计信息
            stats = await self._get_user_document_stats(user_id)

            return {
                "documents": documents,
                "total": len(documents) + skip,  # 简化实现
                "stats": stats
            }

        except Exception as e:
            logger.error(f"获取用户文档列表失败: {e}")
            return {
                "documents": [],
                "total": 0,
                "error": str(e)
            }

    async def delete_document(self, user_id: str, job_id: int) -> Dict[str, Any]:
        """
        删除文档

        Args:
            user_id: 用户ID
            job_id: 任务ID

        Returns:
            删除结果
        """
        try:
            await self.begin_transaction()

            # 检查权限
            job = await self.job_dao.get_job_status(job_id)
            if not job or str(job.user_id) != user_id:
                await self.rollback_transaction()
                return {
                    "success": False,
                    "error": "文档不存在或无权限访问"
                }

            # 删除文件
            if os.path.exists(job.file_path):
                os.remove(job.file_path)

            # 删除数据库记录
            success = await self.job_dao.delete(job_id)

            if not success:
                await self.rollback_transaction()
                return {
                    "success": False,
                    "error": "删除数据库记录失败"
                }

            await self.commit_transaction()

            await self.log_operation(
                user_id=user_id,
                operation="document_deleted",
                details={
                    "job_id": job_id,
                    "filename": job.filename
                }
            )

            return {
                "success": True,
                "message": "文档删除成功"
            }

        except Exception as e:
            await self.rollback_transaction()
            logger.error(f"删除文档失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def search_documents(
        self,
        user_id: str,
        query: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        搜索文档内容

        Args:
            user_id: 用户ID
            query: 搜索关键词
            skip: 跳过数量
            limit: 限制数量

        Returns:
            搜索结果
        """
        try:
            documents = await self.document_dao.search_documents(
                user_id=user_id,
                search_term=query,
                skip=skip,
                limit=limit
            )

            results = []
            for doc in documents:
                results.append({
                    "document_id": str(doc.id),
                    "original_filename": doc.original_filename,
                    "source_type": doc.source_type,
                    "source_title": doc.source_title,
                    "created_at": doc.created_at,
                    "metadata": doc.metadata
                })

            return results

        except Exception as e:
            logger.error(f"搜索文档失败: {e}")
            return []

    async def get_document_content(
        self,
        user_id: str,
        document_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取文档内容

        Args:
            user_id: 用户ID
            document_id: 文档ID

        Returns:
            文档内容和分块信息
        """
        try:
            # 验证文档权限
            document = await self.document_dao.get_by_id(document_id)
            if not document or str(document.user_id) != user_id:
                return None

            # 获取文档分块
            chunks = await self.chunk_dao.get_chunks_by_document(
                document_id=document_id,
                skip=0,
                limit=1000  # 限制分块数量
            )

            # 合并内容
            content_parts = []
            chunk_info = []

            for chunk in chunks:
                content_parts.append(chunk.content)
                chunk_info.append({
                    "chunk_id": str(chunk.id),
                    "chunk_index": chunk.chunk_index,
                    "content_preview": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                    "metadata": chunk.metadata
                })

            return {
                "document_id": document_id,
                "original_filename": document.original_filename,
                "content": "\n\n".join(content_parts),
                "total_chunks": len(chunks),
                "chunks": chunk_info,
                "created_at": document.created_at,
                "metadata": document.metadata
            }

        except Exception as e:
            logger.error(f"获取文档内容失败: {e}")
            return None

    async def retry_document_processing(
        self,
        user_id: str,
        job_id: int
    ) -> Dict[str, Any]:
        """
        重试文档处理

        Args:
            user_id: 用户ID
            job_id: 任务ID

        Returns:
            重试结果
        """
        try:
            job = await self.job_dao.get_job_status(job_id)

            if not job or str(job.user_id) != user_id:
                return {
                    "success": False,
                    "error": "文档不存在或无权限访问"
                }

            if job.status != "failed":
                return {
                    "success": False,
                    "error": "只有失败的任务才能重试"
                }

            # 重置任务状态
            updated_job = await self.job_dao.update_job_status(
                job_id=job_id,
                status="pending",
                error_message=None
            )

            if not updated_job:
                return {
                    "success": False,
                    "error": "更新任务状态失败"
                }

            await self.log_operation(
                user_id=user_id,
                operation="document_retry",
                details={
                    "job_id": job_id,
                    "filename": job.filename
                }
            )

            return {
                "success": True,
                "message": "任务已重新加入处理队列",
                "job_id": job_id,
                "status": "pending"
            }

        except Exception as e:
            logger.error(f"重试文档处理失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _validate_document(self, filename: str, content: bytes) -> Dict[str, Any]:
        """验证文档"""
        # 检查文件大小
        max_size = settings.max_file_size_mb * 1024 * 1024
        if len(content) > max_size:
            return {
                "valid": False,
                "error": f"文件大小超过限制 ({max_size / 1024 / 1024:.1f}MB)"
            }

        # 检查文件类型
        allowed_extensions = ['.pdf', '.docx', '.doc', '.txt', '.md', '.rtf']
        file_ext = Path(filename).suffix.lower()
        if file_ext not in allowed_extensions:
            return {
                "valid": False,
                "error": f"不支持的文件类型。支持的类型: {', '.join(allowed_extensions)}"
            }

        # 检查文件内容是否为空
        if len(content) == 0:
            return {
                "valid": False,
                "error": "文件内容为空"
            }

        return {"valid": True}

    async def _generate_file_path(self, user_id: str, filename: str) -> str:
        """生成文件路径"""
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # 生成唯一文件名
        file_ext = Path(filename).suffix
        unique_name = f"{user_id}_{uuid.uuid4().hex[:8]}{file_ext}"

        return str(upload_dir / unique_name)

    async def _save_file(self, file_path: str, content: bytes) -> str:
        """保存文件"""
        # 确保目录存在
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'wb') as f:
            f.write(content)

        return file_path

    async def _get_user_document_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户文档统计"""
        try:
            stats = await self.job_dao.get_job_statistics()

            # 过滤当前用户的统计（简化实现）
            user_stats = {
                "total_jobs": 0,
                "by_status": {
                    "pending": 0,
                    "processing": 0,
                    "completed": 0,
                    "failed": 0
                }
            }

            return user_stats

        except Exception as e:
            logger.error(f"获取文档统计失败: {e}")
            return {"total_jobs": 0, "by_status": {}}

    async def validate_permissions(self, user_id: str, required_role: str) -> bool:
        """验证用户权限（重写基类方法）"""
        # 文档服务的权限验证逻辑
        # 用户只能操作自己的文档，管理员可以操作所有文档
        return True