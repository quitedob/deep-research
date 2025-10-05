<template>
  <div class="llm-provider-settings">
    <div class="settings-header">
      <h1>LLM 提供商设置</h1>
      <p class="subtitle">管理和切换不同的大语言模型提供商</p>
    </div>

    <!-- 当前使用的提供商 -->
    <div class="current-provider-card">
      <div class="card-header">
        <h2>🎯 当前使用</h2>
      </div>
      <div v-if="currentProvider" class="current-provider-content">
        <div class="provider-badge">
          <span class="provider-icon">{{ getProviderIcon(currentProvider.id) }}</span>
          <div class="provider-info">
            <h3>{{ currentProvider.display_name }}</h3>
            <p>{{ currentProvider.description }}</p>
          </div>
          <span class="status-badge active">使用中</span>
        </div>
        
        <div class="provider-details">
          <div class="detail-section">
            <h4>支持的模型</h4>
            <div class="model-tags">
              <span v-for="model in currentProvider.models" :key="model" class="model-tag">
                {{ model }}
              </span>
            </div>
          </div>
          
          <div class="detail-section">
            <h4>功能特性</h4>
            <div class="feature-tags">
              <span v-for="feature in currentProvider.features" :key="feature" class="feature-tag">
                ✓ {{ feature }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 所有可用的提供商 -->
    <div class="providers-section">
      <h2>📋 所有提供商</h2>
      
      <div v-if="loading" class="loading">加载中...</div>
      
      <div v-else-if="error" class="error">{{ error }}</div>
      
      <div v-else class="providers-grid">
        <div 
          v-for="provider in providers" 
          :key="provider.id"
          :class="['provider-card', { 
            'is-default': provider.is_default,
            'is-unavailable': !provider.is_available 
          }]"
        >
          <div class="provider-card-header">
            <div class="provider-title">
              <span class="provider-icon-large">{{ getProviderIcon(provider.id) }}</span>
              <div>
                <h3>{{ provider.display_name }}</h3>
                <p class="provider-id">{{ provider.id }}</p>
              </div>
            </div>
            
            <div class="provider-status">
              <span v-if="provider.is_default" class="badge badge-primary">默认</span>
              <span v-if="provider.is_available" class="badge badge-success">可用</span>
              <span v-else class="badge badge-warning">未配置</span>
            </div>
          </div>
          
          <p class="provider-description">{{ provider.description }}</p>
          
          <div class="provider-features">
            <h4>功能特性</h4>
            <ul>
              <li v-for="feature in provider.features.slice(0, 3)" :key="feature">
                {{ feature }}
              </li>
            </ul>
          </div>
          
          <div class="provider-models">
            <h4>支持模型 ({{ provider.models.length }})</h4>
            <div class="model-preview">
              <span class="model-tag-small">{{ provider.models[0] }}</span>
              <span v-if="provider.models.length > 1" class="more-models">
                +{{ provider.models.length - 1 }} 更多
              </span>
            </div>
          </div>
          
          <div class="provider-actions">
            <button 
              v-if="!provider.is_default && provider.is_available"
              @click="setDefaultProvider(provider.id)"
              class="btn-set-default"
            >
              设为默认
            </button>
            
            <button 
              v-if="provider.is_default"
              class="btn-current"
              disabled
            >
              当前使用
            </button>
            
            <button 
              v-if="!provider.is_available"
              class="btn-configure"
              @click="showConfigureHelp(provider.id)"
            >
              配置说明
            </button>
            
            <button 
              @click="testConnection(provider.id)"
              class="btn-test"
              :disabled="!provider.is_available"
            >
              测试连接
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 配置帮助模态框 -->
    <div v-if="showConfigModal" class="modal-overlay" @click="closeConfigModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>配置 {{ selectedProviderName }}</h3>
          <button @click="closeConfigModal" class="btn-close">×</button>
        </div>
        
        <div class="modal-body">
          <div class="config-help">
            <h4>环境变量配置</h4>
            <p>请在 <code>.env</code> 文件中添加以下配置：</p>
            
            <div v-if="selectedProviderId === 'doubao'" class="config-code">
              <pre>DOUBAO_API_KEY=your_doubao_api_key_here
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
DOUBAO_MODEL=doubao-seed-1-6-flash-250615</pre>
            </div>
            
            <div v-if="selectedProviderId === 'kimi'" class="config-code">
              <pre>KIMI_API_KEY=your_kimi_api_key_here
