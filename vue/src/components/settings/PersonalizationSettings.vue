<template>
  <div class="settings-section">
    <h3>个性化设置</h3>
    
    <div class="setting-item">
      <div class="setting-label">
        <label>用户名</label>
        <p class="setting-description">设置您的显示名称</p>
      </div>
      <div class="setting-control">
        <input 
          v-model="username" 
          @blur="updateUsername"
          type="text" 
          class="setting-input"
          placeholder="输入用户名"
        />
      </div>
    </div>

    <div class="setting-item">
      <div class="setting-label">
        <label>显示时间戳</label>
        <p class="setting-description">在消息旁显示发送时间</p>
      </div>
      <div class="setting-control">
        <label class="switch">
          <input type="checkbox" v-model="showTimestamp" @change="updateShowTimestamp" />
          <span class="slider"></span>
        </label>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const username = ref('');
const showTimestamp = ref(true);

const updateUsername = () => {
  localStorage.setItem('username', username.value);
  console.log('用户名已更新:', username.value);
};

const updateShowTimestamp = () => {
  localStorage.setItem('showTimestamp', showTimestamp.value);
  console.log('显示时间戳已更新:', showTimestamp.value);
};

onMounted(() => {
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  username.value = user.username || localStorage.getItem('username') || '';
  showTimestamp.value = localStorage.getItem('showTimestamp') !== 'false';
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

.setting-input {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--input-bg);
  color: var(--text-primary);
  border: 1px solid var(--input-border);
  border-radius: var(--radius-medium);
  font-size: 14px;
  min-width: 200px;
}

.setting-input:focus {
  outline: none;
  border-color: var(--input-focus-border);
}

/* Toggle Switch */
.switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 28px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--secondary-bg);
  transition: 0.3s;
  border-radius: 28px;
  border: 2px solid var(--border-color);
}

.slider:before {
  position: absolute;
  content: "";
  height: 20px;
  width: 20px;
  left: 2px;
  bottom: 2px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: var(--accent-blue);
  border-color: var(--accent-blue);
}

input:checked + .slider:before {
  transform: translateX(22px);
}
</style>
