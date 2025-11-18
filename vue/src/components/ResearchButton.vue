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
    <div v-if="isResearching && researchProgress" class="research-progress">
      <div class="progress-header">
        <span>研究进度</span>
        <button @click="cancelResearch" class="cancel-btn">取消</button>
      </div>
      <div class="progress-content">
        <pre>{{ researchProgress }}</pre>
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
const researchProgress = ref('');
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

// 移除 getStepIcon 函数，不再需要

// 启动研究
const startResearch = async () => {
  if (isResearching.value || !props.message.trim()) return;
  
  isResearching.value = true;
  researchProgress.value = '🚀 研究任务已启动，正在初始化...';
  
  try {
    // 启动研究任务
    const response = await apiStartResearch(props.message);
    currentSessionId.value = response.session_id;
    
    // 订阅事件流
    researchEventSource.value = subscribeToResearchEvents(
      response.session_id,
      handleResearchEvent,
      handleResearchError
    );
    
  } catch (error) {
    console.error('启动研究失败:', error);
    const errorMessage = handleAPIError(error);
    researchProgress.value = `❌ 启动失败: ${errorMessage}`;
    emit('research-error', errorMessage);
    isResearching.value = false;
  }
};

// 处理研究事件
const handleResearchEvent = (data) => {
  console.log('收到 SSE 事件:', data.type);
  
  switch (data.type) {
    case 'connected':
      researchProgress.value = '✓ 已连接，等待研究结果...';
      break;
      
    case 'status_update':
      if (data.status === 'in_progress') {
        const progress = data.data?.progress || {};
        let msg = '🔍 正在进行深度研究...\n';
        
        if (progress.tools_used && progress.tools_used.length > 0) {
          msg += `使用工具: ${progress.tools_used.join(', ')}\n`;
        }
        
        if (progress.findings_count > 0) {
          msg += `已发现: ${progress.findings_count} 条信息`;
        }
        
        researchProgress.value = msg;
      }
      break;
      
    case 'completed':
      console.log('✓ 研究完成，收到最终报告');
      const reportText = data.data?.report_text || '研究完成，但报告为空。';
      const metadata = data.data?.metadata || {};
      console.log('证据数量:', metadata.evidence?.length || 0);
      completeResearch(reportText, metadata);
      break;
      
    case 'failed':
    case 'error':
      console.error('✗ 研究失败:', data.error);
      researchProgress.value = `❌ 研究失败: ${data.error || '未知错误'}`;
      emit('research-error', data.error);
      isResearching.value = false;
      if (researchEventSource.value) {
        researchEventSource.value.close();
        researchEventSource.value = null;
      }
      break;
  }
};

// 处理研究错误
const handleResearchError = (error) => {
  console.error('研究事件流错误:', error);
  const errorMessage = handleAPIError(error);
  researchProgress.value = `❌ 连接错误: ${errorMessage}`;
  emit('research-error', errorMessage);
  isResearching.value = false;
};

// 完成研究
const completeResearch = (report, metadata = {}) => {
  isResearching.value = false;
  researchProgress.value = '✓ 研究完成！';
  
  if (researchEventSource.value) {
    researchEventSource.value.close();
    researchEventSource.value = null;
  }
  
  // 将研究报告添加到聊天（包含 metadata）
  chatStore.addMessage({
    role: 'assistant',
    content: report,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    type: 'research_report',
    metadata: metadata  // ✅ 添加 metadata（包含证据链）
  });
  
  emit('research-complete', report);
  
  // 3秒后清除进度显示
  setTimeout(() => {
    researchProgress.value = '';
  }, 3000);
};

// 取消研究
const cancelResearch = () => {
  if (researchEventSource.value) {
    researchEventSource.value.close();
    researchEventSource.value = null;
  }
  
  isResearching.value = false;
  researchProgress.value = '❌ 研究已取消';
  
  setTimeout(() => {
    researchProgress.value = '';
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

.progress-content {
  padding: 12px 16px;
  max-height: 150px;
  overflow-y: auto;
}

.progress-content pre {
  margin: 0;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* 滚动条样式 */
.progress-content::-webkit-scrollbar {
  width: 4px;
}

.progress-content::-webkit-scrollbar-track {
  background: var(--secondary-bg);
  border-radius: 2px;
}

.progress-content::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 2px;
}

.progress-content::-webkit-scrollbar-thumb:hover {
  background: var(--text-secondary);
}
</style> 