<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <div class="logo">芝麻编程</div>
      <button class="new-chat-btn" @click="createNewChat">
        <span class="plus-icon">+</span> 新聊天
      </button>
    </div>
    <div class="list-container">
      <p class="section-title">历史记录</p>
<!--      <p class="section-title explore-title">探索</p>
      <div class="explore-items">
        <a href="#" class="explore-item">多代理 RAG</a>
        <a href="#" class="explore-item">播客生成</a>
        <a href="#" class="explore-item">代码生成</a>
      </div>-->
    </div>
  </div>
</template>


<script setup>
import { useChatStore } from '@/store';
const chatStore = useChatStore();

// 定义点击事件的处理函数
const createNewChat = () => {
  chatStore.clearChat(); // 调用 store 中的 action
};
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
  margin-bottom: 20px;
  color: var(--text-primary);
}

.new-chat-btn {
  background-color: var(--button-bg);
  color: var(--button-text);
  border: none;
  border-radius: 8px;
  padding: 10px 16px;
  cursor: pointer;
  width: 100%;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: background-color 0.2s;
}
.new-chat-btn:hover {
  opacity: 0.9;
}
.plus-icon {
  font-size: 18px;
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