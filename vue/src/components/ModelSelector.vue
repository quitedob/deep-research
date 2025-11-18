<template>
  <div class="model-selector-wrapper" ref="selectorRef">
    <button class="current-model-btn" @click="toggleDropdown">
      <span class="model-display">
        {{ getCurrentModelDisplay() }}
      </span>
      <span class="dropdown-icon" :class="{ 'is-open': isDropdownOpen }">▼</span>
    </button>

    <div v-if="isDropdownOpen" class="model-dropdown">
      <div class="dropdown-header">
        <div class="dropdown-title">选择AI模型</div>
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

      <div v-else>
        <ul class="model-list">
          <li
              class="model-option"
              @click="selectModel('deepseek-chat')"
          >
            <div class="model-info">
              <div class="model-name">DeepSeek</div>
              <div class="model-description">DeepSeek 对话模型</div>
            </div>
            <span v-if="chatStore.currentModel === 'deepseek-chat'" class="checkmark">✔</span>
          </li>
          <li
              class="model-option"
              @click="selectModel('glm-4-plus')"
          >
            <div class="model-info">
              <div class="model-name">智谱 GLM</div>
              <div class="model-description">智谱 GLM-4-Plus 模型</div>
            </div>
            <span v-if="chatStore.currentModel === 'glm-4-plus'" class="checkmark">✔</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
// 简介：组件挂载时调用getModels，同步本地模型到下拉框
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useChatStore } from '@/store';
// 简化注释：引入获取模型列表的API函数
import { chatAPI } from '@/api/index';

const chatStore = useChatStore();
const isDropdownOpen = ref(false);
const isLoading = ref(false);
const error = ref(null);
const selectorRef = ref(null);

// 存储不同提供商的模型列表（仅云端API）
const allModels = ref([]);

/**
 * 获取当前模型的显示名称
 */
const getCurrentModelDisplay = () => {
  const currentModel = chatStore.currentModel;
  if (!currentModel) return '智谱 GLM';

  if (currentModel === 'deepseek-chat') {
    return 'DeepSeek';
  } else if (currentModel === 'glm-4-plus') {
    return '智谱 GLM';
  }

  return currentModel;
};

/**
 * 异步方法，用于获取并更新模型列表
 * 简化注释：刷新模型列表
 */
const refreshModels = async () => {
  if (isLoading.value) return;
  isLoading.value = true;
  error.value = null;
  try {
    // 设置默认模型为智谱 GLM
    if (!chatStore.currentModel) {
      chatStore.setModel('glm-4-plus');
    }
  } catch (e) {
    error.value = e.message || '加载模型列表失败';
    console.error('获取模型列表失败:', e);
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

.provider-section {
  margin-bottom: 16px;
}

.provider-section:last-child {
  margin-bottom: 0;
}

.provider-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 8px 12px 4px;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 4px;
}

.model-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.model-info {
  flex: 1;
  min-width: 0;
}

.model-name {
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.model-provider {
  font-size: 11px;
  color: var(--text-secondary);
  opacity: 0.7;
}

.model-description {
  font-size: 11px;
  color: var(--text-secondary);
  line-height: 1.3;
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