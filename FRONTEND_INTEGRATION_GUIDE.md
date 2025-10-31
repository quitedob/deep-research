# 前端集成智能对话API指南

## 📋 概述

本指南说明如何将前端Vue应用与新实现的智能对话编排系统集成。

## 🔍 当前前端实现分析

### 现有聊天流程

**文件**: `vue/src/views/Home.vue`

当前实现使用 `/api/chat` 端点：

```javascript
const response = await fetch('/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: text,
    session_id: chatStore.activeSessionId,
    stream: true
  }),
  signal: controller.signal
});
```

### 现有API服务

**文件**: `vue/src/services/api.js`

```javascript
export const chatAPI = {
  sendMessage: (message) => apiRequest('/chat', {
    method: 'POST',
    body: JSON.stringify(message),
  }),
  // ...
};
```

## 🚀 集成新的智能对话API

### 方案1：渐进式升级（推荐）

保留现有 `/api/chat` 端点，同时添加新的智能对话功能。

#### 步骤1：在API服务中添加智能对话方法

**文件**: `vue/src/services/api.js`

```javascript
// 在 chatAPI 对象中添加
export const chatAPI = {
  // 现有方法...
  sendMessage: (message) => apiRequest('/chat', {
    method: 'POST',
    body: JSON.stringify(message),
  }),

  // 新增：智能对话
  sendSmartMessage: (message, sessionId, forceMode = null) => 
    apiRequest('/smart-chat', {
      method: 'POST',
      body: JSON.stringify({
        message: message,
        session_id: sessionId,
        force_mode: forceMode  // "normal" 或 "rag_enhanced"
      }),
    }),

  // 新增：获取会话状态
  getSessionStatus: (sessionId) => 
    apiRequest(`/chat/session/${sessionId}/status`),

  // 新增：切换对话模式
  switchMode: (sessionId, mode) => 
    apiRequest(`/chat/session/${sessionId}/switch-mode`, {
      method: 'POST',
      body: JSON.stringify({ mode }),
    }),
};

// 新增：对话监控API
export const monitorAPI = {
  // 获取会话监控指标
  getSessionMetrics: (sessionId) => 
    apiRequest(`/monitor/sessions/${sessionId}`),

  // 获取全局监控指标
  getGlobalMetrics: () => 
    apiRequest('/monitor/global'),

  // 获取性能统计
  getPerformanceStats: () => 
    apiRequest('/monitor/performance'),
};

// 新增：记忆管理API
export const memoryAPI = {
  // 生成记忆摘要
  generateSummary: (sessionId) => 
    apiRequest('/memory/summary/generate', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    }),

  // 获取记忆摘要
  getSummary: (sessionId) => 
    apiRequest(`/memory/summary/${sessionId}`),

  // 获取所有摘要
  getAllSummaries: () => 
    apiRequest('/memory/summaries'),

  // 获取记忆统计
  getStats: () => 
    apiRequest('/memory/stats'),
};
```

#### 步骤2：在Store中添加智能对话状态

**文件**: `vue/src/store/index.js`

