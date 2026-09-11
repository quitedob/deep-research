<template>
  <div class="home-layout">
    <Sidebar />

    <main class="main-content">
      <div class="chat-interface">
        <ChatContainer
            :current-theme="currentTheme"
            @toggle-theme="$emit('toggle-theme')"
            @send-message-from-container="handleSendMessage"
            @edit-and-send="handleEditAndSend"
            @regenerate="handleRegenerate"
        />

        <!-- Input Area with Apple-style Design -->
        <div class="input-area-wrapper">
          <!-- Stop Generation Button -->
          <div v-if="chatStore.isTyping" class="generation-controls">
            <button @click="stopGeneration" class="stop-btn" title="中止生成" aria-label="中止生成">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="6" width="12" height="12"></rect>
              </svg>
              <span>中止生成</span>
            </button>
          </div>

          <div class="input-container">
            <InputBox
              :disabled="chatStore.isTyping"
              @send-message="handleSendMessage"
              @send-research="handleSendResearch"
              @send-web-search="handleSendWebSearch"
              @send-deep-think="handleSendDeepThink"
            />
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { onUnmounted } from 'vue';
import { useChatStore } from '@/store';
import Sidebar from '@/components/Sidebar.vue';
import ChatContainer from '@/components/ChatContainer.vue';
import InputBox from '@/components/InputBox.vue';
import { chatAPI, researchAPI } from '@/api/index';
import { consumeSSE } from '@/utils/sse.js';
import { notificationManager as notifications } from '@/composables/useNotifications.js';

defineProps({ currentTheme: String });
defineEmits(['toggle-theme']);
const chatStore = useChatStore();
const getProviderFromModel = (model) => model.startsWith('glm') ? 'zhipu' : model.startsWith('deepseek') ? 'deepseek' : 'ollama';

async function ensureSession(text, model, controller) {
  let id = chatStore.activeSessionId;
  if (!id) {
    const session = await chatAPI.createSession({
      title: text.slice(0, 50), llm_provider: getProviderFromModel(model), model_name: model
    });
    controller.signal.throwIfAborted();
    id = session.id;
    chatStore.activeSessionId = id;
  } else {
    await chatAPI.updateSession(id, { llm_provider: getProviderFromModel(model), model_name: model });
    controller.signal.throwIfAborted();
  }
  return id;
}

async function consumeChat(text, id, controller) {
  const response = await chatAPI.chatStream({ session_id: chatStore.activeSessionId, message: text, stream: true }, { signal: controller.signal });
  let completed = false;
  await consumeSSE(response, data => {
    controller.signal.throwIfAborted();
    if (data.type === 'error' || data.error) throw new Error(data.error || '生成失败，请重试');
    if (data.content) chatStore.updateMessageContent({ messageId: id, contentChunk: data.content });
    if (data.type === 'message' && data.message) {
      const message = chatStore.messages.find(item => item.id === id);
      if (message) Object.assign(message, data.message);
    }
    if (data.type === 'done') { completed = true; return false; }
  });
  if (!completed) throw new Error('回复连接提前结束，请重试');
}

async function consumeResearch(text, id, controller) {
  const model = chatStore.currentModel;
  const research = await researchAPI.startResearch({
    query: text, research_type: 'comprehensive', sources: ['web', 'academic'],
    include_images: false, llm_config: { provider: getProviderFromModel(model), model_name: model }
  }, { signal: controller.signal });
  controller.signal.throwIfAborted();
  if (!research.success) throw new Error(research.error || '启动研究失败');
  chatStore.setResearchMode(true, research.session_id);
  const timeout = setTimeout(() => controller.abort(new DOMException('研究超过30分钟，请稍后查看历史记录', 'TimeoutError')), 30 * 60 * 1000);
  let completed = false;
  try {
    const response = await researchAPI.getStream(research.session_id, { signal: controller.signal });
    await consumeSSE(response, event => {
      controller.signal.throwIfAborted();
      if (['failed', 'error', 'interrupted', 'not_found'].includes(event.type)) {
        throw new Error(event.error || event.message || event.reason || '研究已中断');
      }
      if (event.type === 'completed') {
        const data = event.data || event;
        const report = data.report_text || data.report || event.report;
        if (typeof report !== 'string' || !report.trim()) throw new Error('研究完成，但报告内容为空');
        const sessionId = data.chat_session_id;
        chatStore.activeSessionId = sessionId || null;
        chatStore.updateMessageContent({ messageId: id, contentChunk: report,
          metadata: { ...data.metadata, type: 'research', session_id: research.session_id } });
        completed = true;
        return false;
      }
    });
    if (!completed) throw new Error('研究连接提前结束，请在历史记录中查看或重试');
  } finally {
    clearTimeout(timeout);
  }
}

