# -*- coding: utf-8 -*-
"""
DocumentProcessingJobDAO: Document processing job data access operations.
Provides high-level methods for document job management and status tracking.
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.sqlmodel.rag_models import DocumentProcessingJob, Document, Chunk as DocumentChunk
from .base import BaseRepository, FilterBuilder


class DocumentProcessingJobDAO(BaseRepository[DocumentProcessingJob]):
    """Data access object for document processing job operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, DocumentProcessingJob)

    async def create_job(
        self,
        user_id: Optional[str],
        filename: str,
        file_path: str
    ) -> DocumentProcessingJob:
        """Create a new document processing job."""
        job = DocumentProcessingJob(
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            status="pending",
            progress=0.0
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def get_job_status(self, job_id: int) -> Optional[DocumentProcessingJob]:
        """Get job status by ID."""
        return await self.get_by_id(job_id)

    async def get_job_by_user_and_filename(
        self,
        user_id: str,
        filename: str
    ) -> Optional[DocumentProcessingJob]:
        """Get a job by user and filename."""
        result = await self.session.execute(
            select(DocumentProcessingJob).where(
                and_(
                    DocumentProcessingJob.user_id == user_id,
                    DocumentProcessingJob.filename == filename
                )
            ).order_by(DocumentProcessingJob.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def update_job_status(
        self,
        job_id: int,
        status: str,
        progress: Optional[float] = None,
        error_message: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None
    ) -> Optional[DocumentProcessingJob]:
        """Update job status and progress."""
        job = await self.get_by_id(job_id)
        if not job:
            return None

        job.status = status

        if progress is not None:
            job.progress = progress

        if error_message is not None:
            job.error_message = error_message

        if result is not None:
            job.result = result

        # Update timestamps based on status
        now = datetime.utcnow()
        if status == "processing" and not job.started_at:
            job.started_at = now
        elif status in ["completed", "failed", "indexed"]:
            job.completed_at = now

        job.updated_at = now

        await self.session.flush()
        return job

    async def get_user_jobs(
        self,
        user_id: str,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[DocumentProcessingJob]:
        """Get all jobs for a specific user with optional status filter."""
        query = select(DocumentProcessingJob).where(
            DocumentProcessingJob.user_id == user_id
        )

        if status:
            query = query.where(DocumentProcessingJob.status == status)

        query = query.order_by(DocumentProcessingJob.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_jobs_by_status(
        self,
        status: str,
        limit: int = 100
    ) -> List[DocumentProcessingJob]:
        """Get jobs by status (useful for job queue processing)."""
        query = select(DocumentProcessingJob).where(
            DocumentProcessingJob.status == status
        ).order_by(DocumentProcessingJob.created_at.asc()).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_job_statistics(self) -> Dict[str, Any]:
        """Get comprehensive job statistics."""
        stats = {}

        # Total jobs
        total_result = await self.session.execute(
            select(func.count(DocumentProcessingJob.id))
        )
        stats["total_jobs"] = total_result.scalar()

        # Jobs by status
        status_query = select(
            DocumentProcessingJob.status,
            func.count(DocumentProcessingJob.id).label('count')
        ).group_by(DocumentProcessingJob.status)

        status_result = await self.session.execute(status_query)
        status_stats = status_result.fetchall()

        stats["by_status"] = {
            row.status: row.count for row in status_stats
        }

        # Average processing time for completed jobs
        avg_time_query = select(
            func.avg(
                func.timestampdiff(
                    text('SECOND'),
                    DocumentProcessingJob.started_at,
                    DocumentProcessingJob.completed_at
                )
            )
        ).where(
            and_(
                DocumentProcessingJob.status == "completed",
                DocumentProcessingJob.started_at.isnot(None),
                DocumentProcessingJob.completed_at.isnot(None)
            )
        )

        # Note: timestampdiff function may not be available in all databases
        # This is a placeholder - you might need to adjust based on your database
        try:
            avg_result = await self.session.execute(avg_time_query)
            avg_time = avg_result.scalar()
            stats["average_processing_time_seconds"] = float(avg_time) if avg_time else None
        except:
            stats["average_processing_time_seconds"] = None

        # Jobs in last 24 hours
        from datetime import timedelta
        day_ago = datetime.utcnow() - timedelta(days=1)

        recent_result = await self.session.execute(
            select(func.count(DocumentProcessingJob.id))
            .where(DocumentProcessingJob.created_at >= day_ago)
        )
        stats["jobs_last_24h"] = recent_result.scalar()

        return stats

    async def get_failed_jobs(
        self,
        days: int = 7,
        skip: int = 0,
        limit: int = 50
    ) -> List[DocumentProcessingJob]:
        """Get recently failed jobs for debugging."""
        from datetime import timedelta
        start_date = datetime.utcnow() - timedelta(days=days)

        query = select(DocumentProcessingJob).where(
            and_(
                DocumentProcessingJob.status == "failed",
                DocumentProcessingJob.updated_at >= start_date
            )
        ).order_by(DocumentProcessingJob.updated_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def delete_old_jobs(self, days: int = 30) -> int:
        """Delete old completed/failed jobs to clean up database."""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query = select(DocumentProcessingJob.id).where(
            and_(
                DocumentProcessingJob.status.in_(["completed", "failed"]),
                DocumentProcessingJob.updated_at < cutoff_date
            )
        )

        result = await self.session.execute(query)
        job_ids = [row[0] for row in result.fetchall()]

        if not job_ids:
            return 0

        # Delete the jobs
        delete_query = DocumentProcessingJob.__table__.delete().where(
            DocumentProcessingJob.id.in_(job_ids)
        )

        from sqlalchemy import delete
        delete_stmt = delete(DocumentProcessingJob).where(
            DocumentProcessingJob.id.in_(job_ids)
        )

        await self.session.execute(delete_stmt)
        await self.session.flush()

        return len(job_ids)

    async def get_processing_jobs_by_user(self, user_id: str) -> List[DocumentProcessingJob]:
        """Get currently processing jobs for a user."""
        query = select(DocumentProcessingJob).where(
            and_(
                DocumentProcessingJob.user_id == user_id,
                DocumentProcessingJob.status.in_(["pending", "processing", "embedding", "indexing"])
            )
        ).order_by(DocumentProcessingJob.created_at.asc())

        result = await self.session.execute(query)
        return result.scalars().all()

    async def cancel_job(self, job_id: int, user_id: str) -> bool:
        """Cancel a job if it belongs to the user and is in a cancellable state."""
        job = await self.session.execute(
            select(DocumentProcessingJob).where(
                and_(
                    DocumentProcessingJob.id == job_id,
                    DocumentProcessingJob.user_id == user_id,
                    DocumentProcessingJob.status.in_(["pending", "processing"])
                )
            )
        )
        job = job.scalar_one_or_none()

        if not job:
            return False

        job.status = "cancelled"
        job.completed_at = datetime.utcnow()
        job.updated_at = datetime.utcnow()

        await self.session.flush()
        return True


class DocumentDAO(BaseRepository[Document]):
    """Data access object for document operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Document)

    async def get_documents_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Document]:
        """Get documents for a specific user."""
        query = select(Document).where(
            Document.user_id == user_id
        ).order_by(Document.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def search_documents(
        self,
        user_id: str,
        search_term: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Document]:
        """Search documents by title or content."""
        search_pattern = f"%{search_term}%"

        query = select(Document).where(
            and_(
                Document.user_id == user_id,
                or_(
                    Document.original_filename.ilike(search_pattern),
                    Document.source_title.ilike(search_pattern) if Document.source_title else False
                )
            )
        ).order_by(Document.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()


class DocumentChunkDAO(BaseRepository[DocumentChunk]):
    """Data access object for document chunk operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, DocumentChunk)

    async def get_chunks_by_document(
        self,
        document_id: str,
        skip: int = 0,
        limit: int = 1000
    ) -> List[DocumentChunk]:
        """Get all chunks for a document."""
        query = select(DocumentChunk).where(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_chunk_count_by_document(self, document_id: str) -> int:
        """Get total chunk count for a document."""
        result = await self.session.execute(
            select(func.count(DocumentChunk.id)).where(
                DocumentChunk.document_id == document_id
            )
        )
        return result.scalar()

    async def search_chunks(
        self,
        user_id: str,
        search_term: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[DocumentChunk]:
        """Search chunks by content."""
        search_pattern = f"%{search_term}%"

        query = select(DocumentChunk).where(
            and_(
                DocumentChunk.user_id == user_id,
                DocumentChunk.content.ilike(search_pattern)
            )
        ).order_by(DocumentChunk.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_documents_by_chunk_search(
        self,
        user_id: str,
        search_term: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get unique documents that have chunks matching the search term."""
        search_pattern = f"%{search_term}%"

        query = select(
            DocumentChunk.document_id,
            func.min(DocumentChunk.chunk_index).label('first_chunk_index'),
            func.min(DocumentChunk.content).label('preview_content'),
            func.count(DocumentChunk.id).label('total_chunks')
        ).where(
            and_(
                DocumentChunk.user_id == user_id,
                DocumentChunk.content.ilike(search_pattern)
            )
        ).group_by(DocumentChunk.document_id).order_by(
            func.min(DocumentChunk.created_at).desc()
        ).offset(skip).limit(limit)

        result = await self.session.execute(query)
        rows = result.fetchall()

        documents = []
        for row in rows:
            # Get a preview of the matching content
            preview = row.preview_content[:200] + "..." if len(row.preview_content) > 200 else row.preview_content

            documents.append({
                "document_id": row.document_id,
                "preview_content": preview,
                "total_chunks": row.total_chunks,
                "first_chunk_index": row.first_chunk_index
            })

        return documents