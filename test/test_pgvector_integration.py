# -*- coding: utf-8 -*-
"""
pgvector 集成测试：验证向量搜索和证据链功能
"""

import asyncio
import pytest
from typing import List

# 测试用的简单嵌入服务
class MockEmbeddingService:
    """模拟嵌入服务"""
    
    def __init__(self):
        self.model_name = "mock-embedding-model"
    
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """生成模拟嵌入向量"""
        import random
        embeddings = []
        for text in texts:
            # 基于文本内容生成确定性的向量
            random.seed(hash(text) % 2**32)
            embedding = [random.uniform(-1, 1) for _ in range(1536)]
            embeddings.append(embedding)
        return embeddings
    
    async def embed_query(self, query: str) -> List[float]:
        """生成查询向量"""
        import random
        random.seed(hash(query) % 2**32)
        return [random.uniform(-1, 1) for _ in range(1536)]


async def test_pgvector_basic_functionality():
    """测试 pgvector 基本功能"""
    try:
        from src.rag.pgvector_store import PgVectorStore
        from src.rag.vector_store import Document as VectorDocument
        
        # 创建测试实例
        store = PgVectorStore()
        
        # 替换为模拟嵌入服务
        store._embedding_service = MockEmbeddingService()
        
        # 准备测试文档
        test_docs = [
            VectorDocument(
                id="test_1",
                content="人工智能是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。",
                metadata={
                    "filename": "ai_intro.txt",
                    "user_id": 1,
                    "source_url": "https://example.com/ai",
                    "citation_id": "ai_001"
                }
            ),
            VectorDocument(
                id="test_2", 
                content="机器学习是人工智能的一个子领域，专注于开发能够从数据中学习和改进的算法。",
                metadata={
                    "filename": "ml_basics.txt",
                    "user_id": 1,
                    "source_url": "https://example.com/ml",
                    "citation_id": "ml_001"
                }
            ),
            VectorDocument(
                id="test_3",
                content="深度学习使用神经网络来模拟人脑的学习过程，在图像识别和自然语言处理方面取得了突破。",
                metadata={
                    "filename": "dl_overview.txt", 
                    "user_id": 1,
                    "source_url": "https://example.com/dl",
                    "citation_id": "dl_001"
                }
            )
        ]
        
        print("开始测试 pgvector 功能...")
        
        # 测试1：添加文档
        print("1. 测试添加文档...")
        try:
            chunk_ids = await store.add_documents(test_docs)
            print(f"✅ 成功添加 {len(chunk_ids)} 个文档")
        except Exception as e:
            print(f"❌ 添加文档失败: {e}")
            return False
        
        # 测试2：基本向量搜索
        print("2. 测试向量搜索...")
        try:
            results = await store.search("什么是人工智能？", top_k=2)
            print(f"✅ 搜索返回 {len(results)} 个结果")
            
            for doc, score in results:
                print(f"   - 评分: {score:.3f}, 内容: {doc.content[:50]}...")
        except Exception as e:
            print(f"❌ 向量搜索失败: {e}")
            return False
        
        # 测试3：带证据链的搜索
        print("3. 测试证据链搜索...")
        try:
            evidence_results = await store.search_with_evidence(
                "机器学习和深度学习的区别",
                top_k=3,
                conversation_id="test_conv_001",
                research_session_id="test_research_001"
            )
            print(f"✅ 证据链搜索返回 {len(evidence_results)} 个结果")
            
            for result in evidence_results:
                print(f"   - 评分: {result.score:.3f}, 来源: {result.source_url}")
                print(f"     引用ID: {result.citation_id}")
        except Exception as e:
            print(f"❌ 证据链搜索失败: {e}")
            return False
        
        # 测试4：获取文档数量
        print("4. 测试获取文档数量...")
        try:
            count = await store.get_document_count()
            print(f"✅ 当前文档数量: {count}")
        except Exception as e:
            print(f"❌ 获取文档数量失败: {e}")
            return False
        
        print("🎉 pgvector 集成测试全部通过！")
        return True
        
    except ImportError as e:
        print(f"❌ 导入错误，可能缺少依赖: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False


async def test_retrieval_service_integration():
    """测试检索服务集成"""
    try:
        from src.rag.retrieval import get_retrieval_service, RetrievalStrategy
        
        print("开始测试检索服务集成...")
        
        # 获取检索服务
        service = get_retrieval_service()
        
        # 测试搜索（会自动尝试 pgvector，失败则回退到内存存储）
        results = await service.search_documents(
            query="人工智能的应用",
            strategy=RetrievalStrategy.VECTOR_ONLY,
            top_k=3,
            conversation_id="test_conv_002"
        )
        
        print(f"✅ 检索服务返回 {len(results)} 个结果")
        
        for result in results:
            print(f"   - 评分: {result.score:.3f}, 来源: {result.source}")
            print(f"     内容: {result.content[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 检索服务集成测试失败: {e}")
        return False


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("🧪 开始 pgvector 集成测试")
    print("=" * 60)
    
    # 测试1：基本 pgvector 功能
    success1 = await test_pgvector_basic_functionality()
    
    print("\n" + "-" * 40 + "\n")
    
    # 测试2：检索服务集成
    success2 = await test_retrieval_service_integration()
    
    print("\n" + "=" * 60)
    
    if success1 and success2:
        print("🎉 所有测试通过！pgvector 集成正常工作")
    else:
        print("❌ 部分测试失败，请检查配置和依赖")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())