async function sendMessage(text, mode = 'chat', branch = null) {
  if (!text.trim() || chatStore.isTyping) return;
  const controller = new AbortController();
  chatStore.setCurrentRequestController(controller);
  let id;
  chatStore.setTypingStatus(true);
  const started = performance.now();
  try {
    if (branch) {
      const session = await chatAPI.branchSession(chatStore.activeSessionId, branch.messageId, { signal: controller.signal });
      controller.signal.throwIfAborted();
      const prefix = await chatAPI.getMessages(session.id, null, { signal: controller.signal });
      controller.signal.throwIfAborted();
      chatStore.messages = prefix;
      chatStore.activeSessionId = session.id;
    }
    chatStore.addMessage({ role: 'user', content: text });
    id = chatStore.addMessage({ role: 'assistant', content: null,
      metadata: mode === 'research' ? { type: 'research', evidence: [] } : undefined });
    if (mode === 'research') {
      await consumeResearch(text, id, controller);
    } else {
      const model = mode === 'think'
        ? (chatStore.currentModel.startsWith('glm') ? 'glm-4.6' : 'deepseek-reasoner') : chatStore.currentModel;
      const sessionId = await ensureSession(text, model, controller);
      if (mode === 'chat') await consumeChat(text, id, controller);
      else {
        const api = mode === 'web' ? chatAPI.webSearch : chatAPI.chat;
        const response = await api({ session_id: sessionId, message: text, stream: false }, { signal: controller.signal });
        controller.signal.throwIfAborted();
        const content = response.message?.content;
        if (typeof content !== 'string') throw new Error('服务器未返回有效的回复');
        chatStore.updateMessageContent({ messageId: id, contentChunk: content });
      }
    }
    controller.signal.throwIfAborted();
    // Reload persisted IDs so feedback/report actions refer to real server messages.
    if (chatStore.activeSessionId) {
      const messages = await chatAPI.getMessages(chatStore.activeSessionId);
      controller.signal.throwIfAborted();
      if (messages.length) chatStore.messages = messages;
    }
    await chatStore.fetchHistoryList();
  } catch (error) {
    if (error.name !== 'AbortError') {
      chatStore.updateMessageContent({ messageId: id, contentChunk: `\n\n错误：${error.message}` });
      notifications.error(error.message || '请求失败，请重试');
    }
  } finally {
    if (chatStore.currentRequestController === controller) {
      chatStore.setMessageDuration(id, ((performance.now() - started) / 1000).toFixed(1));
      chatStore.setTypingStatus(false);
      chatStore.setResearchMode(false);
      chatStore.setCurrentRequestController(null);
    }
  }
}
const handleSendMessage = text => sendMessage(text);
const handleSendDeepThink = text => sendMessage(text, 'think');
const handleSendWebSearch = text => sendMessage(text, 'web');
const handleSendResearch = text => sendMessage(text, 'research');
const handleEditAndSend = ({ messageId, newContent }) => {
  if (chatStore.isTyping || !Number.isSafeInteger(messageId)) return;
  const index = chatStore.messages.findIndex(message => message.id === messageId);
  if (index < 0) return;
  chatStore.abortCurrentRequest();
  sendMessage(newContent, 'chat', { messageId });
};
const handleRegenerate = message => {
  if (chatStore.isTyping || !Number.isSafeInteger(message.id)) return;
  const index = chatStore.messages.findIndex(item => item.id === message.id);
  const previous = chatStore.messages[index - 1];
  if (previous?.role !== 'user') return;
  chatStore.abortCurrentRequest();
  sendMessage(previous.content, 'chat', { messageId: previous.id });
};
const stopGeneration = async () => {
  const researchId = chatStore.researchSessionId;
  chatStore.abortCurrentRequest();
  chatStore.setResearchMode(false);
  if (researchId) {
    try { await researchAPI.interrupt(researchId); }
    catch (error) { notifications.error(`中断研究失败：${error.message}`); }
  }
};
onUnmounted(() => chatStore.abortCurrentRequest());
</script>

<style scoped>
.home-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  background: var(--primary-bg);
}

.main-content {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow-y: hidden;
  background: var(--primary-bg);
  position: relative;
}

.chat-interface {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
}

.input-area-wrapper {
  padding: var(--spacing-lg);
  box-sizing: border-box;
  width: 100%;
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.generation-controls {
  display: flex;
  justify-content: center;
  animation: slideUp 0.3s ease;
}

.stop-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border: none;
  background: var(--accent-red);
  color: white;
  border-radius: var(--radius-large);
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(255, 59, 48, 0.3);
  transition: all 0.2s ease;
}

.stop-btn:hover {
  background: #ff2d55;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(255, 59, 48, 0.4);
}

.stop-btn:active {
  transform: translateY(0);
}

.input-container {
  width: 100%;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Responsive Design */
@media (max-width: 768px) {
  .input-area-wrapper {
    padding: var(--spacing-md);
  }
}

@media (max-width: 480px) {
  .input-area-wrapper {
    padding: var(--spacing-sm);
  }
}
</style>
