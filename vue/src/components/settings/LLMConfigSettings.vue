<template>
  <div class="settings-section llm-config-settings">
    <div class="section-header">
      <h3>AI模型配置</h3>
      <p class="section-description">选择您希望使用的AI模型提供商</p>
    </div>

    <div class="provider-selection">
      <div class="provider-option" :class="{ active: selectedProvider === 'api' }" @click="selectProvider('api')">
        <div class="provider-icon">🌐</div>
        <div class="provider-info">
          <h4>云端API</h4>
          <p>使用OpenAI、DeepSeek等云端AI服务</p>
          <div class="provider-features">
            <span class="feature-tag">稳定</span>
            <span class="feature-tag">快速</span>
            <span class="feature-tag">专业</span>
          </div>
        </div>
        <div class="provider-status">
          <div class="status-indicator" :class="apiStatus"></div>
        </div>
      </div>

      <div class="provider-option" :class="{ active: selectedProvider === 'local' }" @click="selectProvider('local')">
        <div class="provider-icon">🏠</div>
        <div class="provider-info">
          <h4>本地Ollama</h4>
          <p>在本地运行开源AI模型</p>
          <div class="provider-features">
            <span class="feature-tag">隐私</span>
            <span class="feature-tag">离线</span>
            <span class="feature-tag">免费</span>
          </div>
        </div>
        <div class="provider-status">
          <div class="status-indicator" :class="ollamaStatus"></div>
        </div>
      </div>
    </div>

    <!-- API配置详情 -->
    <div v-if="selectedProvider === 'api'" class="provider-details">
      <h4>云端API配置</h4>
      <div class="config-form">
        <div class="form-group">
          <label>API提供商</label>
          <select v-model="apiConfig.provider" class="form-select">
            <option value="openai">OpenAI</option>
            <option value="deepseek">DeepSeek</option>
            <option value="kimi">Kimi</option>
          </select>
        </div>
        
        <div class="form-group">
          <label>API密钥</label>
          <input 
            type="password" 
            v-model="apiConfig.apiKey" 
            placeholder="输入您的API密钥"
            class="form-input"
          />
        </div>
        
        <div class="form-group">
          <label>模型选择</label>
          <select v-model="apiConfig.model" class="form-select">
            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
            <option value="gpt-4">GPT-4</option>
            <option value="deepseek-chat">DeepSeek Chat</option>
            <option value="kimi-pro">Kimi Pro</option>
          </select>
        </div>
        
        <button class="test-button" @click="testApiConnection">
          测试连接
        </button>
      </div>
    </div>

    <!-- Ollama配置详情 -->
    <div v-if="selectedProvider === 'local'" class="provider-details">
      <h4>本地Ollama配置</h4>
      <div class="config-form">
        <div class="form-group">
          <label>Ollama服务地址</label>
          <input 
            type="text" 
            v-model="ollamaConfig.baseUrl" 
            placeholder="http://localhost:11434"
            class="form-input"
          />
        </div>
        
        <div class="form-group">
          <label>模型选择</label>
          <select v-model="ollamaConfig.model" class="form-select">
            <option value="llama2">Llama 2</option>
            <option value="llama2:7b">Llama 2 7B</option>
            <option value="llama2:13b">Llama 2 13B</option>
            <option value="codellama">Code Llama</option>
            <option value="mistral">Mistral</option>
          </select>
        </div>
        
        <div class="form-group">
          <label>模型参数</label>
          <div class="param-inputs">
            <input 
              type="number" 
              v-model="ollamaConfig.temperature" 
              placeholder="温度"
              class="form-input small"
            />
            <input 
              type="number" 
              v-model="ollamaConfig.maxTokens" 
              placeholder="最大令牌数"
              class="form-input small"
            />
          </div>
        </div>
        
        <button class="test-button" @click="testOllamaConnection">
          测试连接
        </button>
      </div>
    </div>

    <!-- 配置状态显示 -->
    <div class="config-status">
      <div class="status-item">
        <span class="status-label">当前状态:</span>
        <span class="status-value" :class="currentStatusClass">{{ currentStatusText }}</span>
      </div>
      <div class="status-item">
        <span class="status-label">连接状态:</span>
        <span class="status-value" :class="connectionStatusClass">{{ connectionStatusText }}</span>
      </div>
    </div>

    <!-- 保存按钮 -->
    <div class="action-buttons">
      <button class="save-button" @click="saveConfiguration" :disabled="!hasChanges">
        保存配置
      </button>
      <button class="reset-button" @click="resetConfiguration">
        重置
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useChatStore } from '@/store';

const chatStore = useChatStore();

// 响应式数据
const selectedProvider = ref('api');
const apiStatus = ref('unknown');
const ollamaStatus = ref('unknown');

// API配置
const apiConfig = ref({
  provider: 'openai',
  apiKey: '',
  model: 'gpt-3.5-turbo'
});

// Ollama配置
const ollamaConfig = ref({
  baseUrl: 'http://localhost:11434',
  model: 'llama2',
  temperature: 0.7,
  maxTokens: 2048
});

// 原始配置（用于检测变化）
const originalConfig = ref({});

// 计算属性
const hasChanges = computed(() => {
  if (selectedProvider.value === 'api') {
    return JSON.stringify(apiConfig.value) !== JSON.stringify(originalConfig.value.api);
  } else {
    return JSON.stringify(ollamaConfig.value) !== JSON.stringify(originalConfig.value.ollama);
  }
});

const currentStatusText = computed(() => {
  return selectedProvider.value === 'api' ? '使用云端API' : '使用本地Ollama';
});

const currentStatusClass = computed(() => {
  return selectedProvider.value === 'api' ? 'status-api' : 'status-local';
});

