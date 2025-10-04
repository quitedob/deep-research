<template>
  <div class="agent-management">
    <div class="page-header">
      <h1>智能体管理</h1>
      <p class="subtitle">管理和调用专业AI智能体</p>
    </div>

    <!-- Agent列表 -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else class="agents-grid">
      <div 
        v-for="agent in agents" 
        :key="agent.id"
        class="agent-card"
        @click="selectAgent(agent)"
      >
        <div class="agent-icon">
          <i :class="getAgentIcon(agent.base_name)"></i>
        </div>
        <h3>{{ agent.name }}</h3>
        <p class="agent-description">{{ agent.description }}</p>
        <div class="agent-capabilities">
          <span 
            v-for="capability in agent.capabilities" 
            :key="capability"
            class="capability-tag"
          >
            {{ capability }}
          </span>
        </div>
        <button @click.stop="callAgent(agent)" class="btn-call">
          <i class="fas fa-play"></i> 调用
        </button>
      </div>
    </div>

    <!-- Agent调用模态框 -->
    <div v-if="showCallModal" class="modal-overlay" @click="showCallModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <div>
            <h2>调用 {{ selectedAgent?.name }}</h2>
            <p class="modal-subtitle">{{ selectedAgent?.description }}</p>
          </div>
          <button @click="showCallModal = false" class="btn-close">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="modal-body">
          <div class="form-group">
            <label>任务描述 *</label>
            <textarea 
              v-model="callRequest.prompt" 
              rows="6"
              placeholder="请描述您希望Agent完成的任务..."
              required
            ></textarea>
          </div>

          <div class="form-group">
            <label>会话ID (可选)</label>
            <input 
              v-model="callRequest.session_id" 
              type="text"
              placeholder="留空将创建新会话"
            />
            <small>使用相同的会话ID可以保持对话上下文</small>
          </div>

          <div class="form-group">
            <label>上下文信息 (可选)</label>
            <textarea 
              v-model="contextJson" 
              rows="3"
              placeholder='{"key": "value"}'
            ></textarea>
            <small>JSON格式的额外上下文信息</small>
          </div>

          <div class="form-actions">
            <button @click="showCallModal = false" class="btn-secondary">
              取消
            </button>
            <button @click="executeCall" class="btn-primary" :disabled="calling">
              {{ calling ? '执行中...' : '执行' }}
            </button>
          </div>

          <!-- 结果显示 -->
          <div v-if="callResult" class="result-section">
            <h3>执行结果</h3>
            <div v-if="callResult.status === 'success'" class="result-success">
              <div class="result-header">
                <i class="fas fa-check-circle"></i>
                <span>执行成功</span>
              </div>
              <div class="result-content">
                {{ callResult.result }}
              </div>
            </div>
            <div v-else class="result-error">
              <div class="result-header">
                <i class="fas fa-exclamation-circle"></i>
                <span>执行失败</span>
              </div>
              <div class="result-content">
                {{ callResult.error }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 多Agent协作模态框 -->
    <div class="collaboration-section">
      <h2>多智能体协作</h2>
      <p>选择多个Agent协同完成复杂任务</p>
      
      <div class="collaboration-form">
        <div class="form-group">
          <label>任务描述 *</label>
          <textarea 
            v-model="collaborationTask" 
            rows="4"
            placeholder="描述需要多个Agent协作完成的任务..."
          ></textarea>
        </div>

        <div class="form-group">
          <label>选择参与的Agents *</label>
          <div class="agent-selector">
            <label 
              v-for="agent in agents" 
              :key="agent.id"
              class="agent-checkbox"
            >
              <input 
                type="checkbox" 
                :value="agent.id"
                v-model="selectedAgentIds"
              />
              <span>{{ agent.name }}</span>
            </label>
          </div>
        </div>

        <button 
          @click="executeCollaboration" 
          class="btn-primary btn-large"
          :disabled="collaborating || selectedAgentIds.length === 0"
        >
          <i class="fas fa-users"></i>
          {{ collaborating ? '执行中...' : '开始协作' }}
        </button>

        <!-- 协作结果 -->
        <div v-if="collaborationResult" class="collaboration-result">
          <h3>协作结果</h3>
          <div 
            v-for="(result, index) in collaborationResult.results" 
            :key="index"
            class="agent-result"
          >
            <div class="agent-result-header">
              <h4>{{ result.agent_name }}</h4>
              <span v-if="result.error" class="error-badge">失败</span>
              <span v-else class="success-badge">成功</span>
            </div>
            <div class="agent-result-content">
              {{ result.result || result.error }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../services/api'

export default {
  name: 'AgentManagement',
  data() {
    return {
      agents: [],
      loading: false,
      showCallModal: false,
      selectedAgent: null,
      calling: false,
      callRequest: {
        prompt: '',
        session_id: '',
        context: null
      },
      contextJson: '',
      callResult: null,
      collaborationTask: '',
      selectedAgentIds: [],
      collaborating: false,
      collaborationResult: null
    }
  },
  mounted() {
    this.loadAgents()
  },
  methods: {
    async loadAgents() {
      this.loading = true
      try {
        const response = await api.get('/agents/list')
        this.agents = response.data
      } catch (error) {
        console.error('加载Agent列表失败:', error)
        this.$toast?.error('加载Agent列表失败')
      } finally {
        this.loading = false
      }
    },
    
    selectAgent(agent) {
      this.selectedAgent = agent
    },
    
    callAgent(agent) {
      this.selectedAgent = agent
      this.showCallModal = true
      this.callResult = null
      this.callRequest = {
        prompt: '',
        session_id: '',
        context: null
      }
      this.contextJson = ''
    },
    
    async executeCall() {
      if (!this.callRequest.prompt.trim()) {
        this.$toast?.error('请输入任务描述')
        return
      }
      
      this.calling = true
      this.callResult = null
      
      try {
        // 解析上下文JSON
        let context = null
        if (this.contextJson.trim()) {
          try {
            context = JSON.parse(this.contextJson)
          } catch (e) {
            this.$toast?.error('上下文JSON格式错误')
            this.calling = false
            return
          }
        }
        
        const response = await api.post('/agents/call', {
          agent_id: this.selectedAgent.id,
          prompt: this.callRequest.prompt,
          session_id: this.callRequest.session_id || null,
          context: context
        })
        
        this.callResult = response.data
        
        if (response.data.status === 'success') {
          this.$toast?.success('Agent执行成功')
        } else {
          this.$toast?.error('Agent执行失败')
        }
      } catch (error) {
        console.error('调用Agent失败:', error)
        this.$toast?.error('调用Agent失败')
        this.callResult = {
          status: 'error',
          error: error.response?.data?.detail || error.message
        }
      } finally {
        this.calling = false
      }
    },
    
    async executeCollaboration() {
      if (!this.collaborationTask.trim()) {
        this.$toast?.error('请输入任务描述')
        return
      }
      
      if (this.selectedAgentIds.length === 0) {
        this.$toast?.error('请至少选择一个Agent')
        return
      }
      
      this.collaborating = true
      this.collaborationResult = null
      
      try {
        const response = await api.post('/agents/collaborate', {
          task: this.collaborationTask,
          agent_ids: this.selectedAgentIds
        })
        
        this.collaborationResult = response.data
        this.$toast?.success('协作任务完成')
      } catch (error) {
        console.error('协作执行失败:', error)
        this.$toast?.error('协作执行失败')
      } finally {
        this.collaborating = false
      }
    },
    
    getAgentIcon(baseName) {
      const iconMap = {
        planner: 'fas fa-clipboard-list',
        searcher: 'fas fa-search',
        analyzer: 'fas fa-chart-line',
        writer: 'fas fa-pen',
        reviewer: 'fas fa-check-double',
        default: 'fas fa-robot'
      }
      return iconMap[baseName] || iconMap.default
    }
  }
}
</script>

<style scoped>
.agent-management {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 3rem;
  text-align: center;
}

.page-header h1 {
  font-size: 2.5rem;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #666;
  font-size: 1.1rem;
}

.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 2rem;
  margin-bottom: 4rem;
}

.agent-card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  cursor: pointer;
  transition: all 0.3s;
  text-align: center;
}

