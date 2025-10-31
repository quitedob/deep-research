# 前端集成智能对话系统 - TODO清单

## 📋 概述

前端当前使用 `/api/chat` 端点进行对话，需要集成新的智能对话编排系统以支持：
- 自动模式切换（普通模式 ↔ RAG增强模式）
- 联网需求检测
- 消息计数显示
- 对话监控
- 记忆摘要管理

## 🎯 核心修改（必须）

### 1. 更新API服务 ✅ 推荐优先级：P0

**文件**: `vue/src/services/api.js`

**需要添加**:
```javascript
// 智能对话API
export const chatAPI = {
  // 现有方法保持不变...
  
  // 新增方法
  sendSmartMessage: (message, sessionId, forceMode = null) => 
    apiRequest('/smart-chat', {
      method: 'POST',
      body: JSON.stringify({
        message: message,
        session_id: sessionId,
        force_mode: forceMode
      }),
    }),

  getSessionStatus: (sessionId) => 
    apiRequest(`/chat/session/${sessionId}/status`),

  switchMode: (sessionId, mode) => 
    apiRequest(`/chat/session/${sessionId}/switch-mode`, {
      method: 'POST',
      body: JSON.stringify({ mode }),
    }),
};

// 监控API
export const monitorAPI = {
  getSessionMetrics: (sessionId) => 
    apiRequest(`/monitor/sessions/${sessionId}`),
  getGlobalMetrics: () => 
    apiRequest('/monitor/global'),
  getPerformanceStats: () => 
    apiRequest('/monitor/performance'),
};

// 记忆管理API
export const memoryAPI = {
  generateSummary: (sessionId) => 
    apiRequest('/memory/summary/generate', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    }),
  getSummary: (sessionId) => 
    apiRequest(`/memory/summary/${sessionId}`),
  getAllSummaries: () => 
    apiRequest('/memory/summaries'),
  getStats: () => 
    apiRequest('/memory/stats'),
};
```

**预计工作量**: 30分钟

---

### 2. 更新Store状态管理 ✅ 推荐优先级：P0

**文件**: `vue/src/store/index.js`

**需要添加**:
```javascript
export const useChatStore = defineStore('chat', {
    state: () => ({
        // 现有状态...
        
        // 新增状态
        conversationMode: 'normal',
        messageCount: 0,
        needsNetwork: false,
        ragUsed: false,
        searchUsed: false,
        sessionStatus: null,
        monitoringMetrics: null,
    }),
    actions: {
        // 现有actions...
        
        // 新增actions
        async sendSmartMessage(text, forceMode = null) {
            const response = await chatAPI.sendSmartMessage(
                text,
                this.activeSessionId,
                forceMode
            );
            
            this.conversationMode = response.mode;
            this.messageCount = response.message_count;
            this.needsNetwork = response.needs_network;
            this.ragUsed = response.rag_used;
            this.searchUsed = response.search_used;
            
            return response;
        },

        async fetchSessionStatus() {
            if (!this.activeSessionId) return;
            const status = await chatAPI.getSessionStatus(this.activeSessionId);
            this.sessionStatus = status;
            this.conversationMode = status.current_mode;
            this.messageCount = status.message_count;
            return status;
        },

        async switchConversationMode(mode) {
            if (!this.activeSessionId) return;
            const result = await chatAPI.switchMode(this.activeSessionId, mode);
            this.conversationMode = result.new_mode;
            return result;
        },

        async fetchMonitoringMetrics() {
            const metrics = await monitorAPI.getGlobalMetrics();
            this.monitoringMetrics = metrics;
            return metrics;
        },
    }
});
```

**预计工作量**: 20分钟

---

### 3. 更新Home.vue使用智能对话 ✅ 推荐优先级：P0

**文件**: `vue/src/views/Home.vue`

**需要修改**: `handleSendMessage` 函数

**当前代码**:
```javascript
const response = await fetch('/api/chat', {
  method: 'POST',
  body: JSON.stringify({
    message: text,
    session_id: chatStore.activeSessionId,
    stream: true
  }),
});
```

**修改为**:
```javascript
// 使用智能对话API
const response = await chatStore.sendSmartMessage(text);

// 更新助手消息
chatStore.updateMessageContent({
  messageId: assistantMessageId,
  contentChunk: response.content
});

// 刷新会话状态
await chatStore.fetchSessionStatus();
```

**预计工作量**: 15分钟

---

## 🎨 UI增强（推荐）

### 4. 创建模式切换组件 ⭐ 推荐优先级：P1

**新建文件**: `vue/src/components/ConversationModeToggle.vue`

**功能**:
- 显示当前对话模式（普通/RAG增强）
- 显示消息计数（X/20）
- 提供手动切换按钮

**预计工作量**: 1小时

**参考代码**: 见 `FRONTEND_INTEGRATION_GUIDE.md`

---

### 5. 在ChatContainer中显示模式 ⭐ 推荐优先级：P1

**文件**: `vue/src/components/ChatContainer.vue`

**需要添加**:
```vue
<template>
  <div class="chat-container">
    <div class="chat-header">
      <ModelSelector />
      <!-- 新增：对话模式显示 -->
      <ConversationModeToggle />
      <UserProfileMenu />
    </div>
    <!-- ... -->
  </div>
</template>
```