```javascript
export const useChatStore = defineStore('chat', {
    state: () => ({
        // 现有状态...
        currentModel: 'ollama',
        messages: [],
        // ...

        // 新增：智能对话状态
        conversationMode: 'normal',  // 'normal' 或 'rag_enhanced'
        messageCount: 0,
        needsNetwork: false,
        ragUsed: false,
        searchUsed: false,
        sessionStatus: null,
        monitoringMetrics: null,
    }),
    actions: {
        // 现有actions...

        // 新增：发送智能消息
        async sendSmartMessage(text, forceMode = null) {
            try {
                const response = await chatAPI.sendSmartMessage(
                    text,
                    this.activeSessionId,
                    forceMode
                );

                // 更新状态
                this.conversationMode = response.mode;
                this.messageCount = response.message_count;
                this.needsNetwork = response.needs_network;
                this.ragUsed = response.rag_used;
                this.searchUsed = response.search_used;

                return response;
            } catch (error) {
                console.error('发送智能消息失败:', error);
                throw error;
            }
        },

        // 新增：获取会话状态
        async fetchSessionStatus() {
            if (!this.activeSessionId) return;

            try {
                const status = await chatAPI.getSessionStatus(this.activeSessionId);
                this.sessionStatus = status;
                this.conversationMode = status.current_mode;
                this.messageCount = status.message_count;
                return status;
            } catch (error) {
                console.error('获取会话状态失败:', error);
            }
        },

        // 新增：切换对话模式
        async switchConversationMode(mode) {
            if (!this.activeSessionId) return;

            try {
                const result = await chatAPI.switchMode(this.activeSessionId, mode);
                this.conversationMode = result.new_mode;
                return result;
            } catch (error) {
                console.error('切换模式失败:', error);
                throw error;
            }
        },

        // 新增：获取监控指标
        async fetchMonitoringMetrics() {
            try {
                const metrics = await monitorAPI.getGlobalMetrics();
                this.monitoringMetrics = metrics;
                return metrics;
            } catch (error) {
                console.error('获取监控指标失败:', error);
            }
        },
    }
});
```

#### 步骤3：更新Home.vue使用智能对话

**文件**: `vue/src/views/Home.vue`

```javascript
// 修改 handleSendMessage 函数
const handleSendMessage = async (text) => {
  if (!text.trim()) return;

  const controller = new AbortController();
  chatStore.setCurrentRequestController(controller);

  const startTime = performance.now();

  // 添加用户消息
  chatStore.addMessage({
    role: 'user',
    content: text,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  });

  const assistantMessageId = chatStore.addMessage({
    role: 'assistant',
    content: null,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  });

  chatStore.setTypingStatus(true);

  try {
    // 使用智能对话API
    const response = await chatStore.sendSmartMessage(text);

    // 更新助手消息
    chatStore.updateMessageContent({
      messageId: assistantMessageId,
      contentChunk: response.content
    });

    // 显示模式和来源信息
    if (response.mode === 'rag_enhanced') {
      console.log('🔍 RAG增强模式已启用');
    }
    if (response.rag_used) {
      console.log('📚 使用了知识库检索');
    }
    if (response.search_used) {
      console.log('🌐 使用了联网搜索');
    }

    // 完成处理
    const endTime = performance.now();
    const duration = ((endTime - startTime) / 1000).toFixed(1);
    chatStore.setMessageDuration(assistantMessageId, duration);
    chatStore.setTypingStatus(false);
    chatStore.setCurrentRequestController(null);

    // 刷新会话状态
    await chatStore.fetchSessionStatus();

    // 刷新历史记录
    if (!chatStore.activeSessionId) {
      chatStore.fetchHistoryList();
    }

  } catch (error) {
    if (error.name === 'AbortError') {
      chatStore.setTypingStatus(false);
      chatStore.setCurrentRequestController(null);
      return;
    }

    const errorMessage = handleAPIError(error);
    chatStore.updateMessageContent({
      messageId: assistantMessageId,
      contentChunk: `**错误:** ${errorMessage}`
    });
    const endTime = performance.now();
    const duration = ((endTime - startTime) / 1000).toFixed(1);
    chatStore.setMessageDuration(assistantMessageId, duration);
    chatStore.setTypingStatus(false);
    chatStore.setCurrentRequestController(null);
  }
};
```

#### 步骤4：添加模式切换UI组件

创建新组件 `vue/src/components/ConversationModeToggle.vue`:

