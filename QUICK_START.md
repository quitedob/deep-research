# 智能对话编排系统 - 快速启动指南

## 🚀 5分钟快速开始

### 1. 启动应用

```bash
# 激活虚拟环境（如果有）
# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 启动应用
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 2. 访问API文档

打开浏览器访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. 测试智能对话

#### 方式1：使用Swagger UI
1. 访问 http://localhost:8000/docs
2. 找到 `POST /api/smart-chat`
3. 点击 "Try it out"
4. 输入请求体：
```json
{
  "message": "什么是机器学习？",
  "session_id": "test-session-001"
}
```
5. 点击 "Execute"

#### 方式2：使用curl
```bash
curl -X POST "http://localhost:8000/api/smart-chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "什么是机器学习？",
    "session_id": "test-session-001"
  }'
```

#### 方式3：使用Python
```python
import requests

response = requests.post(
    "http://localhost:8000/api/smart-chat",
    json={
        "message": "什么是机器学习？",
        "session_id": "test-session-001"
    }
)

result = response.json()
print(f"模式: {result['mode']}")
print(f"消息计数: {result['message_count']}")
print(f"响应: {result['content']}")
```

## 📊 查看监控数据

### 获取全局监控指标
```bash
curl "http://localhost:8000/api/monitor/global"
```

### 获取会话状态
```bash
curl "http://localhost:8000/api/chat/session/test-session-001/status"
```

### 获取性能统计
```bash
curl "http://localhost:8000/api/monitor/performance"
```

## 🧪 测试对话流程

### 测试1：普通模式（< 20条消息）

发送19条消息，观察模式保持为 "normal"：

```python
import requests

session_id = "test-session-001"

for i in range(1, 20):
    response = requests.post(
        "http://localhost:8000/api/smart-chat",
        json={
            "message": f"这是第{i}条消息",
            "session_id": session_id
        }
    )
    result = response.json()
    print(f"消息 #{i}: 模式={result['mode']}, 计数={result['message_count']}")
```

### 测试2：RAG增强模式（≥ 20条消息）

继续发送第20条消息，观察模式切换到 "rag_enhanced"：

```python
response = requests.post(
    "http://localhost:8000/api/smart-chat",
    json={
        "message": "这是第20条消息",
        "session_id": session_id
    }
)
result = response.json()
print(f"⚠️ 模式切换: {result['mode']}")  # 应该是 "rag_enhanced"
```

### 测试3：联网需求检测

发送需要实时信息的查询：

```python
response = requests.post(
    "http://localhost:8000/api/smart-chat",
    json={
        "message": "今天的天气怎么样？",
        "session_id": session_id
    }
)
result = response.json()
print(f"需要联网: {result['needs_network']}")  # 应该是 True
print(f"使用搜索: {result['search_used']}")
```

### 测试4：记忆摘要（≥ 50条消息）

发送50条消息后，系统会自动触发记忆摘要生成：

```python
# 发送50条消息
for i in range(20, 51):
    requests.post(
        "http://localhost:8000/api/smart-chat",
        json={
            "message": f"这是第{i}条消息",
            "session_id": session_id
        }
    )

# 查看会话状态
status = requests.get(
    f"http://localhost:8000/api/chat/session/{session_id}/status"
).json()

print(f"记忆摘要已触发: {status['memory_summary_triggered']}")
```

## 🎛️ 手动切换模式

### 切换到RAG增强模式
```bash
curl -X POST "http://localhost:8000/api/chat/session/test-session-001/switch-mode" \
  -H "Content-Type: application/json" \
  -d '{"mode": "rag_enhanced"}'
```

### 切换回普通模式
```bash
curl -X POST "http://localhost:8000/api/chat/session/test-session-001/switch-mode" \
  -H "Content-Type: application/json" \
  -d '{"mode": "normal"}'
```

## 💾 记忆管理

### 生成记忆摘要
```bash
curl -X POST "http://localhost:8000/api/memory/summary/generate" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-session-001"}'
```

### 获取记忆摘要
```bash
curl "http://localhost:8000/api/memory/summary/test-session-001"
```

### 获取所有摘要
```bash
curl "http://localhost:8000/api/memory/summaries"
```

### 获取记忆统计
```bash
curl "http://localhost:8000/api/memory/stats"
```

## 🔧 配置调整

### 修改消息阈值

编辑 `.env` 文件：
```bash
# 修改消息阈值为10条（默认20条）
DEEP_RESEARCH_SMART_CONVERSATION_MESSAGE_THRESHOLD=10