KIMI_BASE_URL=https://api.moonshot.cn/v1
KIMI_MODEL=moonshot-v1-8k</pre>
            </div>
            
            <div v-if="selectedProviderId === 'deepseek'" class="config-code">
              <pre>DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1</pre>
            </div>
            
            <div v-if="selectedProviderId === 'ollama'" class="config-code">
              <pre>OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_SMALL_MODEL=gemma3:4b
OLLAMA_LARGE_MODEL=qwen3:32b</pre>
            </div>
            
            <h4>获取 API Key</h4>
            <ul class="help-links">
              <li v-if="selectedProviderId === 'doubao'">
                访问 <a href="https://console.volcengine.com/ark" target="_blank">火山方舟控制台</a> 获取 API Key
              </li>
              <li v-if="selectedProviderId === 'kimi'">
                访问 <a href="https://platform.moonshot.cn" target="_blank">Moonshot AI 平台</a> 获取 API Key
              </li>
              <li v-if="selectedProviderId === 'deepseek'">
                访问 <a href="https://platform.deepseek.com" target="_blank">DeepSeek 平台</a> 获取 API Key
              </li>
              <li v-if="selectedProviderId === 'ollama'">
                访问 <a href="https://ollama.com" target="_blank">Ollama 官网</a> 下载并安装本地模型
              </li>
            </ul>
            
            <p class="note">⚠️ 配置完成后需要重启应用才能生效</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import api from '@/services/api';

export default {
  name: 'LLMProviderSettings',
  
  setup() {
    const providers = ref([]);
    const currentProvider = ref(null);
    const loading = ref(false);
    const error = ref(null);
    
    const showConfigModal = ref(false);
    const selectedProviderId = ref('');
    const selectedProviderName = ref('');
    
    // 加载提供商列表
    const loadProviders = async () => {
      loading.value = true;
      error.value = null;
      
      try {
        const response = await api.get('/llm-provider/list');
        providers.value = response.data;
        
        // 找到当前默认的提供商
        currentProvider.value = providers.value.find(p => p.is_default);
      } catch (err) {
        error.value = '加载提供商列表失败: ' + (err.response?.data?.detail || err.message);
      } finally {
        loading.value = false;
      }
    };
    
    // 设置默认提供商
    const setDefaultProvider = async (providerId) => {
      if (!confirm(`确定要将此提供商设置为默认吗？`)) {
        return;
      }
      
      try {
        await api.post('/llm-provider/set-default', {
          provider_id: providerId,
          is_default: true
        });
        
        alert('默认提供商已更新');
        await loadProviders();
      } catch (err) {
        alert('设置失败: ' + (err.response?.data?.detail || err.message));
      }
    };
    
    // 测试连接
    const testConnection = async (providerId) => {
      try {
        const response = await api.get(`/llm-provider/test/${providerId}`);
        
        if (response.data.success) {
          alert(`✓ ${response.data.provider_name} 连接测试成功！`);
        } else {
          alert(`✗ ${response.data.message}`);
        }
      } catch (err) {
        alert('测试失败: ' + (err.response?.data?.detail || err.message));
      }
    };
    
    // 显示配置帮助
    const showConfigureHelp = (providerId) => {
      const provider = providers.value.find(p => p.id === providerId);
      selectedProviderId.value = providerId;
      selectedProviderName.value = provider.display_name;
      showConfigModal.value = true;
    };
    
    // 关闭配置模态框
    const closeConfigModal = () => {
      showConfigModal.value = false;
      selectedProviderId.value = '';
      selectedProviderName.value = '';
    };
    
    // 获取提供商图标
    const getProviderIcon = (providerId) => {
      const icons = {
        doubao: '🚀',
        kimi: '🌙',
        deepseek: '🔍',
        ollama: '🦙'
      };
      return icons[providerId] || '🤖';
    };
    
    // 初始化
    onMounted(() => {
      loadProviders();
    });
    
    return {
      providers,
      currentProvider,
      loading,
      error,
      showConfigModal,
      selectedProviderId,
      selectedProviderName,
      loadProviders,
      setDefaultProvider,
      testConnection,
      showConfigureHelp,
      closeConfigModal,
      getProviderIcon
    };
  }
};
</script>

