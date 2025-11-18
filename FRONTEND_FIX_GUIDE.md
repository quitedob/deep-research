# 前端 SSE 接收修复指南

## 问题分析

### 当前状态

1. **Home.vue** - ✅ 已经正确实现 SSE 接收
   - 正确监听 `completed` 事件
   - 从 `data.data.report_text` 获取完整报告
   - 不显示中间过程

2. **ResearchButton.vue** - ❌ 使用了错误的事件结构
   - 期望接收 `node_start`, `agent_thought`, `tool_call` 等事件
   - 这些是内部过程，不应该暴露给前端

3. **api.js** - ❌ `subscribeToResearchEvents` 未实现

## AgentScope 输出结构（根据官方文档）

### Msg 对象
```python
class Msg:
    name: str  # 发送者名称
    role: Literal["user", "assistant", "system"]
    content: str | list[ContentBlock]  # 可能是字符串或列表
    metadata: dict
    timestamp: str
```

### ContentBlock 结构
```python
class ContentBlock:
    type: str  # "text", "image", "url" 等
    text: str  # 文本内容（如果是文本类型）
    # 其他字段...
```

## 后端 SSE 事件结构（已实现）

### 1. connected - 连接成功
```json
{
  "type": "connected",
  "session_id": "xxx"
}
```

### 2. status_update - 状态更新
```json
{
  "type": "status_update",
  "status": "in_progress",
  "data": {
    "progress": {
      "tools_used": ["web_search", "wikipedia"],
      "findings_count": 5
    }
  }
}
```

### 3. completed - 研究完成（包含完整报告）
```json
{
  "type": "completed",
  "status": "completed",
  "data": {
    "report_text": "# 完整的 Markdown 报告...",
    "session_id": "xxx"
  }
}
```

### 4. failed/error - 失败
```json
{
  "type": "failed",
  "status": "failed",
  "error": "错误信息"
}
```

## 修复方案

### 1. Home.vue - ✅ 无需修改

当前实现已经正确：

```javascript
eventSource.onmessage = async (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'completed') {
    const reportText = data.data?.report_text || '研究完成，但报告为空。';
    // 显示完整报告
    chatStore.updateMessageContent({
      messageId: assistantMessageId,
      contentChunk: reportText,
      metadata: {
        type: 'research',
        session_id: data.data?.session_id
      }
    });
  }
};
```

### 2. ResearchButton.vue - ❌ 需要重写

**问题**：
- 期望接收不存在的事件类型（`node_start`, `agent_thought` 等）
- 这些是 AgentScope 内部的执行过程，不应该暴露

**修复方案**：
使用与 Home.vue 相同的 SSE 接收逻辑

### 3. api.js - ❌ 需要实现

**问题**：
- `subscribeToResearchEvents` 函数未实现
- 返回的是普通 API 请求，不是 EventSource

**修复方案**：
实现正确的 EventSource 连接

## 完整修复代码

### 修复 api.js

```javascript
/**
 * 订阅研究事件流（SSE）
 * @param {string} sessionId - 研究会话ID
 * @param {function} onMessage - 消息处理回调
 * @param {function} onError - 错误处理回调
 * @returns {EventSource} EventSource 实例
 */
export const subscribeToResearchEvents = (sessionId, onMessage, onError) => {
  const eventSource = new EventSource(
    `${API_BASE_URL}/api/research/stream/${sessionId}`
  );

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (onMessage) {
        onMessage(data);
      }
    } catch (error) {
      console.error('解析 SSE 消息失败:', error);
      if (onError) {
        onError(error);
      }
    }
  };

  eventSource.onerror = (error) => {
    console.error('SSE 连接错误:', error);
    if (onError) {
      onError(error);
    }
  };

  return eventSource;
};
```

### 修复 ResearchButton.vue

