<template>
  <div class="agent-llm-config">
    <div class="header">
      <h1>智能体 LLM 模型配置</h1>
      <p class="subtitle">为每个智能体配置使用的 LLM 模型和提供商</p>
    </div>

    <!-- 搜索提供商配置 -->
    <div class="search-provider-section">
      <h2>联网搜索提供商</h2>
      <div class="provider-selector">
        <label>默认搜索提供商:</label>
        <select v-model="currentSearchProvider" @change="updateSearchProvider">
          <option value="doubao">豆包 (Doubao) - 推荐</option>
          <option value="kimi">Kimi (月之暗面)</option>
        </select>
        <span class="provider-status" :class="{ active: searchProviderStatus }">
          {{ searchProviderStatus ? '✓ 已连接' : '✗ 未配置' }}
        </span>
      </div>
      <p class="provider-description">
        {{ searchProviderDescriptions[currentSearchProvider] }}
      </p>
    </div>

    <!-- 智能体配置表格 -->
    <div class="config-table-section">
      <div class="table-header">
        <h2>智能体配置</h2>
        <div class="actions">
          <button @click="resetToDefaults" class="btn-secondary">
            重置为默认
          </button>
          <button @click="saveAllConfigs" class="btn-primary">
            保存所有配置
          </button>
        </div>
      </div>

      <div class="table-container">
        <table class="config-table">
          <thead>
            <tr>
              <th>智能体</th>
              <th>描述</th>
              <th>LLM 提供商</th>
              <th>模型</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="config in agentConfigs" :key="config.agent_id">
              <td class="agent-name">
                <div class="agent-icon">🤖</div>
                <span>{{ config.agent_name }}</span>
              </td>
              <td class="description">{{ config.description }}</td>
              <td>
                <select 
                  v-model="config.llm_provider" 
                  @change="onProviderChange(config)"
                  class="provider-select"
                >
                  <option value="doubao">豆包 (Doubao)</option>
                  <option value="kimi">Kimi</option>
                  <option value="deepseek">DeepSeek</option>
                  <option value="ollama">Ollama (本地)</option>
                </select>
              </td>
              <td>
                <select 
                  v-model="config.model_name" 
                  class="model-select"
                >
                  <option 
                    v-for="model in getAvailableModels(config.llm_provider)" 
                    :key="model.id"
                    :value="model.id"
                  >
                    {{ model.name }}
                  </option>
                </select>
              </td>
              <td>
                <span 
                  class="status-badge" 
                  :class="getProviderStatus(config.llm_provider)"
                >
                  {{ getProviderStatusText(config.llm_provider) }}
                </span>
              </td>
              <td>
                <button 
                  @click="updateSingleConfig(config)" 
                  class="btn-update"
                >
                  更新
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 提供商信息 -->
    <div class="providers-info">
      <h2>可用的 LLM 提供商</h2>
      <div class="provider-cards">
        <div 
          v-for="(provider, key) in availableProviders" 
          :key="key"
          class="provider-card"
          :class="{ unavailable: !provider.available }"
        >
          <div class="provider-header">
            <h3>{{ provider.name }}</h3>
            <span class="availability" :class="{ available: provider.available }">
              {{ provider.available ? '✓ 可用' : '✗ 未配置' }}
            </span>
          </div>
          <div class="provider-models">
            <h4>支持的模型:</h4>
            <ul>
              <li v-for="model in provider.models" :key="model.id">
                <strong>{{ model.name }}</strong>
                <p>{{ model.description }}</p>
                <div class="features">
                  <span 
                    v-for="feature in model.features" 
                    :key="feature"
                    class="feature-tag"
                  >
                    {{ feature }}
                  </span>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- 通知消息 -->
    <div v-if="notification" class="notification" :class="notification.type">
      {{ notification.message }}
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'AgentLLMConfig',
  data() {
    return {
      agentConfigs: [],
      availableProviders: {},
      currentSearchProvider: 'doubao',
      searchProviderStatus: false,
      notification: null,
      searchProviderDescriptions: {
        doubao: '豆包 (Doubao-Seed-1.6-Flash) - 字节跳动出品，支持联网搜索、视觉理解、函数调用等功能，响应速度快，推荐使用。',
        kimi: 'Kimi (Moonshot) - 月之暗面出品，支持超长上下文和联网搜索，适合处理长文本任务。'
      }
    };
  },
  async mounted() {
    await this.loadConfigs();
    await this.loadProviders();
    await this.loadSearchProvider();
  },
  methods: {
    async loadConfigs() {
      try {
        const response = await axios.get('/api/agent-llm-config/configs');
        this.agentConfigs = response.data.configs;
      } catch (error) {
        this.showNotification('加载配置失败: ' + error.message, 'error');
      }
    },
    
    async loadProviders() {
      try {
        const response = await axios.get('/api/agent-llm-config/available-providers');
        this.availableProviders = response.data.providers;
      } catch (error) {
        this.showNotification('加载提供商信息失败: ' + error.message, 'error');
      }
    },
    
    async loadSearchProvider() {
      try {
        const response = await axios.get('/api/llm-provider/current');
        this.currentSearchProvider = response.data.current_provider;
        this.searchProviderStatus = true;
      } catch (error) {
        console.error('加载搜索提供商失败:', error);
      }
    },
    
    async updateSearchProvider() {
      try {
        await axios.post('/api/llm-provider/set-default', {
          provider_id: this.currentSearchProvider
        });
        this.showNotification(`搜索提供商已切换到: ${this.currentSearchProvider}`, 'success');
      } catch (error) {
        this.showNotification('切换搜索提供商失败: ' + error.message, 'error');
      }
    },
    
    async updateSingleConfig(config) {
      try {
        await axios.put(`/api/agent-llm-config/configs/${config.agent_id}`, {
          agent_id: config.agent_id,
          llm_provider: config.llm_provider,
          model_name: config.model_name
        });
        this.showNotification(`${config.agent_name} 配置已更新`, 'success');
      } catch (error) {
        this.showNotification('更新配置失败: ' + error.message, 'error');
      }
    },
    
    async saveAllConfigs() {
      try {
        const configs = this.agentConfigs.map(c => ({
          agent_id: c.agent_id,
          llm_provider: c.llm_provider,
          model_name: c.model_name
        }));
        
        await axios.post('/api/agent-llm-config/configs/batch-update', {
          configs
        });
        
        this.showNotification('所有配置已保存', 'success');
      } catch (error) {
        this.showNotification('保存配置失败: ' + error.message, 'error');
      }
    },
    
    async resetToDefaults() {
      if (!confirm('确定要重置所有配置为默认值吗？')) {
        return;
      }
      
      try {
        const response = await axios.post('/api/agent-llm-config/reset-defaults');
        this.agentConfigs = response.data.configs;
        this.showNotification('配置已重置为默认值', 'success');
      } catch (error) {
        this.showNotification('重置配置失败: ' + error.message, 'error');
      }
    },
    
    onProviderChange(config) {
      // 当提供商改变时，自动选择该提供商的第一个模型
      const models = this.getAvailableModels(config.llm_provider);
      if (models.length > 0) {
        config.model_name = models[0].id;
      }
    },
    
    getAvailableModels(provider) {
      return this.availableProviders[provider]?.models || [];
    },
    
    getProviderStatus(provider) {
      const isAvailable = this.availableProviders[provider]?.available;
      return isAvailable ? 'available' : 'unavailable';
    },
    
    getProviderStatusText(provider) {
      const isAvailable = this.availableProviders[provider]?.available;
      return isAvailable ? '可用' : '未配置';
    },
    
    showNotification(message, type = 'info') {
      this.notification = { message, type };
      setTimeout(() => {
        this.notification = null;
      }, 3000);
    }
  }
};
</script>

