# 智能对话编排系统实现文档

## 概述

本文档描述了智能对话编排系统的实现，该系统根据流程图要求实现了以下核心功能：

1. **消息量检测**：自动检测对话消息数量，达到阈值时切换模式
2. **RAG增强模式**：自动触发知识库检索增强回答
3. **联网需求检测**：智能判断是否需要实时信息
4. **记忆摘要管理**：自动生成对话摘要并存储到长期记忆
5. **实时监控**：全面监控对话状态和性能指标

## 架构设计

### 核心组件

```
┌─────────────────────────────────────────────────────────────┐
│                    智能对话编排系统                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │  消息计数器      │      │  模式切换器      │            │
│  │  (Message        │─────▶│  (Mode           │            │
│  │   Counter)       │      │   Switcher)      │            │
│  └──────────────────┘      └──────────────────┘            │
│           │                         │                        │
│           ▼                         ▼                        │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │  联网需求检测器  │      │  RAG检索器       │            │
│  │  (Network Need   │      │  (RAG            │            │
│  │   Detector)      │      │   Retriever)     │            │
│  └──────────────────┘      └──────────────────┘            │
│           │                         │                        │
│           ▼                         ▼                        │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │  搜索集成器      │      │  上下文构建器    │            │
│  │  (Search         │      │  (Context        │            │
│  │   Integrator)    │      │   Builder)       │            │
│  └──────────────────┘      └──────────────────┘            │
│           │                         │                        │
│           └─────────┬───────────────┘                        │
│                     ▼                                        │
│           ┌──────────────────┐                              │
│           │  LLM响应生成器   │                              │
│           │  (LLM Response   │                              │
│           │   Generator)     │                              │
│           └──────────────────┘                              │
│                     │                                        │
│                     ▼                                        │
│           ┌──────────────────┐                              │
│           │  记忆摘要生成器  │                              │
│           │  (Memory         │                              │
│           │   Summarizer)    │                              │
│           └──────────────────┘                              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 已实现的功能

### 1. 配置管理 (✓)

**文件**: `src/config/loader/config_loader.py`

新增配置项：
```python
# 智能对话编排配置
smart_conversation_message_threshold: int = 20  # 触发RAG增强的消息数阈值
smart_conversation_memory_threshold: int = 50   # 触发记忆摘要的消息数阈值
smart_conversation_enable_auto_rag: bool = True # 启用自动RAG增强
smart_conversation_enable_auto_search: bool = True # 启用自动联网搜索
smart_conversation_rag_top_k: int = 5          # RAG检索返回结果数
smart_conversation_rag_score_threshold: float = 0.3 # RAG检索分数阈值
smart_conversation_search_limit: int = 10      # 联网搜索结果数限制
smart_conversation_enable_reranking: bool = True # 启用重排序
```

### 2. 联网需求检测器 (✓)

**文件**: `src/services/network_need_detector.py`

**功能**:
- 时间相关关键词检测（今天、最近、最新等）
- 新闻事件关键词检测
- 价格/股票关键词检测
- 天气关键词检测
- 体育赛事关键词检测
- 技术/产品发布关键词检测
- 本地知识关键词检测（用于判断不需要联网）
- 日期模式识别

**使用示例**:
```python
from src.services.network_need_detector import get_network_need_detector

detector = get_network_need_detector()
result = detector.detect("今天的天气怎么样？")

# 返回结果
{
    "needs_network": True,
    "confidence": 0.85,
    "reason": "包含时间相关关键词; 查询天气信息",
    "keywords_matched": ["今天", "天气"],
    "scores": {
        "time": 0.33,
        "weather": 1.0,
        "total": 0.85
    }
}
```

### 3. 智能对话编排服务 (✓)

**文件**: `src/services/smart_conversation_service.py`

**核心功能**:

#### 3.1 消息计数和模式切换
```python
# 自动检测消息数量
if message_count >= self.message_threshold:  # 默认20条
    # 切换到RAG增强模式
    current_mode = ConversationMode.RAG_ENHANCED
```

#### 3.2 对话模式
- **普通模式** (`NORMAL`): 基础LLM对话，可选联网搜索
- **RAG增强模式** (`RAG_ENHANCED`): 知识库检索 + 联网搜索 + LLM生成

#### 3.3 处理流程
```python
async def process_message(user_id, session_id, message):
    # 1. 更新消息计数
    # 2. 确定对话模式（普通/RAG增强）
    # 3. 检测联网需求
    # 4. 执行RAG检索（如果在RAG模式）
    # 5. 执行联网搜索（如果需要）
    # 6. 生成LLM响应
    # 7. 检查记忆阈值
    # 8. 触发记忆摘要（如果达到阈值）