```vue
<template>
  <div class="mode-toggle">
    <div class="mode-info">
      <span class="mode-label">对话模式:</span>
      <span class="mode-value" :class="modeClass">
        {{ modeText }}
      </span>
      <span class="message-count">
        ({{ messageCount }}/{{ threshold }})
      </span>
    </div>

    <button 
      v-if="canSwitch" 
      @click="toggleMode" 
      class="switch-btn"
      :disabled="switching"
    >
      {{ switching ? '切换中...' : '切换模式' }}
    </button>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useChatStore } from '@/store';

const chatStore = useChatStore();
const switching = ref(false);

const threshold = 20;  // 消息阈值

const modeText = computed(() => {
  return chatStore.conversationMode === 'rag_enhanced' 
    ? 'RAG增强模式' 
    : '普通模式';
});

const modeClass = computed(() => {
  return chatStore.conversationMode === 'rag_enhanced' 
    ? 'mode-enhanced' 
    : 'mode-normal';
});

const messageCount = computed(() => chatStore.messageCount || 0);

const canSwitch = computed(() => {
  return chatStore.activeSessionId && !chatStore.isTyping;
});

const toggleMode = async () => {
  if (switching.value) return;

  switching.value = true;
  try {
    const newMode = chatStore.conversationMode === 'normal' 
      ? 'rag_enhanced' 
      : 'normal';
    
    await chatStore.switchConversationMode(newMode);
    
    // 显示通知
    console.log(`已切换到${newMode === 'rag_enhanced' ? 'RAG增强' : '普通'}模式`);
  } catch (error) {
    console.error('切换模式失败:', error);
  } finally {
    switching.value = false;
  }
};
</script>

<style scoped>
.mode-toggle {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--secondary-bg);
  border-radius: var(--radius-medium);
  font-size: 14px;
}

.mode-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.mode-label {
  color: var(--text-secondary);
}

.mode-value {
  font-weight: 600;
  padding: 2px 8px;
  border-radius: var(--radius-small);
}

.mode-normal {
  color: var(--accent-blue);
  background: rgba(0, 122, 255, 0.1);
}

.mode-enhanced {
  color: var(--accent-green);
  background: rgba(52, 199, 89, 0.1);
}

.message-count {
  color: var(--text-tertiary);
  font-size: 12px;
}

.switch-btn {
  padding: 4px 12px;
  border: 1px solid var(--border-color);
  background: var(--primary-bg);
  color: var(--text-primary);
  border-radius: var(--radius-small);
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s ease;
}

.switch-btn:hover:not(:disabled) {
  background: var(--secondary-bg);
  border-color: var(--accent-blue);
}

.switch-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
```

#### 步骤5：在ChatContainer中添加模式显示

**文件**: `vue/src/components/ChatContainer.vue`

```vue
<template>
  <div class="chat-container">
    <div class="chat-header">
      <ModelSelector />
      <!-- 新增：对话模式切换 -->
      <ConversationModeToggle />
      <UserProfileMenu :current-theme="currentTheme" @toggle-theme="$emit('toggle-theme')" />
    </div>
    <!-- 其余内容保持不变 -->
  </div>
</template>

<script setup>
// 添加导入
import ConversationModeToggle from './ConversationModeToggle.vue';
// ...
</script>
```

### 方案2：完全替换（激进）

直接将所有聊天请求切换到智能对话API。

**优点**:
- 所有对话都享受智能编排功能
- 代码更简洁

**缺点**:
- 需要更多测试
- 可能影响现有功能

## 📊 添加监控面板

创建新组件 `vue/src/components/ConversationMonitor.vue`:

