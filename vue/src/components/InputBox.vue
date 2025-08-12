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
      <button class="attach-btn" title="视频">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"></rect><line x1="7" y1="2" x2="7" y2="22"></line><line x1="17" y1="2" x2="17" y2="22"></line><line x1="2" y1="12" x2="22" y2="12"></line><line x1="2" y1="7" x2="7" y2="7"></line><line x1="2" y1="17" x2="7" y2="17"></line><line x1="17" y1="17" x2="22" y2="17"></line><line x1="17" y1="7" x2="22" y2="7"></line></svg>
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
const emit = defineEmits(['send-message', 'send-research', 'research-complete', 'research-error']);
const isDeepResearchMode = ref(false);
const placeholderText = ref('输入您的问题或指令 (Enter 发送, Shift + Enter 换行)...');
const isAttachmentMenuOpen = ref(false);
const plusMenuContainerRef = ref(null);

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
  if (isDeepResearchMode.value) {
    emit('send-research', text);
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

// 切换深度研究模式
const toggleResearchMode = () => {
  isDeepResearchMode.value = !isDeepResearchMode.value;
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
  padding: 8px 12px 12px; /* 调整内边距 */
  border-radius: 20px; /* 调整圆角 */
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 8px;
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
  padding: 8px 0; /* 移除左右padding，由外部容器控制 */
  border: none;
  background-color: transparent;
  color: var(--text-primary);
  font-size: 16px;
  resize: none;
  box-sizing: border-box;
  line-height: 1.5;
  min-height: 24px;
  max-height: 200px;
  overflow-y: auto;
}
.text-input::placeholder { color: var(--text-secondary); opacity: 0.8; }
.text-input:focus { outline: none; }

.attachments-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 4px;
}
.attach-btn {
  background: none;
  border: none;
  padding: 6px;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: color 0.2s, background-color 0.2s;
}
.attach-btn svg { width: 20px; height: 20px; }
.attach-btn:hover { color: var(--text-primary); background-color: var(--hover-bg); }
.plus-btn svg { stroke-width: 2.5; }
.mic-btn { margin-left: auto; }
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

@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.7; }
  100% { transform: scale(1); opacity: 1; }
}

/* (新增) 发送按钮样式 */
.send-btn {
  flex-shrink: 0; /* 防止按钮被压缩 */
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background-color: var(--button-bg);
  color: var(--button-text);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: opacity 0.2s, background-color 0.2s;
  padding-left: 2px; /* 微调图标位置 */
  margin-bottom: 2px; /* 微调对齐 */
}
.send-btn:hover {
  opacity: 0.9;
}
.send-btn:disabled {
  background-color: var(--secondary-bg);
  color: var(--text-secondary);
  cursor: not-allowed;
  opacity: 0.6;
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