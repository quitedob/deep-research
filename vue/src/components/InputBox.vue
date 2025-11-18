<template>
  <div class="input-box-container">
    <div class="main-input-wrapper">
      <div class="text-area-wrapper">
        <textarea
            v-model="inputText"
            @keydown.enter.exact.prevent="sendMessage"
            @keydown.enter.shift.exact.prevent="insertNewline"
            :placeholder="placeholderText"
            class="text-input"
            ref="textareaRef"
            rows="1"
            @input="autoGrowTextarea"
        ></textarea>
      </div>

      <button
          class="send-btn"
          title="发送"
          @click="sendMessage"
          :disabled="!inputText.trim()">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
      </button>
    </div>

    <div class="attachments-bar">
      <div class="plus-menu-container" ref="plusMenuContainerRef">
        <button class="attach-btn plus-btn" title="添加" @click="toggleAttachmentMenu">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        </button>
        <div v-if="isAttachmentMenuOpen" class="attachment-menu-popup">
          <ul>
            <li @click="handleMenuAction('upload_files')">
              <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg>
              上传文件
            </li>
            <li @click="handleMenuAction('add_from_drive')">
              <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg> 从云盘添加
            </li>
            <li @click="handleMenuAction('import_code')">
              <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>
              导入代码
            </li>
          </ul>
        </div>
      </div>
      <button
        class="attach-btn deep-think-btn"
        :class="{ 'active': isDeepThinkMode }"
        @click="toggleDeepThinkMode"
        :title="isDeepThinkMode ? '深度思考模式（当前激活）' : '开启深度思考模式'">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2z"></path>
          <path d="M12 6v6l4 2"></path>
          <circle cx="12" cy="12" r="2"></circle>
        </svg>
      </button>
      <button
        class="attach-btn web-search-btn"
        :class="{ 'active': isWebSearchMode }"
        @click="toggleWebSearchMode"
        :title="isWebSearchMode ? '联网搜索模式（当前激活）' : '开启联网搜索模式'">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"></circle>
          <path d="m21 21-4.35-4.35"></path>
          <line x1="19" y1="5" x2="13.5" y2="5"></line>
          <line x1="13.5" y1="5" x2="13.5" y2="1"></line>
          <line x1="13.5" y1="1" x2="17" y2="1"></line>
        </svg>
      </button>
      <button
        class="attach-btn research-btn"
        :class="{ 'active': isDeepResearchMode }"
        @click="toggleResearchMode"
        :title="isDeepResearchMode ? '深度研究模式（当前激活）' : '开启深度研究模式'">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"></circle>
          <path d="M21 21l-4.35-4.35"></path>
          <circle cx="11" cy="11" r="3"></circle>
        </svg>
      </button>

      <!-- 任务进度面板 -->
      <div v-if="showTaskProgress" class="task-progress-panel">
        <div class="progress-header">
          <div class="progress-info">
            <h4>深度研究任务进度</h4>
            <span class="task-status">{{ taskProgress.status }}</span>
          </div>
          <button @click="showTaskProgress = false" class="close-progress">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <div class="progress-bar-container">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: taskProgress.progress + '%' }"></div>
          </div>
          <span class="progress-text">{{ taskProgress.progress }}%</span>
        </div>

        <div class="task-steps">
          <div
            v-for="(step, index) in taskProgress.steps"
            :key="index"
            :class="['task-step', step.status]"
          >
            <div class="step-icon">
              <span v-if="step.status === 'completed'">✅</span>
              <span v-else-if="step.status === 'running'">⏳</span>
              <span v-else-if="step.status === 'error'">❌</span>
              <span v-else>⏸️</span>
            </div>
            <div class="step-content">
              <div class="step-title">{{ step.title }}</div>
              <div class="step-detail">{{ step.detail }}</div>
            </div>
          </div>
        </div>

        <div class="progress-actions">
          <button @click="pauseTask" v-if="taskProgress.status === 'running'" class="btn-pause">
            暂停
          </button>
          <button @click="resumeTask" v-if="taskProgress.status === 'paused'" class="btn-resume">
            继续
          </button>
          <button @click="cancelTask" class="btn-cancel">
            取消
          </button>
        </div>

        <div class="estimated-time" v-if="taskProgress.estimatedTime">
          预计完成时间: {{ taskProgress.estimatedTime }}
        </div>
      </div>
      <button class="attach-btn" title="画布">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg>
      </button>

      <button class="attach-btn mic-btn" title="语音输入">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line></svg>
      </button>
    </div>
  </div>
  
  <!-- 文件上传弹窗 -->
  <div v-if="showFileUpload" class="file-upload-overlay">
    <div class="file-upload-modal">
      <div class="modal-header">
        <h3>文件上传</h3>
        <button @click="showFileUpload = false" class="close-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>
      <div class="modal-content">
        <FileUpload 
          :auto-upload="false"
          :max-files="5"
          @upload-success="handleFileUploadSuccess"
          @upload-error="handleFileUploadError"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue';
