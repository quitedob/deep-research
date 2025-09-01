<template>
  <div class="history-section">
    <div class="history-header">
      <div class="history-title">对话记忆</div>
      <div class="history-actions">
        <button class="action-button" @click="showSearchModal" title="搜索对话">
          <svg viewBox="0 0 24 24" fill="currentColor" class="icon">
            <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
          </svg>
        </button>
        <button class="action-button" @click="showMemorySummary" title="记忆摘要">
          <svg viewBox="0 0 24 24" fill="currentColor" class="icon">
            <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
          </svg>
        </button>
        <button class="action-button" @click="clearHistory" title="清空历史">
          <svg viewBox="0 0 24 24" fill="currentColor" class="icon">
            <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- 搜索框 -->
    <div class="search-container" v-if="showSearch">
      <input 
        type="text" 
        v-model="searchQuery" 
        placeholder="搜索对话内容..."
        class="search-input"
        @input="filterHistory"
      />
      <button class="close-search" @click="hideSearch">×</button>
    </div>

    <!-- 记忆摘要 -->
    <div class="memory-summary" v-if="showMemorySummaryModal">
      <div class="summary-header">
        <h4>记忆摘要</h4>
        <button class="close-summary" @click="hideMemorySummary">×</button>
      </div>
      <div class="summary-content">
        <div class="summary-stats">
          <div class="stat-item">
            <span class="stat-label">总对话:</span>
            <span class="stat-value">{{ memorySummary.total_conversations }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">总消息:</span>
            <span class="stat-value">{{ memorySummary.total_messages }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">记忆令牌:</span>
            <span class="stat-value">{{ memorySummary.memory_tokens }}/{{ memorySummary.memory_limit }}</span>
          </div>
        </div>
        <div class="summary-topics">
          <h5>热门话题</h5>
          <div class="topic-tags">
            <span 
              v-for="topic in memorySummary.favorite_topics" 
              :key="topic"
              class="topic-tag"
            >
              {{ topic }}
            </span>
          </div>
        </div>
        <div class="summary-style">
          <h5>对话风格</h5>
          <p>{{ memorySummary.conversation_style }}</p>
        </div>
      </div>
    </div>

    <!-- 对话列表 -->
    <div class="history-items" v-if="filteredHistory.length > 0">
      <div
          v-for="item in filteredHistory"
          :key="item.id"
          class="history-item"
          :class="{ active: item.id === chatStore.activeSessionId }"
          @click="handleSelectHistory(item.id)"
      >
        <div class="item-content">
          <div class="item-title">{{ item.title }}</div>
          <div class="item-preview">{{ item.last_message }}</div>
          <div class="item-meta">
            <span class="message-count">{{ item.message_count }} 条消息</span>
            <span class="timestamp">{{ formatTime(item.updated_at) }}</span>
          </div>
        </div>
        <div class="item-actions">
          <button class="item-action" @click.stop="deleteHistory(item.id)" title="删除">
            <svg viewBox="0 0 24 24" fill="currentColor" class="icon-small">
              <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div class="empty-state" v-else-if="!showSearch">
      <div class="empty-icon">💬</div>
      <h3>开始您的第一次对话</h3>
      <p>您的对话历史将在这里显示，AI会记住您的偏好和重要信息</p>
      <button class="start-chat-button" @click="startNewChat">
        开始对话
      </button>
    </div>

    <!-- 搜索结果为空 -->
    <div class="empty-search" v-else>
      <div class="empty-icon">🔍</div>
      <h3>未找到相关对话</h3>
      <p>尝试使用不同的关键词搜索</p>
    </div>

    <!-- 加载状态 -->
    <div class="loading-state" v-if="loading">
      <div class="loading-spinner"></div>
      <p>加载对话历史...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useChatStore } from '@/store';

const chatStore = useChatStore();

// 响应式数据
const showSearch = ref(false);
const searchQuery = ref('');
const showMemorySummaryModal = ref(false);
const loading = ref(false);

// 模拟数据（实际应该从API获取）
const mockHistoryList = ref([
  {
    id: 'session-1',
    title: '关于深度学习的讨论',
    last_message: '请解释一下神经网络的工作原理',
    message_count: 5,
    updated_at: new Date('2024-01-15T10:30:00Z'),
    created_at: new Date('2024-01-15T10:00:00Z')
  },
  {
    id: 'session-2',
    title: 'Python编程问题',
    last_message: '如何优化Python代码性能？',
    message_count: 3,
    updated_at: new Date('2024-01-14T15:45:00Z'),
    created_at: new Date('2024-01-14T15:30:00Z')
  },
  {
    id: 'session-3',
    title: '机器学习算法比较',
    last_message: '随机森林和梯度提升有什么区别？',
    message_count: 8,
    updated_at: new Date('2024-01-13T09:20:00Z'),
    created_at: new Date('2024-01-13T09:00:00Z')
  }
]);

const mockMemorySummary = ref({
  total_conversations: 15,
  total_messages: 127,
  memory_tokens: 3200,
  memory_limit: 4000,
  favorite_topics: ['深度学习', 'Python编程', '机器学习', '算法优化'],
  conversation_style: '详细且有条理，喜欢深入探讨技术细节',
  last_active: new Date()
});

// 计算属性
const filteredHistory = computed(() => {
  if (!searchQuery.value) {
    return mockHistoryList.value;
  }
  
  const query = searchQuery.value.toLowerCase();
  return mockHistoryList.value.filter(item => 
    item.title.toLowerCase().includes(query) ||
    item.last_message.toLowerCase().includes(query)
  );
});

// 方法
function handleSelectHistory(id) {
  chatStore.loadHistory(id);
}

function showSearchModal() {
  showSearch.value = true;
  searchQuery.value = '';
}

function hideSearch() {
  showSearch.value = false;
  searchQuery.value = '';
}

function filterHistory() {
  // 搜索逻辑已在计算属性中实现
}

function showMemorySummary() {
  showMemorySummaryModal.value = true;
}

function hideMemorySummary() {
  showMemorySummaryModal.value = false;
}

function clearHistory() {
  if (confirm('确定要清空所有对话历史吗？此操作不可恢复。')) {
    // 这里应该调用API清空历史
    mockHistoryList.value = [];
    console.log('清空对话历史');
  }
}

function deleteHistory(id) {
  if (confirm('确定要删除这个对话吗？')) {
    // 这里应该调用API删除特定对话
    mockHistoryList.value = mockHistoryList.value.filter(item => item.id !== id);
    console.log('删除对话:', id);
  }
}

function startNewChat() {
  // 开始新对话
  chatStore.startNewChat();
}

function formatTime(date) {
  if (!date) return '';
  
  const now = new Date();
  const diff = now - date;
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  
  if (minutes < 1) return '刚刚';
  if (minutes < 60) return `${minutes}分钟前`;
  if (hours < 24) return `${hours}小时前`;
  if (days < 7) return `${days}天前`;
  
  return date.toLocaleDateString('zh-CN');
}

// 生命周期
onMounted(async () => {
  try {
    loading.value = true;
    // 这里应该从后端API获取实际的对话历史
    // 暂时使用模拟数据
    await new Promise(resolve => setTimeout(resolve, 500)); // 模拟加载时间
    loading.value = false;
  } catch (error) {
    console.error('加载对话历史失败：', error);
    loading.value = false;
  }
});
</script>

<style scoped>
.history-section {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.history-title {
  font-size: 16px;
  color: var(--text-primary);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.history-actions {
  display: flex;
  gap: 8px;
}

.action-button {
  background: none;
  border: none;
  color: var(--text-secondary);
  padding: 6px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-button:hover {
  background-color: var(--hover-bg);
  color: var(--text-primary);
}

.icon {
  width: 18px;
  height: 18px;
}

.search-container {
  position: relative;
  margin-bottom: 20px;
}

.search-input {
  width: 100%;
  padding: 10px 40px 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background-color: var(--primary-bg);
  color: var(--text-primary);
  font-size: 14px;
}

.search-input:focus {
  outline: none;
  border-color: var(--button-bg);
}

.close-search {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 18px;
  cursor: pointer;
}

.memory-summary {
  background-color: var(--primary-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  margin-bottom: 20px;
  overflow: hidden;
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background-color: var(--secondary-bg);
  border-bottom: 1px solid var(--border-color);
}

.summary-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.close-summary {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 20px;
  cursor: pointer;
}

.summary-content {
  padding: 20px;
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 5px;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--button-bg);
}

.summary-topics h5,
.summary-style h5 {
  margin: 0 0 10px 0;
  font-size: 14px;
  font-weight: 600;
}

.topic-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 15px;
}

.topic-tag {
  background-color: var(--button-bg);
  color: var(--button-text);
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
}

.summary-style p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.5;
}

.history-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  padding: 15px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.history-item:hover {
  background: var(--hover-bg);
  border-color: var(--border-color);
}

.history-item.active {
  background: rgba(59, 130, 246, 0.1);
  border-color: var(--button-bg);
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-preview {
  color: var(--text-secondary);
  font-size: 13px;
  margin-bottom: 8px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-meta {
  display: flex;
  gap: 15px;
  font-size: 11px;
  color: var(--text-secondary);
}

.item-actions {
  display: flex;
  gap: 5px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.history-item:hover .item-actions {
  opacity: 1;
}

.item-action {
  background: none;
  border: none;
  color: var(--text-secondary);
  padding: 4px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.item-action:hover {
  background-color: var(--hover-bg);
  color: var(--text-primary);
}

.icon-small {
  width: 14px;
  height: 14px;
}

.empty-state,
.empty-search {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.empty-state h3,
.empty-search h3 {
  margin: 0 0 10px 0;
  color: var(--text-primary);
  font-size: 18px;
}

.empty-state p,
.empty-search p {
  margin: 0 0 20px 0;
  font-size: 14px;
  line-height: 1.5;
}

.start-chat-button {
  background-color: var(--button-bg);
  color: var(--button-text);
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.start-chat-button:hover {
  opacity: 0.9;
}

.loading-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-secondary);
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--border-color);
  border-top: 2px solid var(--button-bg);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 自定义滚动条样式 */
.history-section::-webkit-scrollbar {
  width: 6px;
}

.history-section::-webkit-scrollbar-track {
  background: transparent;
}

.history-section::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

.history-section::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.4);
}
</style>