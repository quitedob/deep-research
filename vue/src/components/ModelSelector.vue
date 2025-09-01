<template>
  <div class="model-selector-wrapper" ref="selectorRef">
    <button class="current-model-btn" @click="toggleDropdown">
      <span class="model-display">
        {{ chatStore.currentModel || '选择本地模型' }}
      </span>
      <span class="dropdown-icon" :class="{ 'is-open': isDropdownOpen }">▼</span>
    </button>

    <div v-if="isDropdownOpen" class="model-dropdown">
      <div class="dropdown-header">
        <div class="dropdown-title">选择本地 Ollama 模型</div>
        <button class="refresh-btn" @click="refreshModels" :disabled="isLoading">
          <span class="refresh-icon" :class="{ 'spinning': isLoading }">🔄</span>
        </button>
      </div>

      <div v-if="isLoading" class="loading-state">
        <span>正在加载模型列表...</span>
      </div>

      <div v-else-if="error" class="error-state">
        <span>❌ 加载失败: {{ error }}</span>
        <button @click="refreshModels" class="retry-btn">重试</button>
      </div>

      <ul v-else-if="ollamaModels.length > 0">
        <li
            v-for="modelName in ollamaModels"
            :key="modelName"
            class="model-option"
            @click="selectModel(modelName)"
        >
          <div class="model-info">
            <div class="model-name">{{ modelName }}</div>
          </div>
          <span v-if="chatStore.currentModel === modelName" class="checkmark">✔</span>
        </li>
      </ul>

      <div v-else class="empty-state">
        <span>未找到本地Ollama模型</span>
      </div>
    </div>
  </div>
</template>

<script setup>
// 简介：组件挂载时调用fetchOllamaModelTags，同步本地模型到下拉框
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useChatStore } from '@/store';
// 简化注释：引入获取Ollama模型列表的API函数
import { fetchOllamaModelTags } from '@/services/api.js';

const chatStore = useChatStore();
const isDropdownOpen = ref(false);
const isLoading = ref(false);
const error = ref(null);
const selectorRef = ref(null);

// 简化注释：存储从Ollama获取的模型列表
const ollamaModels = ref([]);

/**
 * 异步方法，用于获取并更新Ollama模型列表
 * 简化注释：刷新模型列表
 */
const refreshModels = async () => {
  if (isLoading.value) return;
  isLoading.value = true;
  error.value = null;
  try {
    // 简化注释：调用API获取模型标签
    const models = await fetchOllamaModelTags();
    ollamaModels.value = models;
    // 简化注释：如果当前选中的模型不在新列表中，或没有选中任何模型，则默认选中第一个
    if (models.length > 0 && !models.includes(chatStore.currentModel)) {
      chatStore.setModel(models[0]);
    }
  } catch (e) {
    error.value = e.message || '请检查Ollama服务是否正在运行';
    console.error('获取Ollama模型失败:', e);
  } finally {
    isLoading.value = false;
  }
};

/**
 * 切换下拉菜单的显示状态
 * 简化注释：切换下拉菜单
 */
const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value;
  // 简化注释：每次打开时都刷新模型列表
  if (isDropdownOpen.value) {
    refreshModels();
  }
};

/**
 * 选中一个模型并更新状态
 * @param {string} modelName - 被选中的模型名称
 * 简化注释：选择模型
 */
const selectModel = (modelName) => {
  chatStore.setModel(modelName);
  isDropdownOpen.value = false; // 选择后关闭菜单
};

/**
 * 处理点击组件外部区域的事件，用于关闭下拉菜单
 * @param {Event} event - 点击事件对象
 * 简化注释：处理外部点击
 */
const handleClickOutside = (event) => {
  if (selectorRef.value && !selectorRef.value.contains(event.target)) {
    isDropdownOpen.value = false;
  }
};

// 简化注释：组件挂载时执行初始化操作
onMounted(() => {
  document.addEventListener('mousedown', handleClickOutside);
  // 简化注释：组件加载时自动刷新一次模型列表
  refreshModels();
});

// 简化注释：组件卸载时移除事件监听
onUnmounted(() => {
  document.removeEventListener('mousedown', handleClickOutside);
});
</script>

<style scoped>
/* 样式与之前版本类似，确保功能性和一致性 */
.model-selector-wrapper {
  position: relative;
  z-index: 20;
}
.current-model-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background-color: var(--secondary-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
  min-width: 200px;
  justify-content: space-between;
}
.current-model-btn:hover {
  background-color: var(--hover-bg);
}
.dropdown-icon {
  font-size: 12px;
  transition: transform 0.2s;
}
.dropdown-icon.is-open {
  transform: rotate(180deg);
}
.model-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 8px;
  width: 300px;
  background-color: var(--secondary-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  padding: 8px;
  max-height: 400px;
  overflow-y: auto;
}
.dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 12px 12px;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 8px;
}
.dropdown-title {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}
.refresh-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  color: var(--text-secondary);
}
.refresh-btn:hover:not(:disabled) {
  background-color: var(--hover-bg);
  color: var(--text-primary);
}
.refresh-icon.spinning {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
.model-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
}
.model-option:hover {
  background-color: var(--hover-bg);
}
.model-name {
  font-weight: 500;
  color: var(--text-primary);
}
.checkmark {
  font-size: 16px;
  color: var(--button-bg);
}
.loading-state,
.error-state,
.empty-state {
  padding: 16px;
  text-align: center;
  color: var(--text-secondary);
}
.error-state {
  color: #dc2626; /* 错误红色 */
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
}
.retry-btn {
  padding: 6px 12px;
  background-color: var(--button-bg);
  color: var(--button-text);
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}
</style>