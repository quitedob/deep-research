<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <div class="logo">Deep Research</div>
      <button class="new-chat-btn" @click="createNewChat">
        <span class="plus-icon">+</span> 新聊天
      </button>
    </div>
    
    <!-- 导航菜单 -->
    <nav class="nav-menu">
      <router-link to="/" class="nav-item">
        <i class="fas fa-home"></i>
        <span>首页</span>
      </router-link>
      <router-link to="/research/projects" class="nav-item">
        <i class="fas fa-project-diagram"></i>
        <span>研究项目</span>
      </router-link>
      <router-link to="/agents" class="nav-item">
        <i class="fas fa-robot"></i>
        <span>智能体</span>
      </router-link>
      
      <!-- 管理员专属菜单 -->
      <template v-if="isAdmin">
        <router-link to="/agent-llm-config" class="nav-item admin-only">
          <i class="fas fa-brain"></i>
          <span>智能体模型配置</span>
        </router-link>
        <router-link to="/admin/dashboard" class="nav-item admin-only">
          <i class="fas fa-shield-alt"></i>
          <span>管理员控制台</span>
        </router-link>
      </template>
      
      <router-link to="/admin" class="nav-item">
        <i class="fas fa-cog"></i>
        <span>设置</span>
      </router-link>
    </nav>
    
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

// 检查用户是否是管理员
const isAdmin = ref(false);

const checkUserRole = () => {
  try {
    // 从 localStorage 或 sessionStorage 获取用户信息
    const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');
    if (userStr) {
      const user = JSON.parse(userStr);
      isAdmin.value = user.role === 'admin';
    }
  } catch (error) {
    console.error('检查用户角色失败:', error);
    isAdmin.value = false;
  }
};

const createNewChat = () => {
  chatStore.clearChat();
};

onMounted(() => {
  chatStore.fetchHistoryList();
  checkUserRole();
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

/* 管理员专属菜单样式 */
.nav-item.admin-only {
  border-left: 3px solid #ffc107;
  background: rgba(255, 193, 7, 0.05);
}

.nav-menu {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-color);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  margin-bottom: 4px;
  border-radius: 8px;
  color: var(--text-secondary);
  text-decoration: none;
  transition: all 0.2s;
  font-size: 14px;
}

.nav-item:hover {
  background-color: rgba(0, 0, 0, 0.05);
  color: var(--text-primary);
}

.nav-item.router-link-active {
  background-color: var(--button-bg);
  color: var(--button-text);
}

.nav-item i {
  width: 20px;
  text-align: center;
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