const connectionStatusText = computed(() => {
  if (selectedProvider.value === 'api') {
    switch (apiStatus.value) {
      case 'connected': return '已连接';
      case 'error': return '连接失败';
      default: return '未测试';
    }
  } else {
    switch (ollamaStatus.value) {
      case 'connected': return '已连接';
      case 'error': return '连接失败';
      default: return '未测试';
    }
  }
});

const connectionStatusClass = computed(() => {
  const status = selectedProvider.value === 'api' ? apiStatus.value : ollamaStatus.value;
  switch (status) {
    case 'connected': return 'status-success';
    case 'error': return 'status-error';
    default: return 'status-unknown';
  }
});

// 方法
const selectProvider = (provider) => {
  selectedProvider.value = provider;
};

const testApiConnection = async () => {
  try {
    apiStatus.value = 'connecting';
    // 这里应该调用后端API测试连接
    await new Promise(resolve => setTimeout(resolve, 1000)); // 模拟API调用
    
    if (apiConfig.value.apiKey) {
      apiStatus.value = 'connected';
    } else {
      apiStatus.value = 'error';
    }
  } catch (error) {
    apiStatus.value = 'error';
  }
};

const testOllamaConnection = async () => {
  try {
    ollamaStatus.value = 'connecting';
    // 这里应该调用后端API测试Ollama连接
    await new Promise(resolve => setTimeout(resolve, 1000)); // 模拟API调用
    
    ollamaStatus.value = 'connected';
  } catch (error) {
    ollamaStatus.value = 'error';
  }
};

const saveConfiguration = async () => {
  try {
    // 这里应该调用后端API保存配置
    await new Promise(resolve => setTimeout(resolve, 500)); // 模拟API调用
    
    // 更新原始配置
    if (selectedProvider.value === 'api') {
      originalConfig.value.api = { ...apiConfig.value };
    } else {
      originalConfig.value.ollama = { ...ollamaConfig.value };
    }
    
    alert('配置保存成功！');
  } catch (error) {
    alert('配置保存失败：' + error.message);
  }
};

const resetConfiguration = () => {
  if (selectedProvider.value === 'api') {
    apiConfig.value = { ...originalConfig.value.api };
  } else {
    ollamaConfig.value = { ...originalConfig.value.ollama };
  }
};

// 生命周期
onMounted(async () => {
  try {
    // 这里应该从后端获取当前配置
    // 暂时使用默认值
    originalConfig.value = {
      api: { ...apiConfig.value },
      ollama: { ...ollamaConfig.value }
    };
    
    // 设置默认提供商
    selectedProvider.value = 'api';
  } catch (error) {
    console.error('加载配置失败：', error);
  }
});
</script>

<style scoped>
.llm-config-settings {
  color: var(--text-primary);
}

.section-header {
  margin-bottom: 30px;
}

.section-header h3 {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.section-description {
  color: var(--text-secondary);
  margin: 0;
  font-size: 14px;
}

.provider-selection {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
}

.provider-option {
  flex: 1;
  padding: 20px;
  border: 2px solid var(--border-color);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.provider-option:hover {
  border-color: var(--button-bg);
  transform: translateY(-2px);
}

.provider-option.active {
  border-color: var(--button-bg);
  background-color: rgba(59, 130, 246, 0.1);
}

.provider-icon {
  font-size: 32px;
  margin-bottom: 15px;
}

.provider-info h4 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.provider-info p {
  color: var(--text-secondary);
  margin: 0 0 15px 0;
  font-size: 14px;
}

.provider-features {
  display: flex;
  gap: 8px;
}

.feature-tag {
  background-color: var(--primary-bg);
  color: var(--text-secondary);
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
}

.provider-status {
  position: absolute;
  top: 15px;
  right: 15px;
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: var(--text-secondary);
}

.status-indicator.connected {
  background-color: #10b981;
}

.status-indicator.error {
  background-color: #ef4444;
}

.status-indicator.connecting {
  background-color: #f59e0b;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.provider-details {
  background-color: var(--primary-bg);
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
  border: 1px solid var(--border-color);
}

.provider-details h4 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 20px 0;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 500;
  font-size: 14px;
}

.form-input, .form-select {
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background-color: var(--secondary-bg);
  color: var(--text-primary);
  font-size: 14px;
}

.form-input:focus, .form-select:focus {
  outline: none;
  border-color: var(--button-bg);
}

.form-input.small {
  width: 120px;
}

.param-inputs {
  display: flex;
  gap: 10px;
}

.test-button {
  background-color: var(--button-bg);
  color: var(--button-text);
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  align-self: flex-start;
}

.test-button:hover {
  opacity: 0.9;
}

.config-status {
  background-color: var(--primary-bg);
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  border: 1px solid var(--border-color);
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.status-item:last-child {
  margin-bottom: 0;
}

.status-label {
  font-weight: 500;
  color: var(--text-secondary);
}

.status-value {
  font-weight: 600;
}

.status-value.status-api {
  color: #3b82f6;
}

.status-value.status-local {
  color: #10b981;
}

.status-value.status-success {
  color: #10b981;
}

.status-value.status-error {
  color: #ef4444;
}

.status-value.status-unknown {
  color: var(--text-secondary);
}

.action-buttons {
  display: flex;
  gap: 15px;
}

.save-button, .reset-button {
  padding: 12px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  border: none;
}

.save-button {
  background-color: var(--button-bg);
  color: var(--button-text);
}

.save-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.reset-button {
  background-color: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.save-button:hover:not(:disabled) {
  opacity: 0.9;
}

.reset-button:hover {
  background-color: var(--hover-bg);
}
</style>