<style scoped>
.llm-provider-settings {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.settings-header {
  margin-bottom: 2rem;
}

.settings-header h1 {
  font-size: 2rem;
  color: #333;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #666;
  font-size: 1rem;
}

/* 当前提供商卡片 */
.current-provider-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 2rem;
  color: white;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.current-provider-card .card-header h2 {
  margin: 0 0 1.5rem 0;
  font-size: 1.5rem;
}

.provider-badge {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.provider-icon {
  font-size: 3rem;
}

.provider-info h3 {
  font-size: 1.5rem;
  margin: 0 0 0.5rem 0;
}

.provider-info p {
  margin: 0;
  opacity: 0.9;
}

.status-badge.active {
  margin-left: auto;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  font-weight: 500;
}

.provider-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.detail-section h4 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  opacity: 0.9;
}

.model-tags,
.feature-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.model-tag,
.feature-tag {
  padding: 0.4rem 0.8rem;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  font-size: 0.85rem;
}

/* 提供商网格 */
.providers-section {
  margin-top: 2rem;
}

.providers-section h2 {
  font-size: 1.5rem;
  color: #333;
  margin-bottom: 1.5rem;
}

.providers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.provider-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}

.provider-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.provider-card.is-default {
  border: 2px solid #667eea;
}

.provider-card.is-unavailable {
  opacity: 0.7;
}

.provider-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.provider-title {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.provider-icon-large {
  font-size: 2.5rem;
}

.provider-title h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #333;
}

.provider-id {
  margin: 0.25rem 0 0 0;
  font-size: 0.85rem;
  color: #999;
  font-family: monospace;
}

.provider-status {
  display: flex;
  gap: 0.5rem;
}

.badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.badge-primary {
  background: #667eea;
  color: white;
}

.badge-success {
  background: #48bb78;
  color: white;
}

.badge-warning {
  background: #ed8936;
  color: white;
}

.provider-description {
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 1rem;
  line-height: 1.5;
}

.provider-features,
.provider-models {
  margin-bottom: 1rem;
}

.provider-features h4,
.provider-models h4 {
  font-size: 0.9rem;
  color: #333;
  margin: 0 0 0.5rem 0;
}

.provider-features ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.provider-features li {
  padding: 0.25rem 0;
  font-size: 0.85rem;
  color: #666;
}

.model-preview {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.model-tag-small {
  padding: 0.25rem 0.5rem;
  background: #f0f0f0;
  border-radius: 4px;
  font-size: 0.75rem;
  font-family: monospace;
}

.more-models {
  font-size: 0.75rem;
  color: #999;
}

.provider-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.provider-actions button {
  flex: 1;
  padding: 0.6rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: opacity 0.2s;
}

.provider-actions button:hover:not(:disabled) {
  opacity: 0.8;
}

.provider-actions button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.btn-set-default {
  background: #667eea;
  color: white;
}

.btn-current {
  background: #48bb78;
  color: white;
}

.btn-configure {
  background: #ed8936;
  color: white;
}

.btn-test {
  background: #4299e1;
  color: white;
}

/* 模态框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.5rem;
}

.btn-close {
  background: none;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  color: #999;
}

.btn-close:hover {
  color: #333;
}

.modal-body {
  padding: 1.5rem;
}

.config-help h4 {
  margin: 0 0 1rem 0;
  color: #333;
}

.config-help p {
  margin: 0 0 1rem 0;
  color: #666;
}

.config-code {
  margin: 1rem 0;
}

.config-code pre {
  background: #f5f5f5;
  padding: 1rem;
  border-radius: 6px;
  overflow-x: auto;
  font-family: monospace;
  font-size: 0.9rem;
}

code {
  background: #f5f5f5;
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  font-family: monospace;
}

.help-links {
  list-style: none;
  padding: 0;
  margin: 1rem 0;
}

.help-links li {
  padding: 0.5rem 0;
}

.help-links a {
  color: #667eea;
  text-decoration: none;
}

.help-links a:hover {
  text-decoration: underline;
}

.note {
  margin-top: 1.5rem;
  padding: 1rem;
  background: #fff3cd;
  border-left: 4px solid #ffc107;
  border-radius: 4px;
  color: #856404;
}

/* 加载和错误状态 */
.loading,
.error {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.error {
  color: #f44336;
}
</style>
