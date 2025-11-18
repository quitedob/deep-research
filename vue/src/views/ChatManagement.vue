<template>
  <div class="chat-management">
    <div class="header">
      <h1>对话管理</h1>
      <button @click="showCreateDialog = true" class="create-btn">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path d="M12 5v14M5 12h14" stroke-width="2" stroke-linecap="round"/>
        </svg>
        新建对话
      </button>
    </div>

    <!-- 模型选择 -->
    <div class="model-selector">
      <h3>选择模型</h3>
      <div class="model-grid">
        <div
          v-for="model in availableModels"
          :key="`${model.provider}-${model.model_name}`"
          class="model-card"
          :class="{ active: selectedModel?.model_name === model.model_name }"
          @click="selectModel(model)"
        >
          <div class="model-header">
            <h4>{{ model.display_name }}</h4>
            <span class="provider-badge">{{ model.provider }}</span>
          </div>
          <p class="model-description">{{ model.description }}</p>
          <div class="model-capabilities">
            <span
              v-for="cap in model.capabilities"
              :key="cap"
              class="capability-tag"
            >
              {{ cap }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 会话列表 -->
    <div class="sessions-section">
      <h3>我的对话</h3>
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="sessions.length === 0" class="empty">
        暂无对话记录
      </div>
      <div v-else class="sessions-list">
        <div
          v-for="session in sessions"
          :key="session.id"
          class="session-card"
          @click="openSession(session)"
        >
          <div class="session-header">
            <h4>{{ session.title }}</h4>
            <div class="session-actions">
              <button @click.stop="editSession(session)" class="icon-btn" title="编辑">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke-width="2"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke-width="2"/>
                </svg>
              </button>
              <button @click.stop="deleteSessionConfirm(session)" class="icon-btn danger" title="删除">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke-width="2"/>
                </svg>
              </button>
            </div>
          </div>
          <div class="session-meta">
            <span class="model-info">{{ session.llm_provider }} / {{ session.model_name }}</span>
            <span class="message-count">{{ session.message_count }} 条消息</span>
            <span class="time">{{ formatTime(session.updated_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建对话对话框 -->
    <div v-if="showCreateDialog" class="dialog-overlay" @click="showCreateDialog = false">
      <div class="dialog" @click.stop>
        <h3>创建新对话</h3>
        <form @submit.prevent="createSession">
          <div class="form-group">
            <label>对话标题</label>
            <input v-model="newSession.title" type="text" placeholder="输入对话标题" required />
          </div>
          <div class="form-group">
            <label>选择模型</label>
            <select v-model="newSession.provider" @change="updateModelOptions" required>
              <option value="">请选择提供商</option>
              <option value="deepseek">DeepSeek</option>
              <option value="zhipu">智谱AI</option>
            </select>
          </div>
          <div class="form-group" v-if="newSession.provider">
            <label>模型</label>
            <select v-model="newSession.model" required>
              <option value="">请选择模型</option>
              <option v-for="model in filteredModels" :key="model.model_name" :value="model.model_name">
                {{ model.display_name }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>系统提示词（可选）</label>
            <textarea v-model="newSession.systemPrompt" placeholder="输入系统提示词" rows="3"></textarea>
          </div>
          <div class="dialog-actions">
            <button type="button" @click="showCreateDialog = false" class="cancel-btn">取消</button>
            <button type="submit" class="submit-btn">创建</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { getModels, getSessions, createSession as createSessionAPI, deleteSession as deleteSessionAPI } from '@/api/chat.js';

const router = useRouter();
const loading = ref(false);
const sessions = ref([]);
const availableModels = ref([]);
const selectedModel = ref(null);
const showCreateDialog = ref(false);

const newSession = ref({
  title: '',
  provider: '',
  model: '',
  systemPrompt: ''
});

const token = computed(() => {
  return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
});

const filteredModels = computed(() => {
  if (!newSession.value.provider) return [];
  return availableModels.value.filter(m => m.provider === newSession.value.provider);
});

const formatTime = (timestamp) => {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now - date;
  
  if (diff < 60000) return '刚刚';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
  return date.toLocaleDateString();
};

const loadModels = async () => {
  try {
    const data = await getModels();
    availableModels.value = data.models;
    if (data.models.length > 0) {
      selectedModel.value = data.models[0];
    }
  } catch (error) {
    console.error('加载模型失败:', error);
    alert(error.message);
  }
};

const loadSessions = async () => {
  if (!token.value) {
    router.push('/login');
    return;
  }
  
  loading.value = true;
  try {
    sessions.value = await getSessions(token.value);
  } catch (error) {
    console.error('加载会话失败:', error);
    alert(error.message);
  } finally {
    loading.value = false;
  }
};

const selectModel = (model) => {
  selectedModel.value = model;
};

const updateModelOptions = () => {
  newSession.value.model = '';
};

const createSession = async () => {
  if (!token.value) {
    router.push('/login');
    return;
  }

  try {
    const sessionData = {
      title: newSession.value.title,
      llm_provider: newSession.value.provider,
      model_name: newSession.value.model,
      system_prompt: newSession.value.systemPrompt || null
    };

    await createSessionAPI(token.value, sessionData);
    showCreateDialog.value = false;
    
    // 重置表单
    newSession.value = {
      title: '',
      provider: '',
      model: '',
      systemPrompt: ''
    };
    
    // 重新加载会话列表
    await loadSessions();
    alert('对话创建成功！');
  } catch (error) {
    console.error('创建会话失败:', error);
    alert(error.message);
  }
};

const openSession = (session) => {
  // 跳转到对话页面
  router.push(`/chat/${session.id}`);
};

const editSession = (session) => {
  // TODO: 实现编辑功能
  console.log('编辑会话:', session);
};

const deleteSessionConfirm = async (session) => {
  if (!confirm(`确定要删除对话"${session.title}"吗？`)) return;
  
  if (!token.value) {
    router.push('/login');
    return;
  }

  try {
    await deleteSessionAPI(token.value, session.id);
    await loadSessions();
    alert('对话已删除');
  } catch (error) {
    console.error('删除会话失败:', error);
    alert(error.message);
  }
};

onMounted(() => {
  loadModels();
  loadSessions();
});
</script>

<style scoped>
.chat-management {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--spacing-xl);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
}

.header h1 {
  font-size: 32px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.create-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-lg);
  background: var(--gradient-blue);
  color: white;
  border: none;
  border-radius: var(--radius-large);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.create-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 122, 255, 0.4);
}

.model-selector {
  margin-bottom: var(--spacing-xl);
}

.model-selector h3 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-md);
}