**预计工作量**: 15分钟

---

### 6. 添加状态指示器 ⭐ 推荐优先级：P1

**位置**: MessageItem组件或ChatContainer

**显示内容**:
- 🔍 RAG增强模式已启用
- 📚 使用了知识库检索
- 🌐 使用了联网搜索

**实现方式**:
```vue
<div v-if="message.metadata" class="message-metadata">
  <span v-if="message.metadata.rag_used" class="badge">
    📚 知识库
  </span>
  <span v-if="message.metadata.search_used" class="badge">
    🌐 联网搜索
  </span>
</div>
```

**预计工作量**: 30分钟

---

## 📊 监控功能（可选）

### 7. 创建监控面板组件 💡 推荐优先级：P2

**新建文件**: `vue/src/components/ConversationMonitor.vue`

**功能**:
- 显示全局监控指标
- 显示性能统计
- 实时刷新（每5秒）

**预计工作量**: 2小时

**参考代码**: 见 `FRONTEND_INTEGRATION_GUIDE.md`

---

### 8. 在设置或管理页面添加监控入口 💡 推荐优先级：P2

**文件**: `vue/src/views/AdminDashboard.vue` 或新建监控页面

**预计工作量**: 30分钟

---

## 💾 记忆管理（可选）

### 9. 创建记忆摘要查看组件 💡 推荐优先级：P3

**新建文件**: `vue/src/components/MemorySummary.vue`

**功能**:
- 显示对话摘要
- 显示主题和关键要点
- 显示用户偏好

**预计工作量**: 1.5小时

---

### 10. 添加记忆摘要触发按钮 💡 推荐优先级：P3

**位置**: 会话列表或聊天界面

**功能**: 手动触发记忆摘要生成

**预计工作量**: 30分钟

---

## 🧪 测试任务

### 11. 基本功能测试 ✅ 推荐优先级：P0

**测试内容**:
- [ ] 发送消息正常工作
- [ ] 消息计数正确
- [ ] 达到20条时自动切换模式
- [ ] 手动切换模式正常
- [ ] 会话状态正确显示

**预计工作量**: 1小时

---

### 12. 集成测试 ⭐ 推荐优先级：P1

**测试内容**:
- [ ] 完整对话流程
- [ ] 模式切换流程
- [ ] 错误处理
- [ ] 加载状态显示

**预计工作量**: 1小时

---

## 📝 文档任务

### 13. 更新前端README 💡 推荐优先级：P2

**需要添加**:
- 智能对话功能说明
- 新增API使用方法
- 配置说明

**预计工作量**: 30分钟

---

## 📊 工作量估算

### 必须完成（P0）
- API服务更新: 30分钟
- Store更新: 20分钟
- Home.vue更新: 15分钟
- 基本功能测试: 1小时
**小计**: 约2小时

### 推荐完成（P1）
- 模式切换组件: 1小时
- ChatContainer更新: 15分钟
- 状态指示器: 30分钟
- 集成测试: 1小时
**小计**: 约2.75小时

### 可选完成（P2-P3）
- 监控面板: 2.5小时
- 记忆管理: 2小时
- 文档更新: 30分钟
**小计**: 约5小时

**总计**: 约10小时（完整实现所有功能）

---

## 🚀 实施建议

### 第一阶段（2小时）- 核心功能
1. 更新API服务（30分钟）
2. 更新Store（20分钟）
3. 更新Home.vue（15分钟）
4. 基本测试（1小时）

**目标**: 智能对话功能可用

### 第二阶段（3小时）- UI增强
1. 创建模式切换组件（1小时）
2. 更新ChatContainer（15分钟）
3. 添加状态指示器（30分钟）
4. 集成测试（1小时）

**目标**: 用户可以看到和控制对话模式

### 第三阶段（5小时）- 完整功能
1. 创建监控面板（2.5小时）
2. 添加记忆管理（2小时）
3. 更新文档（30分钟）

**目标**: 完整的智能对话系统

---

## ✅ 验证清单

完成后检查：

### 功能验证
- [ ] 可以发送消息并收到回复
- [ ] 消息计数正确显示
- [ ] 达到20条时自动切换到RAG增强模式
- [ ] 可以手动切换对话模式
- [ ] 会话状态正确显示
- [ ] RAG/搜索使用状态正确显示

### UI验证
- [ ] 模式切换组件正常显示
- [ ] 消息计数显示正确
- [ ] 状态指示器正常工作
- [ ] 加载状态正常显示
- [ ] 错误提示正常显示

### 性能验证
- [ ] 消息发送响应时间正常（< 3秒）
- [ ] 模式切换响应时间正常（< 1秒）
- [ ] 监控数据刷新不影响性能
- [ ] 无内存泄漏

---

## 📞 需要帮助？

如有问题，请参考：
- 后端API文档: `SMART_CONVERSATION_IMPLEMENTATION.md`
- 前端集成指南: `FRONTEND_INTEGRATION_GUIDE.md`
- 快速启动: `QUICK_START.md`

---

**创建日期**: 2024年
**预计完成时间**: 2-10小时（根据实施范围）
**优先级**: P0（核心功能）必须完成
