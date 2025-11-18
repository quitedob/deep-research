<template>
  <div class="app-root-wrapper">
    <!-- macOS-style Navigation Bar - 在/home页面隐藏 -->
    <header class="app-header" v-if="$route.path !== '/home'">
      <div class="header-content">
        <!-- Left: App Logo and Navigation -->
        <div class="header-left">
          <div class="app-logo">
            <div class="logo-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              </svg>
            </div>
            <span class="logo-text">Deep Research</span>
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
                class="nav-btn"
              >
                <i class="nav-icon">💬</i>
                <span class="nav-label">对话</span>
              </button>
            </router-link>
            <!-- 管理员功能已移除 -->
          </nav>
        </div>

        <!-- Right: User Actions -->
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

/* macOS-style Header */
.app-header {
  background: var(--secondary-bg);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 var(--spacing-lg);
  height: 52px;
  max-width: 1400px;
  margin: 0 auto;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-xl);
}

.app-logo {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-medium);
  transition: background-color 0.2s ease;
}

.app-logo:hover {
  background: var(--hover-bg);
}

.logo-icon {
  width: 20px;
  height: 20px;
  color: var(--accent-blue);
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-text {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.024em;
}

.main-nav {
  display: flex;
  gap: var(--spacing-xs);
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  border-radius: var(--radius-medium);
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
}

.nav-btn:hover {
  background: var(--hover-bg);
  color: var(--text-primary);
}

.nav-btn.active {
  background: var(--button-bg);
  color: var(--button-text);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.nav-icon {
  font-size: 16px;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-label {
  font-size: 14px;
  font-weight: 500;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
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