<template>
  <div class="research-button-wrapper">
    <button 
      class="research-btn" 
      :class="{ 'researching': isResearching }"
      @click="startResearch"
      :disabled="isResearching || !message.trim()"
      :title="buttonTitle"
    >
      <span class="research-icon" :class="{ 'spinning': isResearching }">
        {{ isResearching ? '🔄' : '🔍' }}
      </span>
      <span class="research-text">
        {{ isResearching ? '研究中...' : '深度研究' }}
      </span>
    </button>
    
    <!-- 研究进度显示 -->
    <div v-if="isResearching && researchProgress.length > 0" class="research-progress">
      <div class="progress-header">
        <span>研究进度</span>
        <button @click="cancelResearch" class="cancel-btn">取消</button>
      </div>
      <div class="progress-steps">
        <div 
          v-for="(step, index) in researchProgress" 
          :key="index"
          class="progress-step"
          :class="step.status"
        >
          <span class="step-icon">{{ getStepIcon(step.type) }}</span>
          <span class="step-text">{{ step.message }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useChatStore } from '@/store';
import { startResearch as apiStartResearch, subscribeToResearchEvents, handleAPIError } from '@/services/api.js';

const props = defineProps({
  message: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['research-complete', 'research-error']);

const chatStore = useChatStore();
const isResearching = ref(false);
const researchProgress = ref([]);
const researchEventSource = ref(null);
const currentSessionId = ref(null);

const buttonTitle = computed(() => {
  if (!props.message.trim()) {
    return '请先输入要研究的内容';
  }
  if (isResearching.value) {
    return '正在进行深度研究...';
  }
  return '启动Agentic RAG深度研究，获取更全面的信息';
});

// 获取步骤图标
const getStepIcon = (type) => {
  const icons = {
    'node_start': '🚀',
    'agent_thought': '💭',
    'tool_call': '🔧',
    'research_iteration': '🔄',
    'final_report': '📋',
    'error': '❌'
  };
  return icons[type] || '📄';
};

// 启动研究
const startResearch = async () => {
  if (isResearching.value || !props.message.trim()) return;
  
  isResearching.value = true;
  researchProgress.value = [];
  
  try {
    // 启动研究任务
    const response = await apiStartResearch(props.message);
    
    currentSessionId.value = response.session_id;
    
    // 添加初始进度
    researchProgress.value.push({
      type: 'node_start',
      status: 'active',
      message: '研究任务已启动，正在初始化...'
    });
    
    // 订阅事件流
    researchEventSource.value = subscribeToResearchEvents(response.session_id, handleResearchEvent, handleResearchError);
    
  } catch (error) {
    console.error('启动研究失败:', error);
    const errorMessage = handleAPIError(error);
    
    researchProgress.value.push({
      type: 'error',
      status: 'error',
      message: `启动失败: ${errorMessage}`
    });
    
    emit('research-error', errorMessage);
    isResearching.value = false;
  }
};

// 处理研究事件
const handleResearchEvent = (event) => {
  const { event_type, payload } = event;
  
  switch (event_type) {
    case 'node_start':
      researchProgress.value.push({
        type: 'node_start',
        status: 'active',
        message: `开始执行: ${payload.node}`
      });
      break;
      
    case 'agent_thought':
      researchProgress.value.push({
        type: 'agent_thought',
        status: 'active',
        message: `思考: ${payload.thought}`
      });
      break;
      
    case 'tool_call':
      researchProgress.value.push({
        type: 'tool_call',
        status: 'active',
        message: `调用工具: ${payload.tool}`
      });
      break;
      
    case 'research_iteration':
      researchProgress.value.push({
        type: 'research_iteration',
        status: 'completed',
        message: `第${payload.iteration}轮研究: ${payload.query}`
      });
      break;
      
    case 'final_report':
      researchProgress.value.push({
        type: 'final_report',
        status: 'completed',
        message: '研究完成，生成最终报告'
      });
      
      // 研究完成
      completeResearch(payload.content);
      break;
      
    default:
      console.log('Unknown event type:', event_type, payload);
  }
  
  // 保持进度显示在最新
  setTimeout(() => {
    const progressEl = document.querySelector('.progress-steps');
    if (progressEl) {
      progressEl.scrollTop = progressEl.scrollHeight;
    }
  }, 100);
};

// 处理研究错误
const handleResearchError = (error) => {
  console.error('研究事件流错误:', error);
  const errorMessage = handleAPIError(error);
  
  researchProgress.value.push({
    type: 'error',
    status: 'error',
    message: `事件流错误: ${errorMessage}`
  });
  
  emit('research-error', errorMessage);
  isResearching.value = false;
};

// 完成研究
const completeResearch = (report) => {
  isResearching.value = false;
  
  if (researchEventSource.value) {
    researchEventSource.value.close();
    researchEventSource.value = null;
  }
  
  // 将研究报告添加到聊天
  chatStore.addMessage({
    role: 'assistant',
    content: report,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    type: 'research_report'
  });
  
  emit('research-complete', report);
  
  // 3秒后清除进度显示
  setTimeout(() => {
    researchProgress.value = [];
  }, 3000);
};

// 取消研究
const cancelResearch = () => {
  if (researchEventSource.value) {
    researchEventSource.value.close();
    researchEventSource.value = null;
  }
  
  isResearching.value = false;
  researchProgress.value.push({
    type: 'error',
    status: 'cancelled',
    message: '研究已取消'
  });
  
  setTimeout(() => {
    researchProgress.value = [];
  }, 2000);
};
</script>

<style scoped>
.research-button-wrapper {
  position: relative;
}

.research-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.research-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.research-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.research-btn.researching {
  background: linear-gradient(135deg, #ff9a56 0%, #ff6b6b 100%);
}

.research-icon {
  display: inline-block;
  font-size: 16px;
  transition: transform 0.3s ease;
}

.research-icon.spinning {
  animation: spin 2s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.research-progress {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--primary-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  margin-top: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  z-index: 100;
  max-width: 400px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  font-weight: 500;
  color: var(--text-primary);
}

.cancel-btn {
  background: none;
  border: none;
  color: var(--error-color);
  cursor: pointer;
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.cancel-btn:hover {
  background-color: var(--error-bg);
}

.progress-steps {
  max-height: 200px;
  overflow-y: auto;
  padding: 8px;
}

.progress-step {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px;
  margin-bottom: 4px;
  border-radius: 8px;
  font-size: 13px;
  transition: all 0.2s ease;
}

.progress-step.active {
  background-color: var(--secondary-bg);
  color: var(--text-primary);
}

.progress-step.completed {
  background-color: var(--success-bg);
  color: var(--success-color);
}

.progress-step.error,
.progress-step.cancelled {
  background-color: var(--error-bg);
  color: var(--error-color);
}

.step-icon {
  flex-shrink: 0;
  font-size: 14px;
}

.step-text {
  flex: 1;
  line-height: 1.4;
}

/* 滚动条样式 */
.progress-steps::-webkit-scrollbar {
  width: 4px;
}

.progress-steps::-webkit-scrollbar-track {
  background: var(--secondary-bg);
  border-radius: 2px;
}

.progress-steps::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 2px;
}

.progress-steps::-webkit-scrollbar-thumb:hover {
  background: var(--text-secondary);
}
</style> 