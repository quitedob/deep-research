<template>
  <div :class="['message-wrapper', message.role]">
    <div class="avatar">
      <span v-if="message.role === 'user'">U</span>
      <span v-else>AI</span>
    </div>
    <div class="content-container">
      <div :class="['message-bubble', { 'thinking': isThinking }]">
        <!-- Editing Mode -->
        <div v-if="isEditing" class="edit-area">
          <textarea
              v-model="editedContent"
              ref="textareaRef"
              class="edit-textarea"
              rows="3"
              @keydown.enter.exact.prevent="handleSendEdit"
              @keydown.esc.prevent="cancelEdit"
          ></textarea>
        </div>

        <!-- Thinking Indicator -->
        <div v-else-if="isThinking" class="typing-indicator">
          <div class="typing-text">AI 正在思考中</div>
          <div class="typing-dots">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
          </div>
        </div>

        <!-- Standard Content Display -->
        <div v-else class="message-text" v-html="formattedContent"></div>
      </div>
      <div class="message-actions" v-if="!isThinking">
        <!-- Timer Display -->
        <div v-if="message.role === 'assistant' && message.duration" class="timer-display">
          <span>{{ message.duration }}s</span>
        </div>

        <button @click="copyContent" title="复制">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
        </button>
        <template v-if="message.role === 'user'">
          <button v-if="!isEditing" @click="startEdit" title="编辑">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
          </button>
          <button v-if="isEditing" @click="handleSendEdit" title="发送修改 (Enter)">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
          </button>
        </template>
        <button v-if="message.role === 'assistant'" @click="emit('regenerate', message)" title="重新生成">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, nextTick } from 'vue';
import markdownit from 'markdown-it';
import hljs from 'highlight.js';

const props = defineProps({ message: { type: Object, required: true } });
const emit = defineEmits(['edit-and-send', 'regenerate']);

const isEditing = ref(false);
const editedContent = ref('');
const textareaRef = ref(null);

const isThinking = computed(() => props.message.content === null);

const startEdit = () => {
  isEditing.value = true;
  editedContent.value = props.message.content;
  nextTick(() => {
    textareaRef.value?.focus();
    textareaRef.value?.select();
  });
};

const cancelEdit = () => { isEditing.value = false; };

const handleSendEdit = () => {
  if (editedContent.value.trim() && editedContent.value.trim() !== props.message.content.trim()) {
    emit('edit-and-send', { messageId: props.message.id, newContent: editedContent.value });
  }
  isEditing.value = false;
};

const md = markdownit({
  html: true, linkify: true, typographer: true,
  highlight: (str, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs"><code>${hljs.highlight(str, { language: lang, ignoreIllegals: true }).value}</code></pre>`;
      } catch (__) {}
    }
    return `<pre class="hljs"><code>${md.utils.escapeHtml(str)}</code></pre>`;
  }
});

const formattedContent = computed(() => md.render(props.message.content || ''));

const copyContent = async () => {
  try {
    await navigator.clipboard.writeText(props.message.content);
  } catch (err) {
    console.error('Failed to copy: ', err);
  }
};
</script>

<style scoped>
/* --- Base Styles --- */
.message-wrapper { display: flex; gap: 15px; width: 100%; animation: fadeIn 0.3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.avatar { width: 40px; height: 40px; border-radius: 50%; flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white; }
.user .avatar { background: #71717a; }
.assistant .avatar { background: #2563eb; }
.content-container { display: flex; flex-direction: column; max-width: 90%; }
.message-bubble { padding: 12px 18px; border-radius: 18px; line-height: 1.7; color: var(--text-primary); word-wrap: break-word; font-size: 15px; }
.assistant .message-bubble { background-color: var(--secondary-bg); border: 1px solid var(--border-color); border-top-left-radius: 4px; }
.user .message-bubble { background-color: #3b82f6; color: white; border-top-right-radius: 4px; }
.user { flex-direction: row-reverse; }
.user .content-container { align-items: flex-end; }
.user .message-actions { justify-content: flex-end; }

/* --- Actions Bar --- */
.message-actions {
  display: flex;
  align-items: center; /* Vertically align items */
  gap: 8px;
  margin-top: 8px;
  visibility: hidden;
  opacity: 0;
  transition: visibility 0s, opacity 0.2s linear;
  height: 24px; /* Give a fixed height */
}
.message-wrapper:hover .message-actions { visibility: visible; opacity: 1; }
.message-actions button { background: none; border: none; color: var(--text-secondary); cursor: pointer; padding: 4px; border-radius: 4px; display: flex; align-items: center; }
.message-actions button:hover { background-color: var(--hover-bg); color: var(--text-primary); }
.user .message-actions button { color: #a0bdf6; }
.user .message-actions button:hover { background-color: rgba(255, 255, 255, 0.1); color: white; }

/* --- Timer Display --- */
.timer-display {
  font-size: 12px;
  color: var(--text-secondary);
  padding: 4px 8px;
  background-color: var(--secondary-bg);
  border-radius: 4px;
  margin-right: auto; /* Push other buttons to the right */
}

/* --- Edit Mode Styles --- */
.edit-area { padding: 0; margin: 0; }
.edit-textarea { width: 100%; box-sizing: border-box; border: 1px solid #60a5fa; border-radius: 8px; padding: 10px; font-family: inherit; font-size: 15px; line-height: 1.6; background-color: #1e293b; color: white; resize: vertical; min-height: 60px; }
.edit-textarea:focus { outline: none; box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.5); }
.user .message-bubble { padding: 2px; }

/* --- Thinking Indicator Styles --- */
.message-bubble.thinking { background-color: #1e3a8a; color: #e0e7ff; border: 1px solid #1d4ed8; }
.typing-indicator { display: flex; align-items: center; gap: 8px; }
.typing-dots { display: flex; gap: 4px; align-items: center; }
.typing-dot { width: 8px; height: 8px; background: #93c5fd; border-radius: 50%; animation: typing 1.4s infinite ease-in-out both; }
.typing-dot:nth-child(1) { animation-delay: -0.32s; }
.typing-dot:nth-child(2) { animation-delay: -0.16s; }
.typing-dot:nth-child(3) { animation-delay: 0s; }
@keyframes typing { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1.0); } }
</style>
<style>
/* Global styles for rendered markdown remain the same */
.message-text { white-space: pre-wrap; }
.message-text pre { background: #1e1e1e; color: #d4d4d4; padding: 1em; border-radius: 8px; overflow-x: auto; margin: 1em 0; font-family: 'Courier New', Courier, monospace; font-size: 14px; }
.user .message-text pre { background: #1e293b; }
.message-text pre code { background: transparent; padding: 0; }
.message-text p code, .message-text li code { background: rgba(128, 128, 128, 0.15); padding: 2px 6px; border-radius: 4px; font-family: 'Courier New', Courier, monospace; }
.user .message-text p code, .user .message-text li code { background: rgba(255, 255, 255, 0.2); }
.message-text strong { font-weight: 600; }
.message-text ul, .message-text ol { padding-left: 20px; }
.message-text blockquote { border-left: 3px solid var(--border-color); padding-left: 15px; margin-left: 0; color: var(--text-secondary); }
.user .message-text a { color: #a0bdf6; }
.user .message-text a:hover { color: #c4d7f8; }
</style>