# 修改记忆阈值为30条（默认50条）
DEEP_RESEARCH_SMART_CONVERSATION_MEMORY_THRESHOLD=30
```

或编辑 `conf.yaml`：
```yaml
smart_conversation:
  message_threshold: 10
  memory_threshold: 30
```

重启应用使配置生效。

### 禁用自动RAG
```bash
DEEP_RESEARCH_SMART_CONVERSATION_ENABLE_AUTO_RAG=false
```

### 禁用自动搜索
```bash
DEEP_RESEARCH_SMART_CONVERSATION_ENABLE_AUTO_search=false
```

## 📈 监控仪表板

### 实时监控脚本

创建 `monitor.py`：
```python
import requests
import time

while True:
    # 获取全局指标
    metrics = requests.get("http://localhost:8000/api/monitor/global").json()
    
    print("\n" + "="*60)
    print("智能对话系统监控")
    print("="*60)
    print(f"活跃会话: {metrics['active_sessions']}")
    print(f"总消息数: {metrics['total_messages']}")
    print(f"RAG增强会话: {metrics['rag_enhanced_sessions']}")
    print(f"网络搜索次数: {metrics['network_searches']}")
    print(f"RAG搜索次数: {metrics['rag_searches']}")
    print(f"模式切换次数: {metrics['mode_switches']}")
    print(f"记忆摘要数: {metrics['memory_summaries']}")
    
    # 性能指标
    perf = metrics['performance']
    print(f"\n性能指标:")
    print(f"  平均消息处理时间: {perf['avg_message_processing_time']:.2f}s")
    print(f"  平均RAG搜索时间: {perf['avg_rag_search_time']:.2f}s")
    print(f"  平均网络搜索时间: {perf['avg_network_search_time']:.2f}s")
    
    time.sleep(5)  # 每5秒刷新
```

运行：
```bash
python monitor.py
```

## 🐛 故障排查

### 问题1：无法启动应用
```bash
# 检查依赖
pip install -r requirements.txt

# 检查数据库连接
# 确保PostgreSQL正在运行
```

### 问题2：API返回401错误
```bash
# 需要认证，先登录获取token
curl -X POST "http://localhost:8000/api/auth/login" \
  -d "username=your_username&password=your_password"

# 使用token访问API
curl "http://localhost:8000/api/smart-chat" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 问题3：RAG检索失败
```bash
# 检查向量数据库
# 确保pgvector扩展已安装
# 确保有文档已上传到知识库
```

### 问题4：联网搜索失败
```bash
# 检查搜索服务配置
# 确保API密钥已设置
# 检查网络连接
```

## 📚 更多资源

- **详细文档**: `SMART_CONVERSATION_IMPLEMENTATION.md`
- **实现总结**: `IMPLEMENTATION_SUMMARY.md`
- **TODO清单**: `todo.txt`
- **测试脚本**: `test_simple.py`

## 💡 使用技巧

### 技巧1：批量测试
```python
# 批量发送不同类型的消息
test_messages = [
    "什么是机器学习？",  # 通用知识
    "今天的天气怎么样？",  # 需要联网
    "最新的iPhone价格",  # 需要联网
    "如何学习Python？",  # 通用知识
]

for msg in test_messages:
    response = requests.post(
        "http://localhost:8000/api/smart-chat",
        json={"message": msg, "session_id": "test"}
    )
    result = response.json()
    print(f"{msg} → 联网:{result['needs_network']}, RAG:{result['rag_used']}")
```

### 技巧2：监控特定会话
```python
# 持续监控特定会话
session_id = "important-session"

while True:
    status = requests.get(
        f"http://localhost:8000/api/chat/session/{session_id}/status"
    ).json()
    
    print(f"会话 {session_id}:")
    print(f"  消息数: {status['message_count']}")
    print(f"  当前模式: {status['current_mode']}")
    
    time.sleep(10)
```

### 技巧3：性能分析
```python
import time

# 测试消息处理性能
start = time.time()

response = requests.post(
    "http://localhost:8000/api/smart-chat",
    json={"message": "测试消息", "session_id": "perf-test"}
)

elapsed = time.time() - start
print(f"处理时间: {elapsed:.2f}秒")
```

## 🎉 开始使用

现在你已经准备好使用智能对话编排系统了！

1. ✅ 启动应用
2. ✅ 测试基本功能
3. ✅ 查看监控数据
4. ✅ 调整配置
5. ✅ 开始开发

祝你使用愉快！🚀