```

**使用示例**:
```python
from src.services.smart_conversation_service import get_smart_conversation_service

service = get_smart_conversation_service(db_session)

result = await service.process_message(
    user_id="user123",
    session_id="session456",
    message="什么是机器学习？"
)

# 返回结果
{
    "success": True,
    "content": "机器学习是...",
    "mode": "rag_enhanced",
    "message_count": 25,
    "needs_network": False,
    "rag_used": True,
    "search_used": False,
    "sources": [...]
}
```

### 4. 对话监控服务 (✓)

**文件**: `src/services/conversation_monitor.py`

**监控指标**:
- 会话级指标：消息计数、当前模式、RAG搜索次数、网络搜索次数、模式切换次数
- 全局指标：总会话数、总消息数、RAG增强会话数、搜索次数、记忆摘要数
- 性能指标：消息处理时间、RAG搜索时间、网络搜索时间、记忆摘要时间

**使用示例**:
```python
from src.services.conversation_monitor import get_conversation_monitor

monitor = get_conversation_monitor()

# 跟踪消息
await monitor.track_message(
    session_id="session456",
    user_id="user123",
    message_count=25,
    mode="rag_enhanced",
    processing_time=1.5
)

# 获取全局指标
metrics = await monitor.get_global_metrics()
```

### 5. 记忆摘要生成器 (✓)

**文件**: `src/services/memory_summarizer.py`

**功能**:
- 提取对话主题
- 提取关键要点
- 分析用户偏好
- 生成摘要文本

**使用示例**:
```python
from src.services.memory_summarizer import get_memory_summarizer

summarizer = get_memory_summarizer()

result = await summarizer.generate_summary(
    session_id="session456",
    messages=messages,
    user_id="user123"
)

# 返回结果
{
    "success": True,
    "summary": {
        "summary_text": "本次对话主要讨论了...",
        "topics": ["机器学习", "深度学习", "神经网络"],
        "key_points": ["...", "...", "..."],
        "user_preferences": {
            "message_style": "详细",
            "avg_message_length": 150
        }
    }
}
```

## API端点

### 1. 智能聊天API

**文件**: `src/api/chat.py`

#### POST `/api/smart-chat`
智能对话接口，自动根据消息数量切换模式

**请求**:
```json
{
    "message": "什么是机器学习？",
    "session_id": "session456",
    "force_mode": "rag_enhanced"  // 可选
}
```

**响应**:
```json
{
    "success": true,
    "content": "机器学习是...",
    "mode": "rag_enhanced",
    "message_count": 25,
    "needs_network": false,
    "rag_used": true,
    "search_used": false,
    "sources": [...],
    "metadata": {...}
}
```

#### GET `/api/chat/session/{session_id}/status`
获取会话状态

**响应**:
```json
{
    "session_id": "session456",
    "message_count": 25,
    "current_mode": "rag_enhanced",
    "mode_switched": true,
    "memory_summary_triggered": false,
    "thresholds": {
        "message_threshold": 20,
        "memory_threshold": 50
    }
}
```

#### POST `/api/chat/session/{session_id}/switch-mode`
手动切换对话模式

**请求**:
```json
{
    "mode": "rag_enhanced"
}
```

### 2. 对话监控API

**文件**: `src/api/conversation_monitor.py`

#### GET `/api/monitor/sessions/{session_id}`
获取会话监控指标

#### GET `/api/monitor/sessions`
获取所有会话监控指标

#### GET `/api/monitor/global`
获取全局监控指标

#### GET `/api/monitor/performance`
获取性能统计数据

### 3. 记忆管理API

**文件**: `src/api/memory.py`

#### POST `/api/memory/summary/generate`
生成记忆摘要

#### GET `/api/memory/summary/{session_id}`
获取会话摘要

#### GET `/api/memory/summaries`
获取所有摘要

#### DELETE `/api/memory/summary/{session_id}`
删除摘要

#### GET `/api/memory/stats`
获取记忆统计信息

## 流程图实现对照

### ✓ 用户输入消息
- 通过 `/api/smart-chat` 接口接收

### ✓ 消息量检测
- `SmartConversationService._get_session_state()` 获取消息计数
- `SmartConversationService._determine_mode()` 判断是否达到阈值（20条）

### ✓ 普通对话模式 vs RAG增强模式
- 小于20条：`ConversationMode.NORMAL`
- 达到20条：`ConversationMode.RAG_ENHANCED`

### ✓ 联网需求检测
- `NetworkNeedDetector.detect()` 分析查询内容
- 检测时间敏感性、新闻事件、价格信息等

### ✓ 知识库检索
- `SmartConversationService._perform_rag_search()` 执行向量搜索
- 支持两阶段检索和重排序

### ✓ 网络搜索
- `SmartConversationService._perform_web_search()` 调用统一搜索服务
- 支持多个搜索提供商（Doubao/Kimi）

### ✓ 上下文增强生成
- `SmartConversationService._generate_llm_response()` 整合所有上下文
- 构建增强提示词并调用LLM

### ✓ 对话历史存储
- `ConversationService.add_message()` 存储消息到数据库

### ✓ 记忆阈值检测
- 检查消息数是否达到记忆阈值（50条）
- `SmartConversationService._trigger_memory_summary()` 触发摘要生成

### ✓ 监控系统
- **消息计数器监控**: `ConversationMonitor.track_message()`
- **RAG状态监控**: `ConversationMonitor.track_rag_search()`
- **网络连接监控**: `ConversationMonitor.track_network_search()`

## 配置说明

### 环境变量

```bash
# 智能对话配置
DEEP_RESEARCH_SMART_CONVERSATION_MESSAGE_THRESHOLD=20
DEEP_RESEARCH_SMART_CONVERSATION_MEMORY_THRESHOLD=50
DEEP_RESEARCH_SMART_CONVERSATION_ENABLE_AUTO_RAG=true
DEEP_RESEARCH_SMART_CONVERSATION_ENABLE_AUTO_SEARCH=true
DEEP_RESEARCH_SMART_CONVERSATION_RAG_TOP_K=5
DEEP_RESEARCH_SMART_CONVERSATION_RAG_SCORE_THRESHOLD=0.3
DEEP_RESEARCH_SMART_CONVERSATION_SEARCH_LIMIT=10
DEEP_RESEARCH_SMART_CONVERSATION_ENABLE_RERANKING=true
```

### conf.yaml 配置

```yaml
smart_conversation:
  message_threshold: 20
  memory_threshold: 50
  enable_auto_rag: true
  enable_auto_search: true
  rag_top_k: 5
  rag_score_threshold: 0.3
  search_limit: 10
  enable_reranking: true
