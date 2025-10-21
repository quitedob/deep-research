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
                <div class="action-buttons">
                  <button
                    @click="updateSingleConfig(config)"
                    class="btn-update"
                  >
                    更新
                  </button>
                  <button
                    @click="testAgentConfig(config)"
                    class="btn-test"
                  >
                    测试
                  </button>
                </div>
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
import { agentConfigAPI, llmProviderAPI } from '@/services/api.js';

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
        const response = await agentConfigAPI.getAgentConfigs();
        this.agentConfigs = response.data || [];
        console.log('[AgentLLMConfig] 智能体配置加载成功:', this.agentConfigs);
      } catch (error) {
        console.error('[AgentLLMConfig] 加载配置失败:', error);
        this.showNotification('加载配置失败: ' + error.message, 'error');
      }
    },
    
    async loadProviders() {
      try {
        const response = await agentConfigAPI.getAvailableModels();
        this.availableProviders = response.data?.providers || {};
        console.log('[AgentLLMConfig] 可用提供商加载成功:', this.availableProviders);
      } catch (error) {
        console.error('[AgentLLMConfig] 加载可用提供商失败:', error);
        this.showNotification('加载提供商信息失败: ' + error.message, 'error');
      }
    },
    
    async loadSearchProvider() {
      try {
        const response = await llmProviderAPI.getCurrentProvider();
        this.currentSearchProvider = response.data.current_provider;
        this.searchProviderStatus = true;
      } catch (error) {
        console.error('加载搜索提供商失败:', error);
      }
    },
    
    async updateSearchProvider() {
      try {
        await llmProviderAPI.setDefaultProvider(this.currentSearchProvider);
        this.showNotification(`搜索提供商已切换到: ${this.currentSearchProvider}`, 'success');
      } catch (error) {
        this.showNotification('切换搜索提供商失败: ' + error.message, 'error');
      }
    },
    
    async updateSingleConfig(config) {
      try {
        await agentConfigAPI.updateAgentConfig(config.agent_id, {
          llm_provider: config.llm_provider,
          model_name: config.model_name
        });
        this.showNotification(`${config.agent_name} 配置已更新`, 'success');
        console.log('[AgentLLMConfig] 单个配置更新成功:', config);
      } catch (error) {
        console.error('[AgentLLMConfig] 更新配置失败:', error);
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

        await agentConfigAPI.batchUpdateConfigs(configs);
        this.showNotification('所有配置已保存', 'success');
        console.log('[AgentLLMConfig] 批量配置更新成功');
      } catch (error) {
        console.error('[AgentLLMConfig] 保存配置失败:', error);
        this.showNotification('保存配置失败: ' + error.message, 'error');
      }
    },
    
    async resetToDefaults() {
      if (!confirm('确定要重置所有配置为默认值吗？')) {
        return;
      }

      try {
        const response = await agentConfigAPI.resetToDefaults();
        this.agentConfigs = response.data || [];
        this.showNotification('配置已重置为默认值', 'success');
        console.log('[AgentLLMConfig] 配置重置成功');
      } catch (error) {
        console.error('[AgentLLMConfig] 重置配置失败:', error);
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
    
  async testAgentConfig(config) {
      if (!confirm(`确定要测试 ${config.agent_name} 的配置吗？这将发送一个测试请求。`)) {
        return;
      }

      const testPrompt = '你好，请简单介绍一下你的功能。';

      try {
        this.showNotification(`正在测试 ${config.agent_name} 配置...`, 'info');
        const response = await agentConfigAPI.testAgentConfig(config.agent_id, { prompt: testPrompt });
        this.showNotification(`${config.agent_name} 配置测试成功`, 'success');
        console.log('[AgentLLMConfig] 配置测试成功:', response);
      } catch (error) {
        console.error('[AgentLLMConfig] 配置测试失败:', error);
        this.showNotification(`配置测试失败: ${error.message}`, 'error');
      }
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
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  min-height: 100vh;
  position: relative;
}

.agent-llm-config::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(circle at 20% 80%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.1) 0%, transparent 50%);
  pointer-events: none;
}

.header {
  margin-bottom: 30px;
  text-align: center;
  padding: 20px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  position: relative;
  z-index: 1;
}

.header h1 {
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 8px;
}

.subtitle {
  color: #64748b;
  font-size: 16px;
  font-weight: 500;
}

/* 搜索提供商配置 */
.search-provider-section {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 30px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  position: relative;
  z-index: 1;
}

.search-provider-section h2 {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 15px;
}

.provider-selector {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 10px;
}

.provider-selector label {
  font-weight: 600;
  color: #475569;
}

.provider-selector select {
  padding: 10px 16px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
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
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  margin-bottom: 30px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  position: relative;
  z-index: 1;
  overflow: hidden;
  transition: all 0.3s ease;
}

.config-table-section:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
}

.table-header h2 {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
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
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.9);
  color: #667eea;
  border: 1px solid rgba(102, 126, 234, 0.3);
  backdrop-filter: blur(10px);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 1);
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.btn-update {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  color: white;
  padding: 8px 16px;
  font-size: 13px;
  box-shadow: 0 4px 15px rgba(56, 239, 125, 0.4);
}

.btn-update:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(56, 239, 125, 0.6);
}

/* 提供商信息卡片 */
.providers-info {
  margin-top: 40px;
}

.providers-info h2 {
  font-size: 24px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 30px;
  text-align: center;
}

.provider-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 24px;
}

.provider-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.3);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.provider-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #667eea, #764ba2, #667eea);
  background-size: 200% 100%;
  animation: gradientShift 3s ease-in-out infinite;
}

@keyframes gradientShift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.provider-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

.provider-card.unavailable {
  opacity: 0.6;
}

.provider-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.provider-header h3 {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
}

.availability {
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  backdrop-filter: blur(10px);
}

.availability.available {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(56, 239, 125, 0.3);
}

.provider-models h4 {
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 16px;
}

.provider-models ul {
  list-style: none;
  padding: 0;
}

.provider-models li {
  margin-bottom: 16px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  transition: all 0.2s ease;
}

.provider-models li:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.provider-models li strong {
  color: #333;
  font-size: 14px;
  font-weight: 600;
}

.provider-models li p {
  color: #666;
  font-size: 13px;
  margin: 8px 0;
  line-height: 1.5;
}

.features {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.feature-tag {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
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

/* 新增的按钮样式 */
.action-buttons {
  display: flex;
  gap: 8px;
}

.btn-test {
  padding: 8px 16px;
  border: 1px solid #28a745;
  background: #28a745;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-test:hover {
  background: #218838;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(40, 167, 69, 0.3);
}

.btn-test:active {
  transform: translateY(0);
}

.btn-update {
  padding: 8px 16px;
  border: 1px solid #007bff;
  background: #007bff;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-update:hover {
  background: #0056b3;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.3);
}

.btn-update:active {
  transform: translateY(0);
}

/* 表格样式优化 */
.config-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.config-table th {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 12px;
  text-align: left;
  font-weight: 600;
  font-size: 14px;
}

.config-table td {
  padding: 12px;
  border-bottom: 1px solid #eee;
  vertical-align: middle;
}

.config-table tr:last-child td {
  border-bottom: none;
}

.config-table tr:hover {
  background-color: #f8f9fa;
}

/* 选择框样式优化 */
.provider-select, .model-select {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  background: white;
  min-width: 150px;
  transition: border-color 0.2s;
}

.provider-select:focus, .model-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

/* 状态徽章优化 */
.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge.available {
  background: #d4edda;
  color: #155724;
}

.status-badge.unavailable {
  background: #f8d7da;
  color: #721c24;
}
</style>