import FileUpload from './FileUpload.vue';

const inputText = ref('');
const textareaRef = ref(null);
const emit = defineEmits(['send-message', 'send-research', 'send-web-search', 'send-deep-think', 'research-complete', 'research-error']);
const isDeepResearchMode = ref(false);
const isWebSearchMode = ref(false);
const isDeepThinkMode = ref(false);
const showTaskProgress = ref(false);
const placeholderText = ref('输入您的问题或指令 (Enter 发送, Shift + Enter 换行)...');
const isAttachmentMenuOpen = ref(false);
const plusMenuContainerRef = ref(null);

// 任务进度状态
const taskProgress = ref({
  status: 'running',
  progress: 35,
  estimatedTime: '约2分钟',
  steps: [
    {
      title: '分析研究主题',
      detail: '正在理解您的研究需求...',
      status: 'completed'
    },
    {
      title: '收集相关信息',
      detail: '从多个来源获取数据...',
      status: 'running'
    },
    {
      title: '整理和分析',
      detail: '正在处理收集到的信息',
      status: 'pending'
    },
    {
      title: '生成报告',
      detail: '撰写研究报告',
      status: 'pending'
    }
  ]
});

// (新增) 允许父组件调用此方法来设置输入框文本
const setInputText = (text) => {
  inputText.value = text;
  nextTick(() => {
    autoGrowTextarea();
    textareaRef.value?.focus();
  });
};
defineExpose({ setInputText });

// (修复) 发送消息逻辑
const sendMessage = () => {
  const text = inputText.value.trim();
  if (!text) return; // 不发送空消息
  
  // 根据当前模式发送不同类型的事件
  if (isDeepThinkMode.value) {
    emit('send-deep-think', text);
  } else if (isDeepResearchMode.value) {
    emit('send-research', text);
  } else if (isWebSearchMode.value) {
    emit('send-web-search', text);
  } else {
    emit('send-message', text);
  }
  
  inputText.value = ''; // 清空输入框
  // 发送后重置输入框高度
  nextTick(() => {
    if (textareaRef.value) {
      textareaRef.value.style.height = 'auto';
    }
  });
};

// 切换深度思考模式
const toggleDeepThinkMode = () => {
  isDeepThinkMode.value = !isDeepThinkMode.value;
  // 关闭其他模式
  if (isDeepThinkMode.value) {
    isDeepResearchMode.value = false;
    isWebSearchMode.value = false;
  }
  // 更新提示文本
  if (isDeepThinkMode.value) {
    placeholderText.value = '输入复杂问题，AI将进行深度思考分析 (Enter 发送, Shift + Enter 换行)...';
  } else {
    placeholderText.value = '输入您的问题或指令 (Enter 发送, Shift + Enter 换行)...';
  }
};

// 切换联网搜索模式
const toggleWebSearchMode = () => {
  isWebSearchMode.value = !isWebSearchMode.value;
  // 关闭其他模式
  if (isWebSearchMode.value) {
    isDeepResearchMode.value = false;
    isDeepThinkMode.value = false;
  }
  // 更新提示文本
  if (isWebSearchMode.value) {
    placeholderText.value = '输入您的问题，AI将联网搜索最新信息 (Enter 发送, Shift + Enter 换行)...';
  } else {
    placeholderText.value = '输入您的问题或指令 (Enter 发送, Shift + Enter 换行)...';
  }
};

// 任务控制方法
const pauseTask = () => {
  taskProgress.value.status = 'paused';
  // 这里应该调用API暂停任务
};

const resumeTask = () => {
  taskProgress.value.status = 'running';
  // 这里应该调用API恢复任务
};

const cancelTask = () => {
  showTaskProgress.value = false;
  taskProgress.value.status = 'cancelled';
  // 这里应该调用API取消任务
  emit('research-error', '任务已取消');
};

// 切换深度研究模式
const toggleResearchMode = () => {
  isDeepResearchMode.value = !isDeepResearchMode.value;
  // 关闭其他模式
  if (isDeepResearchMode.value) {
    isWebSearchMode.value = false;
    isDeepThinkMode.value = false;
  }
  // 更新提示文本
  if (isDeepResearchMode.value) {
    placeholderText.value = '输入研究主题，进行深度分析 (Enter 发送, Shift + Enter 换行)...';
  } else {
    placeholderText.value = '输入您的问题或指令 (Enter 发送, Shift + Enter 换行)...';
  }
};

