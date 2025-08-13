<template>
  <div class="history-section">
    <div class="history-title">历史对话</div>
    <div class="history-items">
      <div
          v-for="item in chatStore.historyList"
          :key="item.id"
          class="history-item"
          :class="{ active: item.id === chatStore.activeSessionId }"
          @click="handleSelectHistory(item.id)"
      >
        <span class="item-title">{{ item.title }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useChatStore } from '@/store';

const chatStore = useChatStore();

function handleSelectHistory(id) {
  chatStore.loadHistory(id);
}
</script>

<style scoped>
/* /src/components/HistoryList.vue 的局部样式 */
.history-section {
  flex: 1; /* 占据剩余空间 */
  overflow-y: auto; /* 超出部分显示滚动条 */
  padding: 20px;
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

.history-title {
  font-size: 14px;
  color: var(--gray);
  margin-bottom: 15px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.history-items {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.history-item {
  padding: 10px 15px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: background 0.2s, color 0.2s;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--gray-light);
}

.history-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.history-item.active {
  background: rgba(59, 130, 246, 0.3);
  color: white;
}

.history-item i {
  min-width: 20px;
  text-align: center;
}
</style>