```vue
<template>
  <div class="monitor-panel">
    <h3>对话监控</h3>
    
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-label">活跃会话</div>
        <div class="metric-value">{{ metrics?.active_sessions || 0 }}</div>
      </div>

      <div class="metric-card">
        <div class="metric-label">总消息数</div>
        <div class="metric-value">{{ metrics?.total_messages || 0 }}</div>
      </div>

      <div class="metric-card">
        <div class="metric-label">RAG增强会话</div>
        <div class="metric-value">{{ metrics?.rag_enhanced_sessions || 0 }}</div>
      </div>

      <div class="metric-card">
        <div class="metric-label">网络搜索次数</div>
        <div class="metric-value">{{ metrics?.network_searches || 0 }}</div>
      </div>
    </div>

    <div class="performance-stats" v-if="metrics?.performance">
      <h4>性能指标</h4>
      <div class="stat-item">
        <span>平均消息处理时间:</span>
        <span>{{ metrics.performance.avg_message_processing_time?.toFixed(2) }}s</span>
      </div>
      <div class="stat-item">
        <span>平均RAG搜索时间:</span>
        <span>{{ metrics.performance.avg_rag_search_time?.toFixed(2) }}s</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { monitorAPI } from '@/services/api';

const metrics = ref(null);
let intervalId = null;

const fetchMetrics = async () => {
  try {
    metrics.value = await monitorAPI.getGlobalMetrics();
  } catch (error) {
    console.error('获取监控指标失败:', error);
  }
};

onMounted(() => {
  fetchMetrics();
  // 每5秒刷新一次
  intervalId = setInterval(fetchMetrics, 5000);
});

onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId);
  }
});
</script>

<style scoped>
.monitor-panel {
  padding: var(--spacing-lg);
  background: var(--secondary-bg);
  border-radius: var(--radius-large);
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: var(--spacing-md);
  margin-top: var(--spacing-md);
}

.metric-card {
  padding: var(--spacing-md);
  background: var(--primary-bg);
  border-radius: var(--radius-medium);
  text-align: center;
}

.metric-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-sm);
}

.metric-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--accent-blue);
}

.performance-stats {
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-lg);
  border-top: 1px solid var(--border-color);
}

.stat-item {
  display: flex;
  justify-content: space-between;
  padding: var(--spacing-sm) 0;
  font-size: 14px;
}
</style>
```

## 🎯 集成检查清单

### 必须实现
- [ ] 在 `api.js` 中添加智能对话API方法
- [ ] 在 store 中添加智能对话状态
- [ ] 更新 `Home.vue` 使用智能对话API
- [ ] 测试基本聊天功能

### 推荐实现
- [ ] 添加模式切换UI组件
- [ ] 在ChatContainer中显示当前模式
- [ ] 添加消息计数显示
- [ ] 显示RAG/搜索使用状态

### 可选实现
- [ ] 添加监控面板组件
- [ ] 添加记忆摘要查看功能
- [ ] 添加性能统计显示
- [ ] 添加模式切换动画效果

## 🧪 测试建议

### 1. 基本功能测试
```javascript
// 测试发送消息
await chatStore.sendSmartMessage("测试消息");

// 测试获取会话状态
const status = await chatStore.fetchSessionStatus();
console.log('会话状态:', status);

// 测试切换模式
await chatStore.switchConversationMode('rag_enhanced');
```

### 2. 模式切换测试
```javascript
// 发送20条消息，观察模式自动切换
for (let i = 1; i <= 20; i++) {
  await chatStore.sendSmartMessage(`测试消息 ${i}`);
  const status = await chatStore.fetchSessionStatus();
  console.log(`消息 #${i}: 模式=${status.current_mode}`);
}
```

### 3. 监控测试
```javascript
// 获取监控指标
const metrics = await monitorAPI.getGlobalMetrics();
console.log('监控指标:', metrics);

// 获取性能统计
const performance = await monitorAPI.getPerformanceStats();
console.log('性能统计:', performance);
```

## 📝 注意事项

1. **向后兼容**: 保留现有 `/api/chat` 端点，确保不影响现有功能
2. **错误处理**: 添加适当的错误处理和用户提示
3. **加载状态**: 显示加载指示器，提升用户体验
4. **性能优化**: 避免频繁请求监控API，使用合理的刷新间隔
5. **用户体验**: 模式切换应该平滑，有适当的视觉反馈

## 🚀 部署建议

1. **开发环境**: 先在开发环境测试所有功能
2. **灰度发布**: 可以添加功能开关，逐步启用智能对话功能
3. **监控告警**: 设置监控告警，及时发现问题
4. **用户反馈**: 收集用户反馈，持续优化

## 📚 相关文档

- 后端API文档: `SMART_CONVERSATION_IMPLEMENTATION.md`
- 快速启动: `QUICK_START.md`
- 验证清单: `VERIFICATION_CHECKLIST.md`