// (修复) 插入换行符
const insertNewline = () => {
  const textarea = textareaRef.value;
  if (textarea) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = inputText.value;
    inputText.value = text.substring(0, start) + '\n' + text.substring(end);
    // 将光标移动到换行符后
    nextTick(() => {
      textarea.selectionStart = textarea.selectionEnd = start + 1;
    });
  }
};

// (修复) 输入框自动增高
const autoGrowTextarea = () => {
  const textarea = textareaRef.value;
  if (textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = `${textarea.scrollHeight}px`;
  }
};

// 处理研究完成
const handleResearchComplete = (report) => {
  // 清空输入框
  inputText.value = '';
  emit('research-complete', report);
};

// 处理研究错误
const handleResearchError = (error) => {
  emit('research-error', error);
};

const toggleAttachmentMenu = () => {
  isAttachmentMenuOpen.value = !isAttachmentMenuOpen.value;
};
// 文件上传相关状态
const uploadedFiles = ref([])
const showFileUpload = ref(false)

const handleMenuAction = (action) => {
  console.log('菜单项操作:', action);
  isAttachmentMenuOpen.value = false;
  
  if (action === 'upload_files') {
    showFileUpload.value = true;
  } else if (action === 'add_from_drive') {
    // TODO: 实现云盘添加功能
    alert('云盘添加功能正在开发中...');
  } else if (action === 'import_code') {
    // TODO: 实现代码导入功能
    alert('代码导入功能正在开发中...');
  }
};

// 处理文件上传成功
const handleFileUploadSuccess = (data) => {
  uploadedFiles.value = data.files;
  showFileUpload.value = false;
  
  // 如果自动处理文件内容，将处理结果添加到输入框
  if (data.files.length > 0) {
    const processedContent = data.files
      .map(file => `[文件: ${file.filename}] ${file.result?.processed_content || '已上传'}`)
      .join('\n');
    
    if (inputText.value) {
      inputText.value += '\n\n' + processedContent;
    } else {
      inputText.value = processedContent;
    }
    
    nextTick(() => {
      autoGrowTextarea();
    });
  }
};

// 处理文件上传错误
const handleFileUploadError = (error) => {
  console.error('文件上传失败:', error);
  alert(`文件上传失败: ${error.message || error}`);
};
const handleClickOutsideAttachmentMenu = (event) => {
  if (plusMenuContainerRef.value && !plusMenuContainerRef.value.contains(event.target)) {
    isAttachmentMenuOpen.value = false;
  }
};
onMounted(() => {
  document.addEventListener('mousedown', handleClickOutsideAttachmentMenu);
});
onUnmounted(() => {
  document.removeEventListener('mousedown', handleClickOutsideAttachmentMenu);
});
</script>

<style scoped>
.input-box-container {
  background-color: var(--input-bg);
  padding: var(--spacing-sm) var(--spacing-md) var(--spacing-md);
  border-radius: var(--radius-xlarge);
  border: 1px solid var(--input-border);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
  box-shadow: var(--shadow-elev);
  transition: all 0.2s ease;
}

.input-box-container:focus-within {
  border-color: var(--input-focus-border);
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1), var(--shadow-elev);
}
/* (新增) 包裹输入框和发送按钮的容器 */
.main-input-wrapper {
  display: flex;
  align-items: flex-end; /* 底部对齐 */
  gap: 8px;
}
.text-area-wrapper {
  flex-grow: 1;
}
.text-input {
  width: 100%;
  padding: var(--spacing-sm) 0;
  border: none;
  background-color: transparent;
  color: var(--text-primary);
  font-size: 16px;
  font-family: inherit;
  resize: none;
  box-sizing: border-box;
  line-height: 1.47059;
  min-height: 24px;
  max-height: 200px;
  overflow-y: auto;
  letter-spacing: -0.022em;
}

.text-input::placeholder {
  color: var(--text-tertiary);
  opacity: 0.8;
}

.text-input:focus {
  outline: none;
}

.attachments-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 4px;
}
.attach-btn {
  background: none;
  border: none;
  padding: var(--spacing-sm);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s ease;
  position: relative;
}

.attach-btn svg {
  width: 20px;
  height: 20px;
  transition: transform 0.2s ease;
}

.attach-btn:hover {
  color: var(--text-primary);
  background-color: var(--hover-bg);
}

.attach-btn:hover svg {
  transform: scale(1.1);
}

.attach-btn:active {
  background-color: var(--active-bg);
}

.plus-btn svg {
  stroke-width: 2.5;
}

