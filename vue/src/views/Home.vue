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
          @send-web-search="handleSendWebSearch"
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
import { simpleChat, handleAPIError, conversationAPI, researchAPI } from '@/services/api.js';

defineProps({ currentTheme: String });
defineEmits(['toggle-theme']);

const chatStore = useChatStore();

/**
 * 处理联网搜索请求
 */
const handleSendWebSearch = async (text) => {
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
    content: '正在联网搜索最新信息...',
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  });

  chatStore.setTypingStatus(true);

  try {
    // 3) 使用当前选择的模型进行联网搜索
    const currentModel = chatStore.currentModel;

    // 构造联网搜索请求
    const searchMessage = {
      message: text,
      model: currentModel,
      session_id: chatStore.activeSessionId,
      web_search: true  // 启用联网搜索
    };

    const response = await simpleChat(searchMessage);

    // 4) 更新助手消息
    chatStore.updateMessageContent({ messageId: assistantMessageId, contentChunk: response });

    chatStore.setTypingStatus(false);
    if (!chatStore.activeSessionId) {
      chatStore.fetchHistoryList();
    }
  } catch (error) {
    const msg = handleAPIError(error);
    chatStore.updateMessageContent({ messageId: assistantMessageId, contentChunk: `\n\n[错误] ${msg}` });
    chatStore.setTypingStatus(false);
  }
};

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
    const response = await researchAPI.startResearch(text, chatStore.activeSessionId);
    const session_id = response.session_id;

    // 4) 获取研究流进度
    const streamResponse = await researchAPI.getStream(session_id);
    const reader = streamResponse.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n').filter(line => line.trim());

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));

            if (data.status === 'completed') {
              // 研究完成，获取最终报告
              const report = await researchAPI.getReport(session_id);
              chatStore.updateMessageContent({
                messageId: assistantMessageId,
                contentChunk: `\n\n# 研究报告\n\n${report.content || '报告生成失败'}`
              });
              chatStore.setTypingStatus(false);
              if (!chatStore.activeSessionId) {
                chatStore.fetchHistoryList();
              }
              break;
            } else if (data.status === 'failed') {
              // 研究失败
              const errorMsg = data.error || '研究过程中出现错误';
              chatStore.updateMessageContent({
                messageId: assistantMessageId,
                contentChunk: `\n\n[错误] ${errorMsg}`
              });
              chatStore.setTypingStatus(false);
              break;
            } else if (data.message) {
              // 更新进度消息
              const progressChunk = `\n[进度] ${data.message}`;
              chatStore.updateMessageContent({
                messageId: assistantMessageId,
                contentChunk: progressChunk
              });
            }
          } catch (e) {
            console.warn('Failed to parse SSE data:', line);
          }
        }
      }
    }
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

  try {
    // 使用后端API进行对话
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: text,
        session_id: chatStore.activeSessionId,
        stream: true
      }),
      signal: controller.signal
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n').filter(line => line.trim());

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.content) {
              chatStore.updateMessageContent({
                messageId: assistantMessageId,
                contentChunk: data.content
              });
            }
          } catch (e) {
            console.warn('Failed to parse SSE data:', line);
          }
        }
      }
    }

    // 完成处理
    const endTime = performance.now();
    const duration = ((endTime - startTime) / 1000).toFixed(1);
    chatStore.setMessageDuration(assistantMessageId, duration);
    chatStore.setTypingStatus(false);
    chatStore.setCurrentRequestController(null);

    // 刷新历史记录
    if (!chatStore.activeSessionId) {
      chatStore.fetchHistoryList();
    }

  } catch (error) {
    if (error.name === 'AbortError') {
      // 请求被中止
      chatStore.setTypingStatus(false);
      chatStore.setCurrentRequestController(null);
      return;
    }

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
  }
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
.home-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
}
.main-content {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow-y: hidden;
  background: transparent;
  position: relative;
}
.input-area {
  padding: 1.5rem;
  box-sizing: border-box;
  width: 100%;
  max-width: 1000px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  border-radius: 16px 16px 0 0;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-bottom: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.stop-btn {
  padding: 8px 16px;
  border: none;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  border-radius: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
  transition: all 0.3s ease;
}
.stop-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(239, 68, 68, 0.4);
}
/* Ensure InputBox takes full width inside the flex container */
.input-area > :last-child {
  width: 100%;
}
</style>
