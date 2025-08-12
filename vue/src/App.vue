<template>
  <div class="app-root-wrapper">
    <router-view v-slot="{ Component }">
      <component :is="Component" :current-theme="theme" @toggle-theme="toggleTheme" />
    </router-view>

    <SettingsModal
        v-if="chatStore.isSettingsModalOpen"
        :current-theme="theme"
        @toggle-theme="toggleTheme"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useChatStore } from '@/store';
import SettingsModal from '@/components/SettingsModal.vue';

const theme = ref('dark'); // 默认主题
const chatStore = useChatStore();

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
/* 全局样式部分与上一版本相同，此处不再重复 */
html {
  height: 100%;
  width: 100%;
}
body {
  margin: 0;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
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
</style>