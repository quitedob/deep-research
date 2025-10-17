# -*- coding: utf-8 -*-
"""
PGVector 向量存储模块
使用 PostgreSQL + pgvector 进行向量存储和检索
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """文档块"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


class PgVectorStore:
    """PGVector 向量存储"""

    def __init__(self, connection_string: str = None, table_name: str = "embeddings"):
        """
        初始化 PGVector 存储

        Args:
            connection_string: PostgreSQL 连接字符串
            table_name: 表名
        """
        self.connection_string = connection_string or "postgresql://localhost/deep_research"
        self.table_name = table_name
        self._connection = None
        self._initialized = False

    async def initialize(self):
        """初始化数据库连接和表结构"""
        if self._initialized:
            return

        try:
            # 尝试导入 psycopg2 或 asyncpg
            try:
                import asyncpg
                self._driver = "asyncpg"
            except ImportError:
                try:
                    import psycopg2
                    self._driver = "psycopg2"
                except ImportError:
                    logger.warning("未安装 PostgreSQL 驱动，将使用内存存储")
                    self._driver = "memory"
                    self._memory_store = []
                    self._initialized = True
                    return

            if self._driver == "asyncpg":
                self._connection = await asyncpg.connect(self.connection_string)

                # 创建向量扩展（如果不存在）
                await self._connection.execute("CREATE EXTENSION IF NOT EXISTS vector;")

                # 创建表
                create_table_query = f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id TEXT PRIMARY KEY,
                    content TEXT,
                    metadata JSONB,
                    embedding vector(1536)
                );
                """
                await self._connection.execute(create_table_query)

                # 创建向量相似度索引
                create_index_query = f"""
                CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx
                ON {self.table_name}
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
                """
                await self._connection.execute(create_index_query)

            elif self._driver == "psycopg2":
                # 同步版本的实现
                import psycopg2
                from psycopg2.extras import Json

                self._connection = psycopg2.connect(self.connection_string)

                # 创建向量扩展
                with self._connection.cursor() as cursor:
                    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                    self._connection.commit()

                # 创建表
                create_table_query = f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id TEXT PRIMARY KEY,
                    content TEXT,
                    metadata JSONB,
                    embedding vector(1536)
                );
                """
                with self._connection.cursor() as cursor:
                    cursor.execute(create_table_query)
                    self._connection.commit()

            self._initialized = True
            logger.info(f"PGVector 存储初始化成功，使用驱动: {self._driver}")

        except Exception as e:
            logger.error(f"PGVector 存储初始化失败: {e}")
            # 回退到内存存储
            self._driver = "memory"
            self._memory_store = []
            self._initialized = True

    async def add_document(self, content: str, metadata: Dict[str, Any], embedding: List[float], doc_id: str = None) -> str:
        """
        添加文档到向量存储

        Args:
            content: 文档内容
            metadata: 元数据
            embedding: 向量嵌入
            doc_id: 文档ID（如果不提供则自动生成）

        Returns:
            文档ID
        """
        if not self._initialized:
            await self.initialize()

        if not doc_id:
            import uuid
            doc_id = str(uuid.uuid4())

        try:
            if self._driver == "asyncpg":
                # asyncpg 版本
                insert_query = f"""
                INSERT INTO {self.table_name} (id, content, metadata, embedding)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (id) DO UPDATE SET
                    content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding;
                """

                await self._connection.execute(
                    insert_query,
                    doc_id, content, metadata, embedding
                )

            elif self._driver == "psycopg2":
                # psycopg2 版本
                from psycopg2.extras import Json

                insert_query = f"""
                INSERT INTO {self.table_name} (id, content, metadata, embedding)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding;
                """

                with self._connection.cursor() as cursor:
                    cursor.execute(insert_query, (doc_id, content, Json(metadata), embedding))
                    self._connection.commit()

            else:
                # 内存存储版本
                doc = DocumentChunk(
                    id=doc_id,
                    content=content,
                    metadata=metadata,
                    embedding=embedding
                )
                self._memory_store.append(doc)

            logger.debug(f"文档 {doc_id} 已添加到向量存储")
            return doc_id

        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            raise

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0
    ) -> List[Tuple[Any, float]]:
        """
        向量相似度搜索

        Args:
            query_embedding: 查询向量
            top_k: 返回的文档数量
            filter_metadata: 元数据过滤条件
            score_threshold: 分数阈值

        Returns:
            (文档, 分数) 元组列表
        """
        if not self._initialized:
            await self.initialize()

        try:
            if self._driver == "asyncpg":
                # 构建查询
                select_query = f"""
                SELECT id, content, metadata, 1 - (embedding <=> $1) as similarity
                FROM {self.table_name}
                """

                params = [query_embedding]

                # 添加元数据过滤
                if filter_metadata:
                    conditions = []
                    for key, value in filter_metadata.items():
                        conditions.append(f"metadata->>{key!r} = ${len(params) + 1}")
                        params.append(str(value))

                    if conditions:
                        select_query += " WHERE " + " AND ".join(conditions)

                select_query += f" ORDER BY embedding <=> $1 LIMIT {top_k}"

                rows = await self._connection.fetch(select_query, *params)

                results = []
                for row in rows:
                    similarity = float(row['similarity'])
                    if similarity >= score_threshold:
                        doc = DocumentChunk(
                            id=row['id'],
                            content=row['content'],
                            metadata=dict(row['metadata']) if row['metadata'] else {},
                            embedding=None
                        )
                        results.append((doc, similarity))

                return results

            elif self._driver == "psycopg2":
                # psycopg2 版本
                from psycopg2.extras import Json

                select_query = f"""
                SELECT id, content, metadata, 1 - (embedding <=> %s) as similarity
                FROM {self.table_name}
                """

                params = [query_embedding]

                # 添加元数据过滤
                if filter_metadata:
                    conditions = []
                    for key, value in filter_metadata.items():
                        conditions.append(f"metadata->>%s = %s")
                        params.extend([key, str(value)])

                    if conditions:
                        select_query += " WHERE " + " AND ".join(conditions)

                select_query += f" ORDER BY embedding <=> %s LIMIT {top_k}"

                with self._connection.cursor() as cursor:
                    cursor.execute(select_query, params)
                    rows = cursor.fetchall()

                results = []
                for row in rows:
                    similarity = float(row[3])
                    if similarity >= score_threshold:
                        doc = DocumentChunk(
                            id=row[0],
                            content=row[1],
                            metadata=dict(row[2]) if row[2] else {},
                            embedding=None
                        )
                        results.append((doc, similarity))

                return results

            else:
                # 内存存储版本
                if not self._memory_store:
                    return []

                # 计算余弦相似度
                import numpy as np
                query_vec = np.array(query_embedding)

                similarities = []
                for doc in self._memory_store:
                    if doc.embedding:
                        doc_vec = np.array(doc.embedding)
                        # 计算余弦相似度
                        similarity = np.dot(query_vec, doc_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec))
                        similarities.append((doc, float(similarity)))

                # 排序并返回top_k
                similarities.sort(key=lambda x: x[1], reverse=True)
                return similarities[:top_k]

        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []

    async def delete_document(self, doc_id: str):
        """
        删除文档

        Args:
            doc_id: 文档ID
        """
        if not self._initialized:
            await self.initialize()

        try:
            if self._driver == "asyncpg":
                delete_query = f"DELETE FROM {self.table_name} WHERE id = $1"
                await self._connection.execute(delete_query, doc_id)

            elif self._driver == "psycopg2":
                delete_query = f"DELETE FROM {self.table_name} WHERE id = %s"
                with self._connection.cursor() as cursor:
                    cursor.execute(delete_query, (doc_id,))
                    self._connection.commit()

            else:
                # 内存存储版本
                self._memory_store = [doc for doc in self._memory_store if doc.id != doc_id]

            logger.debug(f"文档 {doc_id} 已从向量存储中删除")

        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            raise

    async def close(self):
        """关闭数据库连接"""
        if self._connection:
            if self._driver == "asyncpg":
                await self._connection.close()
            elif self._driver == "psycopg2":
                self._connection.close()

    def __del__(self):
        """析构函数，确保连接被关闭"""
        if hasattr(self, '_connection') and self._connection:
            # 注意：这里无法使用 await，所以在实际使用中应该显式调用 close()
            pass


# 全局实例
_pgvector_store_instance = None


def get_pgvector_store(connection_string: str = None, table_name: str = "embeddings") -> PgVectorStore:
    """
    获取 PGVector 存储实例

    Args:
        connection_string: 数据库连接字符串
        table_name: 表名

    Returns:
        PgVectorStore 实例
    """
    global _pgvector_store_instance

    if _pgvector_store_instance is None:
        _pgvector_store_instance = PgVectorStore(connection_string, table_name)

    return _pgvector_store_instance
