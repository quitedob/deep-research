<template>
  <div class="settings-section">
    <h3>AI模型配置</h3>
    
    <div class="setting-item">
      <div class="setting-label">
        <label>默认模型提供商</label>
        <p class="setting-description">选择默认使用的AI模型提供商</p>
      </div>
      <div class="setting-control">
        <select v-model="defaultProvider" class="setting-select">
          <option value="deepseek">DeepSeek</option>
          <option value="zhipu">智谱AI</option>
          <option value="ollama">Ollama</option>
        </select>
      </div>
    </div>

    <div class="setting-item">
      <div class="setting-label">
        <label>默认模型</label>
        <p class="setting-description">选择默认使用的具体模型</p>
      </div>
      <div class="setting-control">
        <select v-model="defaultModel" class="setting-select">
          <option value="deepseek-chat">DeepSeek Chat</option>
          <option value="glm-4-air">GLM-4 Air</option>
          <option value="gemma3:4b">Gemma 3 4B</option>
        </select>
      </div>
    </div>

    <div class="actions">
      <button @click="saveSettings" class="test-btn">保存设置</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const defaultProvider = ref('deepseek');
const defaultModel = ref('deepseek-chat');

const saveSettings = () => {
  localStorage.setItem('defaultProvider', defaultProvider.value);
  localStorage.setItem('defaultModel', defaultModel.value);
  alert('设置已保存');
};

onMounted(() => {
  defaultProvider.value = localStorage.getItem('defaultProvider') || 'deepseek';
  defaultModel.value = localStorage.getItem('defaultModel') || 'deepseek-chat';
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

.setting-select {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--input-bg);
  color: var(--text-primary);
  border: 1px solid var(--input-border);
  border-radius: var(--radius-medium);
  font-size: 14px;
  cursor: pointer;
  min-width: 200px;
}

.actions {
  margin-top: var(--spacing-xl);
}

.test-btn {
  padding: var(--spacing-sm) var(--spacing-lg);
  background: var(--gradient-blue);
  color: white;
  border: none;
  border-radius: var(--radius-medium);
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}
</style>
