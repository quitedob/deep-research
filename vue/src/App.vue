<template>
  <div class="app-root-wrapper">
    <!-- 顶部导航栏 -->
    <header class="app-header">
      <div class="header-content">
        <div class="logo">
          <img src="@/assets/logo.svg" alt="Deep Research" class="logo-icon">
          <span>Deep Research</span>
        </div>
        <nav class="main-nav">
          <router-link
            to="/home"
            class="nav-item"
            custom
            v-slot="{ navigate, isActive }"
          >
            <button
              :class="{ active: isActive }"
              @click="navigate"
            >
              <i class="icon-message"></i>
              对话
            </button>
          </router-link>
          <router-link
            v-if="isAdmin"
            to="/admin"
            class="nav-item"
            custom
            v-slot="{ navigate, isActive }"
          >
            <button
              :class="{ active: isActive }"
              @click="navigate"
            >
              <i class="icon-dashboard"></i>
              控制台
            </button>
          </router-link>
        </nav>
        <div class="header-actions">
          <UserProfileMenu :current-theme="theme" @toggle-theme="toggleTheme" />
        </div>
      </div>
    </header>

    <!-- 主要内容区域 -->
    <main class="app-main">
      <div class="view-container">
        <router-view />
      </div>
    </main>

    <!-- 设置模态框 -->
    <SettingsModal
        v-if="chatStore.isSettingsModalOpen"
        :current-theme="theme"
        @toggle-theme="toggleTheme"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useChatStore } from '@/store';
import SettingsModal from '@/components/SettingsModal.vue';
import UserProfileMenu from '@/components/UserProfileMenu.vue';

const theme = ref('dark'); // 默认主题
const chatStore = useChatStore();

// 计算管理员权限
const isAdmin = computed(() => {
  try {
    const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');
    const user = userStr ? JSON.parse(userStr) : null;
    return user?.role === 'admin';
  } catch (error) {
    console.error('[App] 解析用户信息失败:', error);
    return false;
  }
});

// 完整的 toggleTheme 方法
const toggleTheme = () => {
  const newTheme = theme.value === 'dark' ? 'light' : 'dark';
  theme.value = newTheme;
  // localStorage 的操作已移至 updateBodyClass，以确保同步
};

// 完整的 updateBodyClass 方法，用于更新 document.body 的类名并保存到 localStorage
const updateBodyClass = (newTheme) => {
  if (newTheme === 'dark') {
    document.body.classList.add('dark');
    document.body.classList.remove('light');
  } else {
    document.body.classList.add('light');
    document.body.classList.remove('dark');
  }
  // 确保主题偏好被保存
  localStorage.setItem('app-theme', newTheme);
};

// 组件挂载时，从 localStorage 读取主题并应用
onMounted(() => {
  const savedTheme = localStorage.getItem('app-theme');
  if (savedTheme) {
    theme.value = savedTheme; // 更新 ref
  }
  // 确保即使 localStorage 为空，也使用默认主题初始化 body class
  updateBodyClass(theme.value);
});

// 监听 theme ref 的变化，并同步更新 body 的 class
watch(theme, (newTheme, oldTheme) => {
  if (newTheme !== oldTheme) { // 仅当主题实际改变时才更新
    updateBodyClass(newTheme);
  }
});

</script>

<style>
/* 全局样式 */
html {
  height: 100%;
  width: 100%;
}

body {
  margin: 0;
  font-family: inherit;
  background-color: var(--primary-bg);
  color: var(--text-primary);
  height: 100%;
  width: 100%;
  overflow: hidden;
}

#app, .app-root-wrapper {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
}

/* 应用头部样式 */
.app-header {
  background: var(--secondary-bg);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 60px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.logo-icon {
  height: 24px;
  width: 24px;
}

.main-nav {
  display: flex;
  gap: 4px;
}

.nav-item {
  padding: 8px 16px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--primary-bg);
  color: var(--text-primary);
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.nav-item:hover {
  background: var(--hover-bg);
}

.nav-item.active {
  background: var(--accent-color);
  color: white;
  border-color: var(--accent-color);
}

.header-actions {
  display: flex;
  align-items: center;
}

/* 应用主体样式 */
.app-main {
  flex: 1;
  overflow: hidden;
}

.view-container {
  height: 100%;
  overflow: hidden;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    padding: 0 16px;
    height: 50px;
  }

  .logo {
    font-size: 16px;
  }

  .main-nav {
    gap: 2px;
  }

  .nav-item {
    padding: 6px 12px;
    font-size: 13px;
  }
}
</style>