```vue
<script setup>
import { ref, computed } from 'vue';
import { useChatStore } from '@/store';
import { startResearch as apiStartResearch, subscribeToResearchEvents, handleAPIError } from '@/services/api.js';

const props = defineProps({
  message: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['research-complete', 'research-error']);

const chatStore = useChatStore();
const isResearching = ref(false);
const researchProgress = ref('');
const researchEventSource = ref(null);
const currentSessionId = ref(null);

const buttonTitle = computed(() => {
  if (!props.message.trim()) {
    return '请先输入要研究的内容';
  }
  if (isResearching.value) {
    return '正在进行深度研究...';
  }
  return '启动Agentic RAG深度研究，获取更全面的信息';
});

// 启动研究
const startResearch = async () => {
  if (isResearching.value || !props.message.trim()) return;
  
  isResearching.value = true;
  researchProgress.value = '🚀 研究任务已启动，正在初始化...';
  
  try {
    // 启动研究任务
    const response = await apiStartResearch(props.message);
    currentSessionId.value = response.session_id;
    
    // 订阅事件流
    researchEventSource.value = subscribeToResearchEvents(
      response.session_id,
      handleResearchEvent,
      handleResearchError
    );
    
  } catch (error) {
    console.error('启动研究失败:', error);
    const errorMessage = handleAPIError(error);
    researchProgress.value = `❌ 启动失败: ${errorMessage}`;
    emit('research-error', errorMessage);
    isResearching.value = false;
  }
};

// 处理研究事件
const handleResearchEvent = (data) => {
  console.log('收到 SSE 事件:', data.type);
  
  switch (data.type) {
    case 'connected':
      researchProgress.value = '✓ 已连接，等待研究结果...';
      break;
      
    case 'status_update':
      if (data.status === 'in_progress') {
        const progress = data.data?.progress || {};
        let msg = '🔍 正在进行深度研究...\n';
        
        if (progress.tools_used && progress.tools_used.length > 0) {
          msg += `使用工具: ${progress.tools_used.join(', ')}\n`;
        }
        
        if (progress.findings_count > 0) {
          msg += `已发现: ${progress.findings_count} 条信息`;
        }
        
        researchProgress.value = msg;
      }
      break;
      
    case 'completed':
      console.log('✓ 研究完成，收到最终报告');
      const reportText = data.data?.report_text || '研究完成，但报告为空。';
      completeResearch(reportText);
      break;
      
    case 'failed':
    case 'error':
      console.error('✗ 研究失败:', data.error);
      researchProgress.value = `❌ 研究失败: ${data.error || '未知错误'}`;
      emit('research-error', data.error);
      isResearching.value = false;
      if (researchEventSource.value) {
        researchEventSource.value.close();
        researchEventSource.value = null;
      }
      break;
  }
};

// 处理研究错误
const handleResearchError = (error) => {
  console.error('研究事件流错误:', error);
  const errorMessage = handleAPIError(error);
  researchProgress.value = `❌ 连接错误: ${errorMessage}`;
  emit('research-error', errorMessage);
  isResearching.value = false;
};

// 完成研究
const completeResearch = (report) => {
  isResearching.value = false;
  researchProgress.value = '✓ 研究完成！';
  
  if (researchEventSource.value) {
    researchEventSource.value.close();
    researchEventSource.value = null;
  }
  
  // 将研究报告添加到聊天
  chatStore.addMessage({
    role: 'assistant',
    content: report,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    type: 'research_report'
  });
  
  emit('research-complete', report);
  
  // 3秒后清除进度显示
  setTimeout(() => {
    researchProgress.value = '';
  }, 3000);
};

// 取消研究
const cancelResearch = () => {
  if (researchEventSource.value) {
    researchEventSource.value.close();
    researchEventSource.value = null;
  }
  
  isResearching.value = false;
  researchProgress.value = '❌ 研究已取消';
  
  setTimeout(() => {
    researchProgress.value = '';
  }, 2000);
};
</script>
```

## 关键修改点

### 1. 不再显示内部过程
- ❌ 删除：`node_start`, `agent_thought`, `tool_call` 等事件处理
- ✅ 只显示：连接状态、进度更新、最终报告

### 2. 统一事件结构
- 所有前端组件使用相同的 SSE 事件类型
- 与后端 API 完全匹配

### 3. 简化进度显示
- 不显示详细的工具调用过程
- 只显示高层次的进度信息（工具数量、发现数量）

## 测试验证

### 1. 启动研究
```javascript
// 应该看到
✓ 已连接，等待研究结果...
```

### 2. 研究进行中
```javascript
// 应该看到
🔍 正在进行深度研究...
使用工具: web_search, wikipedia
已发现: 5 条信息
```

### 3. 研究完成
```javascript
// 应该看到完整的 Markdown 报告
# 深度研究报告

**研究主题**: 今日金价快速研究
...
```

## 总结

**后端**：✅ 已正确实现
- 生成完整报告
- 通过 SSE 推送 `completed` 事件
- 包含 `report_text` 字段

**前端**：
- Home.vue: ✅ 已正确实现
- ResearchButton.vue: ❌ 需要修复（使用错误的事件结构）
- api.js: ❌ 需要实现 `subscribeToResearchEvents`

**核心原则**：
1. 前端只接收高层次的事件（连接、进度、完成、失败）
2. 不显示 AgentScope 内部的执行细节
3. 最终报告通过 `completed` 事件的 `report_text` 字段获取
