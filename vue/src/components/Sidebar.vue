<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <div class="logo">Deep Research</div>
    </div>
    
    <div class="list-container">
      <HistoryList />
    </div>
  </div>
</template>


<script setup>
import { useChatStore } from '@/store';
import HistoryList from './HistoryList.vue';
import { onMounted, ref, computed } from 'vue';

const chatStore = useChatStore();

onMounted(() => {
  chatStore.fetchHistoryList();
});
</script>

<style scoped>
.sidebar {
  width: 260px;
  height: 100vh;
  background-color: var(--secondary-bg);
  display: flex;
  flex-direction: column;
  padding: 16px;
  box-sizing: border-box;
  flex-shrink: 0;
  border-right: 1px solid var(--border-color);
  transition: margin-left 0.3s ease;
}

.sidebar-header {
  margin-bottom: 24px;
}

.logo {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 24px;
  color: var(--text-primary);
}

.list-container {
  flex-grow: 1;
  overflow-y: auto;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  padding: 0 8px;
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.explore-title {
  margin-top: 24px;
}

.explore-items {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.explore-item {
  padding: 8px 12px;
  border-radius: 6px;
  text-decoration: none;
  color: var(--text-secondary);
  font-size: 14px;
  transition: background-color 0.2s, color 0.2s;
}
.explore-item:hover {
  background-color: var(--hover-bg);
  color: var(--text-primary);
}

/* (新增) 响应式设计：在屏幕宽度小于768px时隐藏侧边栏 */
@media (max-width: 768px) {
  .sidebar {
    display: none;
  }
}
</style>