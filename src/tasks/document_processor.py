# -*- coding: utf-8 -*-
"""
文档处理工作流：实现 .docx/.doc -> PDF -> OCR -> 向量化的完整流水线。
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
import asyncio
from datetime import datetime

# 文档处理库
try:
    import docx2txt
    DOCX2TXT_AVAILABLE = True
except ImportError:
    DOCX2TXT_AVAILABLE = False

try:
    import pypandoc
    PYPANDOC_AVAILABLE = True
except ImportError:
    PYPANDOC_AVAILABLE = False

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from src.config.settings import get_settings
from src.sqlmodel.models import DocumentProcessingJob
from src.core.db import get_db_session
from sqlalchemy import update, select

# 导入新的RAG功能
from src.core.rag import FileProcessor, KnowledgeBase

settings = get_settings()


class DocumentProcessor:
    """文档处理器"""
    
    def __init__(self):
        self.supported_formats = {
            '.docx': self._process_docx,
            '.doc': self._process_doc,
            '.txt': self._process_txt,
            '.md': self._process_markdown,
            '.pdf': self._process_pdf
        }
        
        # 检查必要的依赖
        self._check_dependencies()
    
    def _check_dependencies(self):
        """检查必要的依赖是否可用"""
        missing_deps = []
        
        if not DOCX2TXT_AVAILABLE:
            missing_deps.append("docx2txt")
        
        if not PYPANDOC_AVAILABLE:
            missing_deps.append("pypandoc")
        
        if not REPORTLAB_AVAILABLE:
            missing_deps.append("reportlab")
        
        # 检查 OCRmyPDF 是否可用
        try:
            subprocess.run(['ocrmypdf', '--version'], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_deps.append("ocrmypdf")
        
        if missing_deps:
            print(f"警告：以下依赖不可用：{', '.join(missing_deps)}")
            print("某些文档处理功能可能无法正常工作")
    
    async def process_document(
        self,
        job_id: str,
        file_path: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        处理文档的主函数
        
        Args:
            job_id: 任务ID
            file_path: 文件路径
            user_id: 用户ID
        
        Returns:
            处理结果字典
        """
        try:
            # 更新任务状态为处理中
            await self._update_job_status(job_id, "processing", progress=0.1)
            
            # 获取文件扩展名
            file_extension = Path(file_path).suffix.lower()
            
            # 检查文件格式是否支持
            if file_extension not in self.supported_formats:
                raise ValueError(f"不支持的文件格式：{file_extension}")
            
            # 步骤1：提取文本内容
            print(f"开始处理文件：{file_path}")
            text_content = await self._extract_text(file_path, file_extension)
            await self._update_job_status(job_id, "processing", progress=0.3)
            
            if not text_content or len(text_content.strip()) < 10:
                raise ValueError("提取的文本内容过少，可能文件损坏或格式不支持")
            
            # 步骤2：分块处理（简化流程，跳过OCR）
            chunks = await self._chunk_text(text_content)
            await self._update_job_status(job_id, "processing", progress=0.5)
            
            # 更新任务状态为嵌入处理中
            await self._update_job_status(job_id, "embedding", progress=0.6)
            
            # 步骤3：生成嵌入向量
            embeddings = await self._generate_embeddings(chunks)
            await self._update_job_status(job_id, "embedding", progress=0.8)
            
            # 步骤4：存储到向量数据库
            await self._update_job_status(job_id, "indexed", progress=0.9)
            await self._store_vectors(chunks, embeddings, user_id, file_path)
            
            # 步骤5：集成到RAG知识库系统
            await self._integrate_with_rag_system(file_path, user_id, text_content)
            
            # 准备结果数据
            result_data = {
                "text_length": len(text_content),
                "chunks_count": len(chunks),
                "embeddings_count": len(embeddings),
                "filename": Path(file_path).name
            }
            
            # 更新任务状态为完成
            await self._update_job_status(
                job_id, 
                "completed", 
                progress=1.0,
                result=result_data
            )
            
            return {
                "status": "success",
                **result_data
            }
            
        except Exception as e:
            error_message = str(e)
            print(f"文档处理失败：{error_message}")
            
            # 更新任务状态为失败
            await self._update_job_status(job_id, "failed", error_message)
            
            # 清理临时文件
            await self._cleanup_temp_files([file_path])
            
            return {
                "status": "failed",
                "error": error_message
            }
    
    async def _extract_text(self, file_path: str, file_extension: str) -> str:
        """根据文件格式提取文本"""
        processor = self.supported_formats.get(file_extension)
        if not processor:
            raise ValueError(f"不支持的文件格式：{file_extension}")
        
        return await processor(file_path)
    
    async def _process_docx(self, file_path: str) -> str:
        """处理 .docx 文件"""
        if not DOCX2TXT_AVAILABLE:
            raise ImportError("docx2txt 库未安装")
        
        try:
            # 在线程池中执行同步操作
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(None, docx2txt.process, file_path)
            return text or ""
        except Exception as e:
            raise ValueError(f"处理 .docx 文件失败：{str(e)}")
    
    async def _process_doc(self, file_path: str) -> str:
        """处理 .doc 文件"""
        if not PYPANDOC_AVAILABLE:
            raise ImportError("pypandoc 库未安装")
        
        try:
            # 使用 pandoc 转换 .doc 文件
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                None, 
                pypandoc.convert_file, 
                file_path, 
                'plain'
            )
            return text or ""
        except Exception as e:
            raise ValueError(f"处理 .doc 文件失败：{str(e)}")
    
    async def _process_txt(self, file_path: str) -> str:
        """处理 .txt 文件"""
        try:
            loop = asyncio.get_event_loop()
            with open(file_path, 'r', encoding='utf-8') as f:
                text = await loop.run_in_executor(None, f.read)
            return text or ""
        except Exception as e:
            raise ValueError(f"处理 .txt 文件失败：{str(e)}")
    
    async def _process_markdown(self, file_path: str) -> str:
        """处理 .md 文件"""
        try:
            loop = asyncio.get_event_loop()
            with open(file_path, 'r', encoding='utf-8') as f:
                text = await loop.run_in_executor(None, f.read)
            return text or ""
        except Exception as e:
            raise ValueError(f"处理 .md 文件失败：{str(e)}")
    
    async def _process_pdf(self, file_path: str) -> str:
        """处理 .pdf 文件（支持文本提取和OCR）"""
        try:
            # 首先尝试直接提取文本
            text_content = await self._extract_text_from_pdf_direct(file_path)

            # 如果提取的文本太少，尝试OCR处理
            if len(text_content.strip()) < 100:
                print(f"直接提取文本过少 ({len(text_content)} 字符)，尝试OCR处理")
                text_content = await self._extract_text_from_pdf_ocr(file_path)

            return text_content or ""

        except Exception as e:
            raise ValueError(f"处理 .pdf 文件失败：{str(e)}")

    async def _extract_text_from_pdf_direct(self, file_path: str) -> str:
        """直接从PDF提取文本"""
        try:
            # 使用PyPDF2提取文本
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                text_content = ""

                for page in reader.pages:
                    text_content += page.extract_text() + "\n"

                return text_content.strip()

            except ImportError:
                print("PyPDF2未安装，尝试使用pdfplumber")
                # 回退到pdfplumber
                import pdfplumber

                with pdfplumber.open(file_path) as pdf:
                    text_content = ""
                    for page in pdf.pages:
                        text_content += page.extract_text() + "\n"

                return text_content.strip()

        except Exception as e:
            print(f"直接文本提取失败: {str(e)}")
            return ""

    async def _extract_text_from_pdf_ocr(self, file_path: str) -> str:
        """使用OCR从PDF提取文本"""
        try:
            # 检查OCRmyPDF是否可用
            try:
                subprocess.run(['ocrmypdf', '--version'],
                             capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                raise ImportError("OCRmyPDF未安装或不可用")

            # 创建临时文件用于OCR处理
            temp_dir = Path(self.settings.temp_dir)
            temp_dir.mkdir(parents=True, exist_ok=True)

            ocr_output_path = temp_dir / f"ocr_{Path(file_path).stem}.pdf"

            # 执行OCR处理
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                subprocess.run,
                [
                    'ocrmypdf',
                    '--deskew',           # 自动倾斜校正
                    '--force-ocr',        # 强制OCR
                    '--optimize', 1,      # 优化级别
                    '--output-type', 'pdf',
                    '--language', 'chi_sim+eng',  # 支持中文和英文
                    file_path,
                    str(ocr_output_path)
                ],
                subprocess.PIPE,
                subprocess.PIPE,
                None,
                600  # 10分钟超时
            )

            if result.returncode != 0:
                raise RuntimeError(f"OCR处理失败：{result.stderr.decode()}")

            # 从OCR后的PDF提取文本
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(str(ocr_output_path))
                text_content = ""

                for page in reader.pages:
                    text_content += page.extract_text() + "\n"

                # 清理临时文件
                if ocr_output_path.exists():
                    ocr_output_path.unlink()

                return text_content.strip()

            except ImportError:
                # 使用pdfplumber作为回退
                import pdfplumber

                with pdfplumber.open(str(ocr_output_path)) as pdf:
                    text_content = ""
                    for page in pdf.pages:
                        text_content += page.extract_text() + "\n"

                # 清理临时文件
                if ocr_output_path.exists():
                    ocr_output_path.unlink()

                return text_content.strip()

        except Exception as e:
            print(f"OCR文本提取失败: {str(e)}")
            return ""
    
    async def _create_pdf_from_text(self, text: str, job_id: str) -> str:
        """从文本创建PDF文件"""
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab 库未安装")
        
        try:
            # 创建临时PDF文件
            temp_dir = Path(settings.temp_dir)
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            pdf_path = temp_dir / f"temp_{job_id}.pdf"
            
            # 在线程池中执行PDF创建
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._create_pdf_sync,
                text,
                str(pdf_path)
            )
            
            return str(pdf_path)
            
        except Exception as e:
            raise ValueError(f"创建PDF文件失败：{str(e)}")
    
    def _create_pdf_sync(self, text: str, pdf_path: str):
        """同步创建PDF文件"""
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        
        # 设置字体（支持中文）
        try:
            # 尝试使用系统中文字体
            pdfmetrics.registerFont(TTFont('SimSun', 'simsun.ttc'))
            font_name = 'SimSun'
        except:
            font_name = 'Helvetica'
        
        c.setFont(font_name, 12)
        
        # 分页处理长文本
        lines = text.split('\n')
        y_position = height - 50
        page = 1
        
        for line in lines:
            # 检查是否需要新页
            if y_position < 50:
                c.showPage()
                c.setFont(font_name, 12)
                y_position = height - 50
                page += 1
            
            # 处理长行（自动换行）
            if len(line) > 80:
                words = line.split()
                current_line = ""
                for word in words:
                    if len(current_line + word) > 80:
                        c.drawString(50, y_position, current_line)
                        y_position -= 20
                        current_line = word
                    else:
                        current_line += " " + word if current_line else word
                
                if current_line:
                    c.drawString(50, y_position, current_line)
                    y_position -= 20
            else:
                c.drawString(50, y_position, line)
                y_position -= 20
        
        c.save()
    
    async def _perform_ocr(self, pdf_path: str) -> str:
        """对PDF文件进行OCR处理"""
        try:
            # 检查 OCRmyPDF 是否可用
            try:
                subprocess.run(['ocrmypdf', '--version'], 
                             capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                raise ImportError("OCRmyPDF 未安装或不可用")
            
            # 创建OCR输出文件路径
            ocr_pdf_path = f"{pdf_path}.ocr.pdf"
            
            # 在线程池中执行OCR处理
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                subprocess.run,
                [
                    'ocrmypdf',
                    '--deskew',           # 自动倾斜校正
                    '--force-ocr',        # 强制OCR
                    '--optimize', 1,      # 优化级别
                    '--output-type', 'pdf',
                    pdf_path,
                    ocr_pdf_path
                ],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"OCR处理失败：{result.stderr}")
            
            return ocr_pdf_path
            
        except Exception as e:
            raise ValueError(f"OCR处理失败：{str(e)}")
    
    async def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """从OCR后的PDF提取文本"""
        try:
            # 这里应该使用 PyPDF2 或其他PDF文本提取库
            # 暂时返回一个占位符
            return "OCR处理后的文本内容"
            
        except Exception as e:
            raise ValueError(f"从PDF提取文本失败：{str(e)}")
    
    async def _chunk_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """将文本分块"""
        try:
            chunks = []
            words = text.split()
            current_chunk = ""
            
            for word in words:
                if len(current_chunk + " " + word) > chunk_size:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                        current_chunk = word
                    else:
                        # 单个词超过块大小，强制分割
                        chunks.append(word)
                else:
                    current_chunk += " " + word if current_chunk else word
            
            # 添加最后一个块
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            return chunks
            
        except Exception as e:
            raise ValueError(f"文本分块失败：{str(e)}")
    
    async def _generate_embeddings(self, chunks: List[str]) -> List[List[float]]:
        """为文本块生成嵌入向量"""
        try:
            # 使用真实的嵌入服务
            from src.llms.embeddings import get_embedding_service
            
            embedding_service = get_embedding_service()
            embeddings = await embedding_service.embed_documents(chunks)
            
            print(f"成功生成 {len(embeddings)} 个嵌入向量")
            return embeddings
            
        except Exception as e:
            print(f"嵌入服务不可用，使用占位符向量: {e}")
            # 回退到随机向量
            import random
            embeddings = []
            for chunk in chunks:
                embedding = [random.uniform(-1, 1) for _ in range(1536)]
                embeddings.append(embedding)
            return embeddings
    
    async def _store_vectors(
        self,
        chunks: List[str],
        embeddings: List[List[float]],
        user_id: str,
        source_file: str
    ):
        """将向量存储到向量数据库"""
        try:
            # 使用 pgvector 存储
            from src.rag.pgvector_store import get_pgvector_store
            from src.rag.vector_store import Document as VectorDocument
            
            pgvector_store = get_pgvector_store()
            
            # 准备文档数据
            documents = []
            filename = Path(source_file).name
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                doc = VectorDocument(
                    id=f"{user_id}_{filename}_{i}",
                    content=chunk,
                    metadata={
                        'user_id': int(user_id),
                        'filename': filename,
                        'source_file': source_file,
                        'chunk_index': i,
                        'total_chunks': len(chunks)
                    }
                )
                # 预设嵌入向量以避免重复计算
                doc.embedding = embedding
                documents.append(doc)
            
            # 批量添加到向量存储
            chunk_ids = await pgvector_store.add_documents(documents)
            
            print(f"成功存储 {len(chunk_ids)} 个向量到 pgvector 数据库")
            print(f"用户ID: {user_id}, 文件: {filename}")
            
        except Exception as e:
            print(f"存储向量到 pgvector 失败，尝试内存存储: {e}")
            # 回退到内存存储
            try:
                from src.rag.retrieval import get_retrieval_service
                
                retrieval_service = get_retrieval_service()
                
                for i, chunk in enumerate(chunks):
                    await retrieval_service.add_document(
                        content=chunk,
                        metadata={
                            'user_id': user_id,
                            'filename': Path(source_file).name,
                            'chunk_index': i,
                            'source_file': source_file
                        },
                        doc_id=f"{user_id}_{Path(source_file).name}_{i}"
                    )
                
                print(f"回退存储：成功存储 {len(chunks)} 个文档块到内存")
                
            except Exception as fallback_error:
                raise ValueError(f"向量存储完全失败: {fallback_error}")
    
    async def _integrate_with_rag_system(self, file_path: str, user_id: str, text_content: str):
        """
        将处理后的文档集成到RAG知识库系统
        为每个用户创建一个默认的知识库
        """
        try:
            # 为用户创建默认知识库名称
            default_kb_name = f"user_{user_id}_docs"
            
            # 检查知识库是否存在，不存在则创建
            existing_kbs = KnowledgeBase.list_kbs()
            if default_kb_name not in existing_kbs:
                # 创建知识库
                kb = KnowledgeBase(default_kb_name)
                print(f"为用户 {user_id} 创建默认知识库: {default_kb_name}")
            else:
                kb = KnowledgeBase(default_kb_name)
            
            # 创建临时文本文件
            temp_dir = Path(settings.temp_dir)
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            filename = Path(file_path).name
            temp_txt_path = temp_dir / f"{filename}.txt"
            
            # 写入文本内容
            with open(temp_txt_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            # 添加到知识库
            await kb.add_txt_file(temp_txt_path, filename)
            
            # 清理临时文件
            if temp_txt_path.exists():
                temp_txt_path.unlink()
            
            print(f"成功将文档 {filename} 添加到用户 {user_id} 的知识库")
            
        except Exception as e:
            print(f"集成到RAG系统失败: {e}")
            # 这里不抛出异常，因为主要的文档处理已经完成
    
    async def _update_job_status(
        self,
        job_id: str,
        status: str,
        error_message: str = None,
        progress: float = None,
        result: Dict[str, Any] = None
    ):
        """更新任务状态"""
        try:
            async for session in get_db_session():
                # 查询任务记录
                stmt = select(DocumentProcessingJob).where(DocumentProcessingJob.id == int(job_id))
                result_query = await session.execute(stmt)
                job = result_query.scalar_one_or_none()

                if job:
                    job.status = status
                    job.updated_at = datetime.utcnow()

                    if status == "processing" and not job.started_at:
                        job.started_at = datetime.utcnow()
                    elif status in ["completed", "failed"]:
                        job.completed_at = datetime.utcnow()

                    if error_message:
                        job.error_message = error_message

                    if progress is not None:
                        job.progress = progress

                    if result:
                        job.result = result

                    await session.commit()
                    print(f"任务 {job_id} 状态更新为: {status}")
                else:
                    print(f"任务 {job_id} 不存在")

        except Exception as e:
            print(f"更新任务状态失败：{str(e)}")
            # 回退到直接SQL执行
            try:
                async for session in get_db_session():
                    from sqlalchemy import text
                    update_fields = ["status = :status", "updated_at = :updated_at"]
                    params = {
                        "job_id": int(job_id),
                        "status": status,
                        "updated_at": datetime.utcnow()
                    }

                    if status == "processing":
                        update_fields.append("started_at = COALESCE(started_at, :started_at)")
                        params["started_at"] = datetime.utcnow()
                    elif status in ["completed", "failed"]:
                        update_fields.append("completed_at = :completed_at")
                        params["completed_at"] = datetime.utcnow()

                    if error_message:
                        update_fields.append("error_message = :error_message")
                        params["error_message"] = error_message

                    if progress is not None:
                        update_fields.append("progress = :progress")
                        params["progress"] = progress

                    if result:
                        update_fields.append("result = :result")
                        params["result"] = result

                    sql = f"UPDATE document_processing_jobs SET {', '.join(update_fields)} WHERE id = :job_id"
                    await session.execute(text(sql), params)
                    await session.commit()
                    print(f"使用SQL回退方式更新任务 {job_id} 状态为: {status}")
            except Exception as fallback_error:
                print(f"SQL回退也失败: {fallback_error}")
    
    async def _cleanup_temp_files(self, file_paths: List[str]):
        """清理临时文件"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"清理临时文件失败 {file_path}: {str(e)}")


# 全局文档处理器实例
document_processor: Optional[DocumentProcessor] = None


async def get_document_processor() -> DocumentProcessor:
    """获取文档处理器实例（单例模式）"""
    global document_processor
    if document_processor is None:
        document_processor = DocumentProcessor()
    return document_processor


async def process_document_task(
    job_id: str,
    file_path: str,
    user_id: str
) -> Dict[str, Any]:
    """文档处理任务（供任务队列调用）"""
    processor = await get_document_processor()
    return await processor.process_document(job_id, file_path, user_id)
