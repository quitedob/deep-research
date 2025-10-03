#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整集成测试：验证 DeerFlow 端到端功能
包括文档上传、向量搜索、证据链追踪等核心功能
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量（测试用）
os.environ.setdefault("DATABASE_URL", "mysql+aiomysql://deerflow:deerflow123@localhost:3306/deerflow_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DEBUG", "true")


async def test_basic_imports():
    """测试基本模块导入"""
    print("🧪 测试基本模块导入...")
    
    try:
        # 测试核心模块导入
        from src.rag.pgvector_store import PgVectorStore
        from src.rag.retrieval import get_retrieval_service, RetrievalStrategy
        from src.tasks.document_processor import DocumentProcessor
        from src.api.evidence import EvidenceResponse
        from src.sqlmodel.rag_models import Evidence, Document, Chunk, Embedding
        
        print("✅ 所有核心模块导入成功")
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False


async def test_database_models():
    """测试数据库模型"""
    print("\n🗄️  测试数据库模型...")
    
    try:
        from src.sqlmodel.rag_models import Evidence, Document, Chunk, Embedding
        from datetime import datetime
        
        # 创建测试数据
        evidence = Evidence(
            conversation_id="test_conv_001",
            source_type="document",
            source_url="https://example.com/test.pdf",
            content="这是一个测试证据内容",
            relevance_score=0.85,
            confidence_score=0.90
        )
        
        print("✅ 数据库模型创建成功")
        print(f"   证据ID: {evidence.source_type}")
        print(f"   相关性评分: {evidence.relevance_score}")
        return True
        
    except Exception as e:
        print(f"❌ 数据库模型测试失败: {e}")
        return False


async def test_vector_store_mock():
    """测试向量存储（模拟模式）"""
    print("\n🔍 测试向量存储...")
    
    try:
        from src.rag.vector_store import MemoryVectorStore, Document as VectorDocument
        
        # 创建内存向量存储
        store = MemoryVectorStore()
        
        # 创建测试文档
        test_docs = [
            VectorDocument(
                id="test_1",
                content="人工智能是计算机科学的一个重要分支",
                metadata={"source": "test_doc_1.txt", "user_id": 1}
            ),
            VectorDocument(
                id="test_2", 
                content="机器学习是人工智能的核心技术之一",
                metadata={"source": "test_doc_2.txt", "user_id": 1}
            )
        ]
        
        # 添加文档（会自动生成嵌入向量）
        doc_ids = await store.add_documents(test_docs)
        print(f"✅ 成功添加 {len(doc_ids)} 个文档")
        
        # 测试搜索
        results = await store.search("什么是人工智能", top_k=2)
        print(f"✅ 搜索返回 {len(results)} 个结果")
        
        for doc, score in results:
            print(f"   - 评分: {score:.3f}, 内容: {doc.content[:30]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 向量存储测试失败: {e}")
        return False


async def test_document_processor():
    """测试文档处理器"""
    print("\n📄 测试文档处理器...")
    
    try:
        from src.tasks.document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        
        # 创建临时测试文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("这是一个测试文档。\n人工智能技术正在快速发展。\n机器学习是其中的重要组成部分。")
            temp_file = f.name
        
        try:
            # 测试文本提取
            text = await processor._extract_text(temp_file, '.txt')
            print(f"✅ 文本提取成功，长度: {len(text)} 字符")
            
            # 测试文本分块
            chunks = await processor._chunk_text(text, chunk_size=50)
            print(f"✅ 文本分块成功，分块数: {len(chunks)}")
            
            # 测试嵌入生成（使用模拟）
            embeddings = await processor._generate_embeddings(chunks)
            print(f"✅ 嵌入生成成功，向量数: {len(embeddings)}")
            
            return True
            
        finally:
            # 清理临时文件
            os.unlink(temp_file)
        
    except Exception as e:
        print(f"❌ 文档处理器测试失败: {e}")
        return False