.agent-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
}

.agent-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.agent-icon i {
  font-size: 2.5rem;
  color: white;
}

.agent-card h3 {
  font-size: 1.5rem;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.agent-description {
  color: #666;
  line-height: 1.6;
  margin-bottom: 1rem;
  min-height: 48px;
}

.agent-capabilities {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.capability-tag {
  padding: 0.25rem 0.75rem;
  background: #f0f0f0;
  border-radius: 12px;
  font-size: 0.75rem;
  color: #666;
}

.btn-call {
  width: 100%;
  padding: 0.75rem;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.btn-call:hover {
  background: #45a049;
}

.collaboration-section {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.collaboration-section h2 {
  font-size: 1.8rem;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.collaboration-section > p {
  color: #666;
  margin-bottom: 2rem;
}

.agent-selector {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
  padding: 1rem;
  background: #f9f9f9;
  border-radius: 8px;
}

.agent-checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  transition: background 0.2s;
}

.agent-checkbox:hover {
  background: #f0f0f0;
}

.agent-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.btn-large {
  width: 100%;
  padding: 1rem;
  font-size: 1.1rem;
  margin-top: 1.5rem;
}

.collaboration-result {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 2px solid #eee;
}

.collaboration-result h3 {
  font-size: 1.3rem;
  color: #2c3e50;
  margin-bottom: 1.5rem;
}

.agent-result {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1rem;
}

.agent-result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.agent-result-header h4 {
  font-size: 1.1rem;
  color: #2c3e50;
  margin: 0;
}

.success-badge {
  padding: 0.25rem 0.75rem;
  background: #d1e7dd;
  color: #0f5132;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.error-badge {
  padding: 0.25rem 0.75rem;
  background: #f8d7da;
  color: #842029;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.agent-result-content {
  color: #666;
  line-height: 1.6;
  white-space: pre-wrap;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  padding: 2rem;
  border-bottom: 1px solid #eee;
}

.modal-header h2 {
  font-size: 1.8rem;
  color: #2c3e50;
  margin: 0 0 0.5rem 0;
}

.modal-subtitle {
  color: #666;
  font-size: 0.9rem;
  margin: 0;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.btn-close:hover {
  background: #f5f5f5;
  color: #666;
}

.modal-body {
  padding: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #333;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 0.9rem;
  font-family: inherit;
}

.form-group textarea {
  resize: vertical;
}

.form-group small {
  display: block;
  margin-top: 0.5rem;
  color: #999;
  font-size: 0.85rem;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 2rem;
}

.btn-primary,
.btn-secondary {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #4CAF50;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #45a049;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f5f5f5;
  color: #666;
}

.btn-secondary:hover {
  background: #e0e0e0;
}

.result-section {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 2px solid #eee;
}

.result-section h3 {
  font-size: 1.2rem;
  color: #2c3e50;
  margin-bottom: 1rem;
}

.result-success,
.result-error {
  border-radius: 8px;
  padding: 1.5rem;
}

.result-success {
  background: #d1e7dd;
  border: 1px solid #badbcc;
}

.result-error {
  background: #f8d7da;
  border: 1px solid #f5c2c7;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  font-weight: 600;
}

.result-success .result-header {
  color: #0f5132;
}

.result-error .result-header {
  color: #842029;
}

.result-content {
  color: #333;
  line-height: 1.6;
  white-space: pre-wrap;
}

.loading {
  text-align: center;
  padding: 4rem 2rem;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
