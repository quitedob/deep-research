<template>
  <div class="home-layout">
    <Sidebar />

    <main class="main-content">
      <ChatContainer
          :current-theme="currentTheme"
          @toggle-theme="$emit('toggle-theme')"
          @send-message-from-container="handleSendMessage"
          @edit-and-send="handleEditAndSend"
          @regenerate="handleRegenerate"
      />
      <div class="input-area">
        <!-- Stop Generation Button -->
        <button v-if="chatStore.isTyping" @click="stopGeneration" class="stop-btn" title="中止生成">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <rect x="6" y="6" width="12" height="12"></rect>
          </svg>
          <span>中止</span>
        </button>
        <InputBox 
          @send-message="handleSendMessage" 
          @send-research="handleSendResearch" 
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { useChatStore } from '@/store';
import Sidebar from '@/components/Sidebar.vue';
import ChatContainer from '@/components/ChatContainer.vue';
import InputBox from '@/components/InputBox.vue';
import { simpleChat, handleAPIError, startResearch, subscribeToResearchEvents, getFinalResearchReport } from '@/services/api.js';

defineProps({ currentTheme: String });
defineEmits(['toggle-theme']);

const chatStore = useChatStore();

/**
 * 处理深度研究请求 - 使用完整的研究流程
 */
const handleSendResearch = async (text) => {
  if (!text.trim()) return;

  // 1) 添加用户消息
  chatStore.addMessage({
    role: 'user',
    content: text,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  });

  // 2) 添加助手占位
  const assistantMessageId = chatStore.addMessage({
    role: 'assistant',
    content: '正在启动深度研究任务…',
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  });

  chatStore.setTypingStatus(true);

  try {
    // 3) 启动研究任务 -> 获取 session_id
    const { session_id } = await startResearch(text, chatStore.activeSessionId);

    // 4) 订阅 SSE 事件，动态更新助手消息
    const es = subscribeToResearchEvents(
      session_id,
      async (evt) => {
        if (evt.event_type === 'agent_thought') {
          // 将中间事件以“思考/进度”形式追加
          const chunk = `\n[进度] ${evt.payload.thought}`;
          chatStore.updateMessageContent({ messageId: assistantMessageId, contentChunk: chunk });
        } else if (evt.event_type === 'final_report') {
          // 最终报告：替换为报告内容
          chatStore.updateMessageContent({ messageId: assistantMessageId, contentChunk: `\n\n${evt.payload.content}` });
          chatStore.setTypingStatus(false);
          if (!chatStore.activeSessionId) {
            chatStore.fetchHistoryList();
          }
        }
      },
      (err) => {
        const msg = handleAPIError(err);
        chatStore.updateMessageContent({ messageId: assistantMessageId, contentChunk: `\n\n[错误] ${msg}` });
        chatStore.setTypingStatus(false);
      }
    );

    // （可选）如需保留以便取消：chatStore.setCurrentRequestController({ abort: () => es.close() });
  } catch (error) {
    const msg = handleAPIError(error);
    chatStore.updateMessageContent({ messageId: assistantMessageId, contentChunk: `\n\n[错误] ${msg}` });
    chatStore.setTypingStatus(false);
  }
};

/**
 * Main function to send a message and handle simple chat response (using Kimi model).
 */
const handleSendMessage = async (text) => {
  if (!text.trim()) return;

  const controller = new AbortController();
  chatStore.setCurrentRequestController(controller);

  const startTime = performance.now();

  chatStore.addMessage({
    role: 'user',
    content: text,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  });

  const assistantMessageId = chatStore.addMessage({
    role: 'assistant',
    content: null,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  });

  chatStore.setTypingStatus(true);

  streamChat(
    text,
    chatStore.activeSessionId,
    (contentChunk) => {
      chatStore.updateMessageContent({ messageId: assistantMessageId, contentChunk });
    },
    () => {
      const endTime = performance.now();
      const duration = ((endTime - startTime) / 1000).toFixed(1);
      chatStore.setMessageDuration(assistantMessageId, duration);
      chatStore.setTypingStatus(false);
      chatStore.setCurrentRequestController(null);
      // After a successful chat, refresh the history list to show the new conversation
      if (!chatStore.activeSessionId) {
        chatStore.fetchHistoryList();
      }
    },
    (error) => {
      const errorMessage = handleAPIError(error);
      chatStore.updateMessageContent({
        messageId: assistantMessageId,
        contentChunk: `**错误:** ${errorMessage}`
      });
      const endTime = performance.now();
      const duration = ((endTime - startTime) / 1000).toFixed(1);
      chatStore.setMessageDuration(assistantMessageId, duration);
      chatStore.setTypingStatus(false);
      chatStore.setCurrentRequestController(null);
    },
    controller.signal
  );
};

/**
 * Handles the 'edit-and-send' event from a MessageItem.
 */
const handleEditAndSend = ({ messageId, newContent }) => {
  const messageIndex = chatStore.messages.findIndex(m => m.id === messageId);
  if (messageIndex === -1) return;

  // Abort any ongoing requests
  chatStore.abortCurrentRequest();
  // Truncate the history from the edited message onwards
  chatStore.replaceMessagesFromIndex(messageIndex);
  // Send the edited content as a new message
  handleSendMessage(newContent);
};

/**
 * Handles the 'regenerate' event from a MessageItem.
 */
const handleRegenerate = (assistantMessage) => {
  const messageIndex = chatStore.messages.findIndex(m => m.id === assistantMessage.id);
  // Ensure there is a user message before the assistant message
  if (messageIndex < 1) return;

  const userMessage = chatStore.messages[messageIndex - 1];
  if (userMessage.role !== 'user') return;

  // Abort any ongoing requests
  chatStore.abortCurrentRequest();
  // Truncate the history, removing the previous user message and the assistant response
  chatStore.replaceMessagesFromIndex(messageIndex - 1);
  // Resend the content of that user message
  handleSendMessage(userMessage.content);
};

/**
 * Stops the current AI response generation.
 */
const stopGeneration = () => {
  chatStore.abortCurrentRequest();
};
</script>

<style scoped>
.home-layout { display: flex; height: 100vh; width: 100vw; }
.main-content { flex-grow: 1; display: flex; flex-direction: column; height: 100%; overflow-y: hidden; background-color: var(--primary-bg); }
.input-area {
  padding: 1rem 1.5rem 1.5rem;
  box-sizing: border-box;
  width: 100%;
  max-width: 940px;
  margin: 0 auto;
  background-color: var(--primary-bg);
  /* (New) Center the stop button above the input box */
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}
.stop-btn {
  padding: 6px 12px;
  border: 1px solid var(--border-color);
  background-color: var(--secondary-bg);
  color: var(--text-primary);
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 14px;
}
.stop-btn:hover { background-color: var(--hover-bg); }
/* Ensure InputBox takes full width inside the flex container */
.input-area > :last-child {
  width: 100%;
}
</style>