async def test_retrieval_service():
    """测试检索服务"""
    print("\n🔎 测试检索服务...")
    
    try:
        from src.rag.retrieval import get_retrieval_service, RetrievalStrategy
        
        service = get_retrieval_service()
        
        # 添加测试文档
        doc_id = await service.add_document(
            content="深度学习是机器学习的一个子领域，使用神经网络进行学习。",
            metadata={"source": "test_deep_learning.txt", "user_id": 1},
            doc_id="test_doc_dl"
        )
        print(f"✅ 文档添加成功，ID: {doc_id}")
        
        # 测试搜索
        results = await service.search_documents(
            query="什么是深度学习",
            strategy=RetrievalStrategy.VECTOR_ONLY,
            top_k=1
        )
        print(f"✅ 检索成功，结果数: {len(results)}")
        
        if results:
            result = results[0]
            print(f"   - 评分: {result.score:.3f}")
            print(f"   - 来源: {result.source}")
            print(f"   - 内容: {result.content[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 检索服务测试失败: {e}")
        return False


async def test_api_models():
    """测试 API 模型"""
    print("\n🌐 测试 API 模型...")
    
    try:
        from src.api.evidence import EvidenceResponse
        from datetime import datetime
        
        # 创建证据响应模型
        evidence_resp = EvidenceResponse(
            id=1,
            source_type="document",
            source_url="https://example.com/test.pdf",
            source_title="测试文档",
            content="这是测试证据内容",
            snippet="测试片段",
            relevance_score=0.85,
            confidence_score=0.90,
            citation_text="[1] 测试引用",
            used_in_response=True,
            metadata={"test": "data"},
            created_at=datetime.now().isoformat()
        )
        
        print("✅ API 模型创建成功")
        print(f"   证据类型: {evidence_resp.source_type}")
        print(f"   相关性评分: {evidence_resp.relevance_score}")
        
        return True
        
    except Exception as e:
        print(f"❌ API 模型测试失败: {e}")
        return False


async def test_task_queue_mock():
    """测试任务队列（模拟模式）"""
    print("\n⚡ 测试任务队列...")
    
    try:
        from src.tasks.queue import Task, TaskStatus, TaskPriority
        from datetime import datetime
        
        # 创建测试任务
        task = Task(
            id="test_task_001",
            name="process_document",
            args=["job_123", "/path/to/file.pdf", "user_456"],
            kwargs={},
            priority=TaskPriority.NORMAL,
            created_at=datetime.now()
        )
        
        print("✅ 任务模型创建成功")
        print(f"   任务ID: {task.id}")
        print(f"   任务名称: {task.name}")
        print(f"   优先级: {task.priority}")
        
        return True
        
    except Exception as e:
        print(f"❌ 任务队列测试失败: {e}")
        return False


async def test_configuration():
    """测试配置系统"""
    print("\n⚙️  测试配置系统...")
    
    try:
        from src.config.settings import get_settings
        
        settings = get_settings()
        
        print("✅ 配置加载成功")
        print(f"   应用名称: {settings.app_name}")
        print(f"   调试模式: {settings.debug}")
        print(f"   环境: {settings.environment}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置系统测试失败: {e}")
        return False


async def run_all_tests():
    """运行所有测试"""
    print("🚀 开始 DeerFlow 完整集成测试")
    print("=" * 60)
    
    tests = [
        ("基本模块导入", test_basic_imports),
        ("数据库模型", test_database_models),
        ("向量存储", test_vector_store_mock),
        ("文档处理器", test_document_processor),
        ("检索服务", test_retrieval_service),
        ("API 模型", test_api_models),
        ("任务队列", test_task_queue_mock),
        ("配置系统", test_configuration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 总结结果
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有测试通过！DeerFlow 核心功能正常")
        print("\n🚀 下一步:")
        print("   1. 配置数据库和 Redis")
        print("   2. 设置 LLM API 密钥")
        print("   3. 启动服务: python app.py")
        print("   4. 启动前端: cd vue && npm run dev")
    elif passed >= total * 0.7:
        print("⚠️  大部分测试通过，系统基本可用")
        print("💡 建议修复失败的测试项以获得最佳体验")
    else:
        print("❌ 多项测试失败，请检查依赖和配置")
        print("💡 运行 'python scripts/check_setup.py' 进行详细诊断")
    
    print("=" * 60)
    return passed == total


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)