.mic-btn {
  margin-left: auto;
}
.plus-menu-container {
  position: relative;
}
.attachment-menu-popup {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 0;
  background-color: var(--secondary-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.2);
  z-index: 10;
  width: max-content;
  padding: 4px;
}
.attachment-menu-popup ul { list-style: none; padding: 0; margin: 0; }
.attachment-menu-popup li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 15px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-primary);
  border-radius: 6px;
}
.attachment-menu-popup li:hover { background-color: var(--hover-bg); }
.menu-icon { width: 18px; height: 18px; stroke-width: 2; }

/* 深度思考按钮样式 */
.deep-think-btn {
  position: relative;
  transition: all 0.3s ease;
}

.deep-think-btn.active {
  background-color: #9333ea;
  color: white;
  box-shadow: 0 0 10px rgba(147, 51, 234, 0.3);
}

.deep-think-btn.active::after {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(45deg, #9333ea, #7c3aed);
  border-radius: 50%;
  z-index: -1;
  animation: pulse 2s infinite;
}

/* 深度研究按钮样式 */
.research-btn {
  position: relative;
  transition: all 0.3s ease;
}

.research-btn.active {
  background-color: var(--accent-color, #007bff);
  color: white;
  box-shadow: 0 0 10px rgba(0, 123, 255, 0.3);
}

.research-btn.active::after {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(45deg, #007bff, #0056b3);
  border-radius: 50%;
  z-index: -1;
  animation: pulse 2s infinite;
}

.web-search-btn {
  position: relative;
  transition: all 0.3s ease;
}

.web-search-btn.active {
  background-color: #28a745;
  color: white;
  box-shadow: 0 0 10px rgba(40, 167, 69, 0.3);
}

.web-search-btn.active::after {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(45deg, #28a745, #20c997);
  border-radius: 50%;
  z-index: -1;
  animation: pulse 2s infinite;
}

/* 任务进度面板样式 */
.task-progress-panel {
  position: fixed;
  top: 20px;
  right: 20px;
  width: 350px;
  background: var(--primary-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  z-index: 1000;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.progress-info h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.task-status {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 12px;
  background: var(--accent-color);
  color: white;
}

.close-progress {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
}

.close-progress:hover {
  background: var(--hover-bg);
  color: var(--text-primary);
}

.progress-bar-container {
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: var(--border-color);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent-color), #4ade80);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  min-width: 40px;
  text-align: right;
}

.task-steps {
  padding: 0 20px;
  max-height: 200px;
  overflow-y: auto;
}

.task-step {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.task-step:last-child {
  border-bottom: none;
}

.step-icon {
  font-size: 16px;
  margin-top: 2px;
}

.step-content {
  flex: 1;
}

.step-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.step-detail {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.progress-actions {
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
  display: flex;
  gap: 8px;
}

.btn-pause, .btn-resume, .btn-cancel {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-pause {
  background: #f59e0b;
  color: white;
}

.btn-resume {
  background: #10b981;
  color: white;
}

.btn-cancel {
  background: #ef4444;
  color: white;
}

.btn-pause:hover, .btn-resume:hover, .btn-cancel:hover {
  opacity: 0.9;
}

.estimated-time {
  padding: 12px 20px;
  text-align: center;
  font-size: 12px;
  color: var(--text-secondary);
  border-top: 1px solid var(--border-color);
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.7; }
  100% { transform: scale(1); opacity: 1; }
}

/* Apple-style Send Button */
.send-btn {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: var(--gradient-blue);
  color: var(--button-text);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  padding-left: 2px;
  margin-bottom: 2px;
  box-shadow: 0 2px 8px rgba(0, 122, 255, 0.3);
}

.send-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 122, 255, 0.4);
}

.send-btn:active {
  transform: scale(0.95);
}

.send-btn:disabled {
  background: var(--secondary-bg);
  color: var(--text-quaternary);
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

/* 文件上传弹窗样式 */
.file-upload-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.file-upload-modal {
  background-color: var(--primary-bg);
  border-radius: 12px;
  width: 90%;
  max-width: 700px;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--secondary-bg);
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  color: var(--text-secondary);
  transition: all 0.2s;
}

.close-btn:hover {
  color: var(--text-primary);
  background-color: var(--hover-bg);
}

.close-btn svg {
  width: 20px;
  height: 20px;
}

.modal-content {
  padding: 24px;
  max-height: calc(80vh - 100px);
  overflow-y: auto;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .file-upload-modal {
    width: 95%;
    max-height: 90vh;
  }
  
  .modal-header {
    padding: 16px 20px;
  }
  
  .modal-header h3 {
    font-size: 16px;
  }
  
  .modal-content {
    padding: 20px;
    max-height: calc(90vh - 80px);
  }
}

</style>