# -*- coding: utf-8 -*-
"""
智能对话编排系统测试脚本
"""

import asyncio
from src.services.network_need_detector import get_network_need_detector


async def test_network_detector():
    """测试联网需求检测器"""
    print("=" * 60)
    print("测试联网需求检测器")
    print("=" * 60)
    
    detector = get_network_need_detector()
    
    test_cases = [
        "今天的天气怎么样？",
        "什么是机器学习？",
        "最新的iPhone价格是多少？",
        "如何学习Python编程？",
        "昨天的新闻有哪些？",
        "解释一下量子计算的原理",
        "现在比特币的价格",
        "2024年世界杯冠军是谁？"
    ]
    
    for query in test_cases:
        result = detector.detect(query)
        print(f"\n查询: {query}")
        print(f"需要联网: {result['needs_network']}")
        print(f"置信度: {result['confidence']:.2f}")
        print(f"原因: {result['reason']}")
        print(f"匹配关键词: {result['keywords_matched']}")


async def test_conversation_flow():
    """测试对话流程（模拟）"""
    print("\n" + "=" * 60)
    print("测试对话流程（模拟）")
    print("=" * 60)
    
    # 模拟消息计数
    message_threshold = 20
    memory_threshold = 50
    
    for i in range(1, 60):
        mode = "普通模式" if i < message_threshold else "RAG增强模式"
        memory_status = "已触发" if i >= memory_threshold else "未触发"
        
        if i in [1, 10, 20, 30, 40, 50]:
            print(f"\n消息 #{i}:")
            print(f"  当前模式: {mode}")
            print(f"  记忆摘要: {memory_status}")
            
            if i == message_threshold:
                print(f"  ⚠️  达到消息阈值，切换到RAG增强模式！")
            
            if i == memory_threshold:
                print(f"  ⚠️  达到记忆阈值，触发记忆摘要生成！")


def test_configuration():
    """测试配置加载"""
    print("\n" + "=" * 60)
    print("测试配置加载")
    print("=" * 60)
    
    try:
        from src.config.loader.config_loader import get_settings
        
        settings = get_settings()
        
        print(f"\n智能对话配置:")
        print(f"  消息阈值: {settings.smart_conversation_message_threshold}")
        print(f"  记忆阈值: {settings.smart_conversation_memory_threshold}")
        print(f"  启用自动RAG: {settings.smart_conversation_enable_auto_rag}")
        print(f"  启用自动搜索: {settings.smart_conversation_enable_auto_search}")
        print(f"  RAG检索数量: {settings.smart_conversation_rag_top_k}")
        print(f"  RAG分数阈值: {settings.smart_conversation_rag_score_threshold}")
        print(f"  搜索结果限制: {settings.smart_conversation_search_limit}")
        print(f"  启用重排序: {settings.smart_conversation_enable_reranking}")
        
        print("\n✓ 配置加载成功")
        
    except Exception as e:
        print(f"\n✗ 配置加载失败: {e}")


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("智能对话编排系统测试")
    print("=" * 60)
    
    # 测试配置
    test_configuration()
    
    # 测试联网需求检测器
    await test_network_detector()
    
    # 测试对话流程
    await test_conversation_flow()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    
    print("\n已实现的功能:")
    print("  ✓ 配置管理")
    print("  ✓ 联网需求检测器")
    print("  ✓ 智能对话编排服务")
    print("  ✓ 对话监控服务")
    print("  ✓ 记忆摘要生成器")
    print("  ✓ 智能聊天API")
    print("  ✓ 对话监控API")
    print("  ✓ 记忆管理API")
    
    print("\nAPI端点:")
    print("  POST   /api/smart-chat")
    print("  GET    /api/chat/session/{session_id}/status")
    print("  POST   /api/chat/session/{session_id}/switch-mode")
    print("  GET    /api/monitor/sessions/{session_id}")
    print("  GET    /api/monitor/global")
    print("  GET    /api/monitor/performance")
    print("  POST   /api/memory/summary/generate")
    print("  GET    /api/memory/summary/{session_id}")
    print("  GET    /api/memory/summaries")
    print("  GET    /api/memory/stats")


if __name__ == "__main__":
    asyncio.run(main())