<style scoped>
.agent-llm-config {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  margin-bottom: 30px;
}

.header h1 {
  font-size: 28px;
  color: #333;
  margin-bottom: 8px;
}

.subtitle {
  color: #666;
  font-size: 14px;
}

/* 搜索提供商配置 */
.search-provider-section {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
}

.search-provider-section h2 {
  font-size: 18px;
  margin-bottom: 15px;
  color: #333;
}

.provider-selector {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 10px;
}

.provider-selector label {
  font-weight: 500;
  color: #555;
}

.provider-selector select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  min-width: 200px;
}

.provider-status {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
}

.provider-status.active {
  background: #d4edda;
  color: #155724;
}

.provider-description {
  color: #666;
  font-size: 13px;
  line-height: 1.5;
  margin-top: 10px;
}

/* 配置表格 */
.config-table-section {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 30px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.table-header h2 {
  font-size: 18px;
  color: #333;
}

.actions {
  display: flex;
  gap: 10px;
}

.table-container {
  overflow-x: auto;
}

.config-table {
  width: 100%;
  border-collapse: collapse;
}

.config-table th {
  background: #f8f9fa;
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #555;
  font-size: 13px;
  border-bottom: 2px solid #dee2e6;
}

.config-table td {
  padding: 15px 12px;
  border-bottom: 1px solid #eee;
  font-size: 14px;
}

.agent-name {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 500;
}

.agent-icon {
  font-size: 20px;
}

.description {
  color: #666;
  font-size: 13px;
}

.provider-select,
.model-select {
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
  width: 100%;
  max-width: 200px;
}

.status-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.available {
  background: #d4edda;
  color: #155724;
}

.status-badge.unavailable {
  background: #f8d7da;
  color: #721c24;
}

/* 按钮样式 */
.btn-primary,
.btn-secondary,
.btn-update {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #545b62;
}

.btn-update {
  background: #28a745;
  color: white;
  padding: 6px 12px;
  font-size: 13px;
}

.btn-update:hover {
  background: #218838;
}

/* 提供商信息卡片 */
.providers-info {
  margin-top: 30px;
}

.providers-info h2 {
  font-size: 18px;
  margin-bottom: 20px;
  color: #333;
}

.provider-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.provider-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.provider-card.unavailable {
  opacity: 0.6;
}

.provider-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.provider-header h3 {
  font-size: 16px;
  color: #333;
}

.availability {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.availability.available {
  background: #d4edda;
  color: #155724;
}

.provider-models h4 {
  font-size: 14px;
  color: #555;
  margin-bottom: 10px;
}

.provider-models ul {
  list-style: none;
  padding: 0;
}

.provider-models li {
  margin-bottom: 15px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 4px;
}

.provider-models li strong {
  color: #333;
  font-size: 13px;
}

.provider-models li p {
  color: #666;
  font-size: 12px;
  margin: 5px 0;
}

.features {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 8px;
}

.feature-tag {
  background: #e7f3ff;
  color: #0066cc;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
}

/* 通知消息 */
.notification {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 15px 20px;
  border-radius: 4px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  z-index: 1000;
  animation: slideIn 0.3s ease-out;
}

.notification.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.notification.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.notification.info {
  background: #d1ecf1;
  color: #0c5460;
  border: 1px solid #bee5eb;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
</style>