.model-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--spacing-md);
}

.model-card {
  padding: var(--spacing-lg);
  background: var(--card-bg);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-large);
  cursor: pointer;
  transition: all 0.2s ease;
}

.model-card:hover {
  border-color: var(--accent-blue);
  transform: translateY(-2px);
}

.model-card.active {
  border-color: var(--accent-blue);
  background: rgba(0, 122, 255, 0.05);
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.model-header h4 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.provider-badge {
  padding: 4px 8px;
  background: var(--secondary-bg);
  color: var(--text-secondary);
  border-radius: var(--radius-small);
  font-size: 12px;
  font-weight: 500;
}

.model-description {
  font-size: 14px;
  color: var(--text-secondary);
  margin: var(--spacing-sm) 0;
}

.model-capabilities {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-sm);
}

.capability-tag {
  padding: 2px 8px;
  background: var(--hover-bg);
  color: var(--text-tertiary);
  border-radius: var(--radius-small);
  font-size: 12px;
}

.sessions-section h3 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-md);
}

.loading, .empty {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--text-secondary);
}

.sessions-list {
  display: grid;
  gap: var(--spacing-md);
}

.session-card {
  padding: var(--spacing-lg);
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-large);
  cursor: pointer;
  transition: all 0.2s ease;
}

.session-card:hover {
  border-color: var(--accent-blue);
  transform: translateY(-2px);
  box-shadow: var(--shadow-elev-medium);
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.session-header h4 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.session-actions {
  display: flex;
  gap: var(--spacing-xs);
}

.icon-btn {
  padding: var(--spacing-xs);
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: var(--radius-small);
  transition: all 0.2s ease;
}

.icon-btn:hover {
  background: var(--hover-bg);
  color: var(--text-primary);
}

.icon-btn.danger:hover {
  background: rgba(255, 59, 48, 0.1);
  color: var(--accent-red);
}

.session-meta {
  display: flex;
  gap: var(--spacing-md);
  font-size: 14px;
  color: var(--text-secondary);
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  width: 90%;
  max-width: 500px;
  padding: var(--spacing-xl);
  background: var(--card-bg);
  border-radius: var(--radius-xlarge);
  box-shadow: var(--shadow-elev-high);
}

.dialog h3 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-lg) 0;
}

.form-group {
  margin-bottom: var(--spacing-md);
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: var(--spacing-sm);
  border: 1px solid var(--input-border);
  border-radius: var(--radius-medium);
  background: var(--input-bg);
  color: var(--text-primary);
  font-size: 14px;
  transition: all 0.2s ease;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--input-focus-border);
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-lg);
}

.cancel-btn,
.submit-btn {
  padding: var(--spacing-sm) var(--spacing-lg);
  border: none;
  border-radius: var(--radius-medium);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cancel-btn {
  background: var(--secondary-bg);
  color: var(--text-secondary);
}

.cancel-btn:hover {
  background: var(--hover-bg);
}

.submit-btn {
  background: var(--gradient-blue);
  color: white;
}

.submit-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 122, 255, 0.4);
}
</style>
