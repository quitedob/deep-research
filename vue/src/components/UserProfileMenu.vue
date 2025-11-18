<template>
  <div class="user-profile-menu" ref="menuRef">
    <div class="avatar" @click="toggleMenu">{{ userInitial }}</div>
    <div v-if="isMenuOpen" class="menu-dropdown">
      <div class="menu-header">{{ displayName }}</div>
      <div class="menu-items">
        <a href="#" class="menu-item">我的订阅</a>
        <a href="#" class="menu-item" @click.prevent="openSettings">设置</a>

        <!-- 管理员专用功能已移除 -->

        <div class="menu-item theme-toggle" @click="onToggleTheme">
          <span>{{ currentTheme === 'dark' ? '亮色模式' : '暗色模式' }}</span>
          <span class="theme-icon">{{ currentTheme === 'dark' ? '☀️' : '🌙' }}</span>
        </div>
        <div class="menu-divider"></div>
        <a href="#" class="menu-item logout" @click.prevent="handleLogout">注销</a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useChatStore } from '@/store'; // 1. 引入 useChatStore

const props = defineProps({ currentTheme: String });
const emit = defineEmits(['toggle-theme']);
const router = useRouter();
const isMenuOpen = ref(false);
const menuRef = ref(null);
const chatStore = useChatStore(); // 2. 获取 store 实例

// 计算用户信息和管理员权限
const currentUser = computed(() => {
  try {
    const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  } catch (error) {
    console.error('[UserProfileMenu] 解析用户信息失败:', error);
    return null;
  }
});

const isAdmin = computed(() => {
  return currentUser.value?.role === 'admin';
});

const userInitial = computed(() => {
  const username = currentUser.value?.username || 'U';
  return username.charAt(0).toUpperCase();
});

const displayName = computed(() => {
  return currentUser.value?.username || '用户';
});

const toggleMenu = () => { isMenuOpen.value = !isMenuOpen.value; };
const onToggleTheme = () => { emit('toggle-theme'); };

// 3. 新增方法：打开设置弹窗
const openSettings = () => {
  chatStore.openSettingsModal();
  isMenuOpen.value = false; // 点击后关闭用户菜单
};

// 4. 新增方法：处理用户注销
const handleLogout = () => {
  console.log('[UserProfileMenu] 开始注销流程');

  // 清除所有认证相关的存储
  localStorage.removeItem('auth_token');
  localStorage.removeItem('auth_username');
  localStorage.removeItem('user');
  sessionStorage.removeItem('auth_token');
  sessionStorage.removeItem('auth_username');
  sessionStorage.removeItem('user');

  console.log('[UserProfileMenu] 已清除所有认证信息');

  // 关闭菜单
  isMenuOpen.value = false;

  // 重定向到登录页面
  console.log('[UserProfileMenu] 重定向到登录页面');
  router.push('/login');
};

const handleClickOutside = (event) => {
  if (menuRef.value && !menuRef.value.contains(event.target)) {
    isMenuOpen.value = false;
  }
};
onMounted(() => document.addEventListener('mousedown', handleClickOutside));
onUnmounted(() => document.removeEventListener('mousedown', handleClickOutside));
</script>


<style scoped>
/* 样式定义 */
.user-profile-menu {
  position: relative;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: #8ab4f8;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  cursor: pointer;
  border: 2px solid var(--primary-bg);
  transition: transform 0.2s;
}
.avatar:hover {
  transform: scale(1.1);
}

.menu-dropdown {
  position: absolute;
  top: 50px;
  right: 0;
  width: 280px;
  background-color: var(--secondary-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  color: var(--text-primary);
  overflow: hidden;
}

.menu-header {
  padding: 16px;
  font-weight: 500;
  border-bottom: 1px solid var(--border-color);
}

.menu-items {
  padding: 8px 0;
}

/* router-link 默认会被渲染成 a 标签，所以样式可以通用 */
.menu-item {
  display: block;
  padding: 12px 16px;
  color: var(--text-primary);
  text-decoration: none;
  cursor: pointer;
  transition: background-color 0.2s;
}
.menu-item:hover {
  background-color: var(--hover-bg);
}

.theme-toggle {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.menu-divider {
  height: 1px;
  background-color: var(--border-color);
  margin: 8px 0;
}

.admin-link {
  color: #8ab4f8;
  font-weight: 500;
}
.admin-link:hover {
  background-color: rgba(138, 180, 248, 0.1);
}

.logout {
  color: #f28b82; /* 红色以示注销 */
}
</style>