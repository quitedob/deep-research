# -*- coding: utf-8 -*-
"""
ResearchService：深度研究工作流业务逻辑服务
提供智能体协作、研究工作流管理、证据链生成等功能
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import json

from .base_service import BaseService
from src.dao import DocumentDAO, DocumentChunkDAO, UsersDAO
from src.sqlmodel.rag_models import Document, Chunk as DocumentChunk
from src.sqlmodel.models import User
from src.config.logging.logging import get_logger

logger = get_logger("research_service")


class ResearchService(BaseService):
    """深度研究服务类"""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.document_dao = DocumentDAO(session)
        self.chunk_dao = DocumentChunkDAO(session)
        self.users_dao = UsersDAO(session)

    async def create_research_project(
        self,
        user_id: str,
        title: str,
        description: Optional[str] = None,
        research_type: str = "general"
    ) -> Dict[str, Any]:
        """
        创建研究项目

        Args:
            user_id: 用户ID
            title: 项目标题
            description: 项目描述
            research_type: 研究类型

        Returns:
            创建的项目信息
        """
        try:
            project_id = str(uuid.uuid4())

            project_data = {
                "project_id": project_id,
                "title": title,
                "description": description,
                "research_type": research_type,
                "status": "created",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "stages": [],
                "evidence_chain": [],
                "findings": [],
                "metadata": {}
            }

            await self.log_operation(
                user_id=user_id,
                operation="research_project_created",
                details={
                    "project_id": project_id,
                    "title": title,
                    "research_type": research_type
                }
            )

            return {
                "success": True,
                "project_id": project_id,
                "title": title,
                "status": "created",
                "message": "研究项目创建成功"
            }

        except Exception as e:
            logger.error(f"创建研究项目失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "创建研究项目失败"
            }

    async def start_research_workflow(
        self,
        user_id: str,
        project_id: str,
        query: str,
        research_type: str = "comprehensive",
        sources: Optional[List[str]] = None,
        agent_configs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        启动研究工作流

        Args:
            user_id: 用户ID
            project_id: 项目ID
            query: 研究查询
            research_type: 研究类型
            sources: 数据源列表
            agent_configs: 智能体配置

        Returns:
            工作流启动结果
        """
        try:
            workflow_id = str(uuid.uuid4())

            # 验证用户权限
            user = await self.users_dao.get_by_id(user_id)
            if not user:
                return {
                    "success": False,
                    "error": "用户不存在"
                }

            # 检查用户角色
            if user.role not in ["subscribed", "admin"]:
                return {
                    "success": False,
                    "error": "需要订阅用户权限才能使用深度研究功能"
                }

            # 创建工作流记录
            workflow_data = {
                "workflow_id": workflow_id,
                "project_id": project_id,
                "query": query,
                "research_type": research_type,
                "status": "initiated",
                "created_at": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "sources": sources or ["web_search"],
                "agent_configs": agent_configs or {},
                "stages": [
                    {
                        "stage_id": str(uuid.uuid4()),
                        "stage_name": "research_planning",
                        "status": "pending",
                        "agent": "research_coordinator",
                        "created_at": datetime.utcnow().isoformat()
                    }
                ],
                "metadata": {
                    "estimated_duration": "30-60 minutes",
                    "complexity": "medium"
                }
            }

            await self.log_operation(
                user_id=user_id,
                operation="research_workflow_started",
                details={
                    "workflow_id": workflow_id,
                    "project_id": project_id,
                    "query": query,
                    "research_type": research_type
                }
            )

            return {
                "success": True,
                "workflow_id": workflow_id,
                "project_id": project_id,
                "status": "initiated",
                "estimated_duration": "30-60 minutes",
                "message": "研究工作流已启动"
            }

        except Exception as e:
            logger.error(f"启动研究工作流失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "启动研究工作流失败"
            }

    async def get_research_status(
        self,
        user_id: str,
        workflow_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取研究工作流状态

        Args:
            user_id: 用户ID
            workflow_id: 工作流ID

        Returns:
            工作流状态信息
        """
        try:
            # 这里应该从数据库获取工作流状态
            # 简化实现，返回模拟状态
            return {
                "workflow_id": workflow_id,
                "status": "processing",
                "progress": 45,
                "current_stage": "data_analysis",
                "stages": [
                    {
                        "stage_name": "research_planning",
                        "status": "completed",
                        "completed_at": datetime.utcnow().isoformat()
                    },
                    {
                        "stage_name": "data_collection",
                        "status": "completed",
                        "completed_at": datetime.utcnow().isoformat()
                    },
                    {
                        "stage_name": "data_analysis",
                        "status": "processing",
                        "progress": 45
                    }
                ],
                "estimated_completion": datetime.utcnow() + timedelta(minutes=15)
            }

        except Exception as e:
            logger.error(f"获取研究状态失败: {e}")
            return None

    async def generate_evidence_chain(
        self,
        user_id: str,
        project_id: str,
        research_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成证据链

        Args:
            user_id: 用户ID
            project_id: 项目ID
            research_data: 研究数据

        Returns:
            证据链生成结果
        """
        try:
            # 验证用户权限
            user = await self.users_dao.get_by_id(user_id)
            if not user:
                return {
                    "success": False,
                    "error": "用户不存在"
                }

            if user.role not in ["subscribed", "admin"]:
                return {
                    "success": False,
                    "error": "需要订阅用户权限"
                }

            evidence_chain_id = str(uuid.uuid4())

            # 分析研究数据并生成证据链
            evidence_items = []
            sources = research_data.get("sources", [])

            for i, source in enumerate(sources):
                evidence_items.append({
                    "evidence_id": str(uuid.uuid4()),
                    "source_type": source.get("type", "unknown"),
                    "source_url": source.get("url", ""),
                    "source_title": source.get("title", ""),
                    "content": source.get("content", ""),
                    "relevance_score": source.get("relevance", 0.8),
                    "verification_status": "pending",
                    "created_at": datetime.utcnow().isoformat(),
                    "metadata": source.get("metadata", {})
                })

            # 生成证据链关系
            chain_relationships = []
            for i in range(len(evidence_items) - 1):
                chain_relationships.append({
                    "from_evidence": evidence_items[i]["evidence_id"],
                    "to_evidence": evidence_items[i + 1]["evidence_id"],
                    "relationship_type": "supports",
                    "confidence": 0.85,
                    "created_at": datetime.utcnow().isoformat()
                })

            chain_data = {
                "evidence_chain_id": evidence_chain_id,
                "project_id": project_id,
                "research_query": research_data.get("query", ""),
                "evidence_items": evidence_items,
                "chain_relationships": chain_relationships,
                "overall_confidence": sum(item["relevance_score"] for item in evidence_items) / len(evidence_items) if evidence_items else 0,
                "status": "generated",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            await self.log_operation(
                user_id=user_id,
                operation="evidence_chain_generated",
                details={
                    "evidence_chain_id": evidence_chain_id,
                    "project_id": project_id,
                    "evidence_count": len(evidence_items)
                }
            )

            return {
                "success": True,
                "evidence_chain_id": evidence_chain_id,
                "evidence_count": len(evidence_items),
                "overall_confidence": chain_data["overall_confidence"],
                "status": "generated",
                "message": "证据链生成成功"
            }

        except Exception as e:
            logger.error(f"生成证据链失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "生成证据链失败"
            }

    async def generate_research_report(
        self,
        user_id: str,
        project_id: str,
        research_data: Dict[str, Any],
        report_format: str = "markdown"
    ) -> Dict[str, Any]:
        """
        生成研究报告

        Args:
            user_id: 用户ID
            project_id: 项目ID
            research_data: 研究数据
            report_format: 报告格式 (markdown, pdf, docx)

        Returns:
            报告生成结果
        """
        try:
            # 验证用户权限
            user = await self.users_dao.get_by_id(user_id)
            if not user:
                return {
                    "success": False,
                    "error": "用户不存在"
                }

            if user.role not in ["subscribed", "admin"]:
                return {
                    "success": False,
                    "error": "需要订阅用户权限"
                }

            report_id = str(uuid.uuid4())

            # 生成报告内容
            report_content = await self._generate_report_content(
                research_data,
                report_format
            )

            # 保存报告
            report_data = {
                "report_id": report_id,
                "project_id": project_id,
                "title": research_data.get("query", "研究报告"),
                "format": report_format,
                "content": report_content,
                "status": "generated",
                "created_at": datetime.utcnow().isoformat(),
                "file_size": len(report_content.encode('utf-8')),
                "metadata": {
                    "evidence_count": len(research_data.get("sources", [])),
                    "research_duration": research_data.get("duration", 0),
                    "confidence_score": research_data.get("confidence", 0.8)
                }
            }

            await self.log_operation(
                user_id=user_id,
                operation="research_report_generated",
                details={
                    "report_id": report_id,
                    "project_id": project_id,
                    "format": report_format,
                    "file_size": report_data["file_size"]
                }
            )

            return {
                "success": True,
                "report_id": report_id,
                "format": report_format,
                "file_size": report_data["file_size"],
                "content": report_content,
                "message": "研究报告生成成功"
            }

        except Exception as e:
            logger.error(f"生成研究报告失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "生成研究报告失败"
            }

    async def _generate_report_content(
        self,
        research_data: Dict[str, Any],
        format: str
    ) -> str:
        """生成报告内容"""
        query = research_data.get("query", "研究主题")
        sources = research_data.get("sources", [])

        if format == "markdown":
            content = f"# {query}\n\n"
            content += f"## 研究摘要\n\n"
            content += f"本研究对\"{query}\"进行了深入分析，通过{len(sources)}个数据源收集相关信息。\n\n"

            content += "## 主要发现\n\n"
            for i, source in enumerate(sources[:5], 1):
                content += f"{i}. **{source.get('title', f'来源{i}')}**\n"
                content += f"   {source.get('content', '')[:200]}...\n\n"

            content += "## 数据来源\n\n"
            for source in sources:
                content += f"- [{source.get('title', '未知来源')}]({source.get('url', '#')})\n"

            content += f"\n---\n\n*报告生成时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}*"

            return content
        else:
            # 其他格式的实现
            return f"研究报告: {query}\n\n详细内容需要根据{format}格式进行生成。"

    async def get_user_research_projects(
        self,
        user_id: str,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        获取用户研究项目列表

        Args:
            user_id: 用户ID
            status: 状态筛选
            skip: 跳过数量
            limit: 限制数量

        Returns:
            项目列表
        """
        try:
            # 这里应该从数据库获取项目列表
            # 简化实现，返回模拟数据
            projects = [
                {
                    "project_id": str(uuid.uuid4()),
                    "title": "人工智能发展趋势研究",
                    "status": "completed",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                    "research_type": "comprehensive"
                }
            ]

            return {
                "projects": projects,
                "total": len(projects),
                "filters": {
                    "status": status
                }
            }

        except Exception as e:
            logger.error(f"获取研究项目失败: {e}")
            return {
                "projects": [],
                "total": 0,
                "error": str(e)
            }

    async def validate_permissions(self, user_id: str, required_role: str) -> bool:
        """验证用户权限（重写基类方法）"""
        # 研究服务的权限验证
        # 只有订阅用户和管理员可以使用深度研究功能
        try:
            user = await self.users_dao.get_by_id(user_id)
            if not user:
                return False

            if required_role == "subscribed":
                return user.role in ["subscribed", "admin"]
            elif required_role == "admin":
                return user.role == "admin"

            return True
        except:
            return False