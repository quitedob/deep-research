<template>
  <div class="settings-section">
    <h3>通用设置</h3>
    <div class="setting-item">
      <label for="theme-select">主题</label>
      <select id="theme-select" :value="currentTheme" @change="onThemeChange">
        <option value="light">浅色</option>
        <option value="dark">深色</option>
      </select>
    </div>
    <div class="setting-item">
      <label for="language-select">语言</label>
      <select id="language-select">
        <option value="auto">自动检测</option>
        <option value="zh">中文</option>
        <option value="en">English</option>
      </select>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  currentTheme: String
});
const emit = defineEmits(['toggle-theme']);

const onThemeChange = (event) => {
  // 仅当选择的主题与当前主题不同时才触发切换
  if (event.target.value !== props.currentTheme) {
    emit('toggle-theme');
  }
};
</script>

<style scoped>
.settings-section h3 {
  font-size: 18px;
  margin-bottom: 20px;
  color: var(--text-primary);
}
.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 0;
  border-bottom: 1px solid var(--border-color);
}
.setting-item:last-child {
  border-bottom: none;
}
.setting-item label {
  font-size: 15px;
}
.setting-item select {
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background-color: var(--input-bg);
  color: var(--text-primary);
  min-width: 120px;
}
</style>