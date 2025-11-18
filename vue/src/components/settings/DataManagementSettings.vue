<template>
  <div class="settings-section">
    <h3>数据管理</h3>
    
    <div class="setting-item">
      <div class="setting-label">
        <label>清除对话历史</label>
        <p class="setting-description">删除所有本地保存的对话记录</p>
      </div>
      <div class="setting-control">
        <button @click="clearHistory" class="action-btn danger">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke-width="2"/>
          </svg>
          清除历史
        </button>
      </div>
    </div>

    <div class="setting-item">
      <div class="setting-label">
        <label>自动清理</label>
        <p class="setting-description">自动删除超过指定天数的对话</p>
      </div>
      <div class="setting-control">
        <select v-model="autoCleanDays" @change="updateAutoClean" class="setting-select">
          <option value="0">关闭</option>
          <option value="7">7天</option>
          <option value="30">30天</option>
          <option value="90">90天</option>
        </select>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useChatStore } from '@/store';

const chatStore = useChatStore();
const autoCleanDays = ref('0');

const clearHistory = () => {
  if (!confirm('确定要清除所有对话历史吗？此操作不可恢复！')) return;
  
  try {
    chatStore.clearAllHistory();
    localStorage.removeItem('chat_history');
    alert('对话历史已清除');
  } catch (error) {
    console.error('清除失败:', error);
    alert('清除失败，请重试');
  }
};

const updateAutoClean = () => {
  localStorage.setItem('autoCleanDays', autoCleanDays.value);
  console.log('自动清理已更新:', autoCleanDays.value);
};

onMounted(() => {
  autoCleanDays.value = localStorage.getItem('autoCleanDays') || '0';
});
</script>

<style scoped>
.settings-section {
  max-width: 600px;
}

.settings-section h3 {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: var(--spacing-xl);
  color: var(--text-primary);
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg) 0;
  border-bottom: 1px solid var(--border-color);
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-label {
  flex: 1;
}

.setting-label label {
  display: block;
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.setting-description {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.setting-control {
  flex-shrink: 0;
  margin-left: var(--spacing-lg);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-lg);
  background: var(--button-bg);
  color: var(--button-text);
  border: none;
  border-radius: var(--radius-medium);
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: var(--button-hover-bg);
  transform: translateY(-1px);
}

.action-btn.danger {
  background: var(--accent-red);
  color: white;
}

.action-btn.danger:hover {
  background: #ff2d55;
}

.setting-select {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--input-bg);
  color: var(--text-primary);
  border: 1px solid var(--input-border);
  border-radius: var(--radius-medium);
  font-size: 14px;
  cursor: pointer;
  min-width: 150px;
}

.setting-select:focus {
  outline: none;
  border-color: var(--input-focus-border);
}
</style>