```

## 使用示例

### 前端集成示例

```javascript
// 发送智能聊天消息
async function sendSmartMessage(message, sessionId) {
    const response = await fetch('/api/smart-chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            message: message,
            session_id: sessionId
        })
    });
    
    const result = await response.json();
    
    console.log('模式:', result.mode);
    console.log('消息计数:', result.message_count);
    console.log('使用RAG:', result.rag_used);
    console.log('使用搜索:', result.search_used);
    
    return result;
}

// 获取会话状态
async function getSessionStatus(sessionId) {
    const response = await fetch(`/api/chat/session/${sessionId}/status`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    return await response.json();
}

// 获取监控指标
async function getMonitoringMetrics() {
    const response = await fetch('/api/monitor/global', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    return await response.json();
}
```

## 性能优化

1. **会话状态缓存**: 使用内存缓存减少数据库查询
2. **异步处理**: 记忆摘要生成使用后台任务
3. **批量操作**: 监控数据批量更新
4. **连接池**: 数据库和Redis连接池管理

## 扩展性

系统设计支持以下扩展：

1. **自定义检测器**: 可以添加更多的需求检测器
2. **多种RAG策略**: 支持不同的检索和重排序策略
3. **多LLM提供商**: 支持切换不同的LLM服务
4. **长期记忆存储**: 可扩展到数据库持久化
5. **实时推送**: 可集成WebSocket实时推送监控数据

## 测试建议

1. **单元测试**: 测试各个服务的核心功能
2. **集成测试**: 测试完整的对话流程
3. **性能测试**: 测试高并发场景
4. **边界测试**: 测试阈值边界情况

## 已知限制

1. 会话状态目前存储在内存中，重启后会丢失
2. 记忆摘要目前存储在内存中，需要扩展到数据库
3. 监控数据没有持久化
4. 缺少WebSocket实时推送功能

## 后续优化方向

1. 将会话状态持久化到Redis
2. 将记忆摘要存储到数据库
3. 添加监控数据持久化
4. 实现WebSocket实时推送
5. 添加更多的智能检测策略
6. 优化RAG检索性能
7. 添加A/B测试功能
8. 实现对话质量评估

## 总结

智能对话编排系统已经完整实现了流程图中的所有核心功能：

✓ 消息量检测（20条阈值）
✓ 对话模式切换（普通/RAG增强）
✓ 联网需求检测
✓ RAG知识库检索
✓ 网络搜索集成
✓ 上下文增强生成
✓ 记忆摘要管理（50条阈值）
✓ 全面监控系统

系统已经可以投入使用，并支持进一步的扩展和优化。
