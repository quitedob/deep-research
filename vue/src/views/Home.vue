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
            <button @click="stopGeneration" class="stop-btn" title="中止生成">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="6" width="12" height="12"></rect>
              </svg>
              <span>中止生成</span>
            </button>
          </div>

          <div class="input-container">
            <InputBox
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
import { useChatStore } from '@/store';
import Sidebar from '@/components/Sidebar.vue';
import ChatContainer from '@/components/ChatContainer.vue';
import InputBox from '@/components/InputBox.vue';
import { chatAPI } from '@/api/index';
import { handleAPIError } from '@/services/api.js';

defineProps({ currentTheme: String });
defineEmits(['toggle-theme']);

const chatStore = useChatStore();

/**
 * 根据模型名称获取提供商
 */
const getProviderFromModel = (modelName) => {
  if (!modelName) return 'deepseek';
  
  if (modelName.startsWith('deepseek')) {
    return 'deepseek';
  } else if (modelName.startsWith('glm')) {
    return 'zhipu';
  }
  
  // 默认返回 deepseek
  return 'deepseek';
};

/**
 * 处理深度思考请求 - 使用 deepseek-reasoner 或 glm-4.6
 */
const handleSendDeepThink = async (text) => {
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
    content: '正在进行深度思考分析...',
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  });

  chatStore.setTypingStatus(true);

  try {
    // 根据当前模型选择深度思考模型
    const currentModel = chatStore.currentModel;
    let deepThinkModel = 'deepseek-reasoner'; // 默认使用 deepseek-reasoner
    let provider = 'deepseek';
    
    if (currentModel && currentModel.startsWith('glm')) {
      deepThinkModel = 'glm-4.6';
      provider = 'zhipu';
    }

    // 如果没有活动会话，先创建一个
    let sessionId = chatStore.activeSessionId;
    if (!sessionId) {
      const newSession = await chatAPI.createSession({
        title: text.substring(0, 50) + (text.length > 50 ? '...' : ''),
        llm_provider: provider,
        model_name: deepThinkModel
      });
      sessionId = newSession.id;
      chatStore.activeSessionId = sessionId;
      await chatStore.fetchHistoryList();
    }

    // 使用深度思考模型进行对话
    const response = await chatAPI.chat({
      session_id: sessionId,
      message: text,
      stream: false
    });

    // 更新助手消息
    chatStore.updateMessageContent({ 
      messageId: assistantMessageId, 
      contentChunk: response.content || response.message 
    });

    chatStore.setTypingStatus(false);
    if (!chatStore.activeSessionId) {
      chatStore.fetchHistoryList();
    }
  } catch (error) {
    const msg = handleAPIError(error);
    chatStore.updateMessageContent({ 
      messageId: assistantMessageId, 
      contentChunk: `\n\n[错误] ${msg}` 
    });
    chatStore.setTypingStatus(false);
  }
};

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

  // 2) 添加助手占位（使用 null 内容触发动画）
  const assistantMessageId = chatStore.addMessage({
    role: 'assistant',
    content: null, // null 会触发 MessageItem 的 thinking 动画
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  });

  chatStore.setTypingStatus(true);

  try {
    // 如果没有活动会话，先创建一个
    let sessionId = chatStore.activeSessionId;
    if (!sessionId) {
      const modelName = chatStore.currentModel || 'glm-4-plus';
      const newSession = await chatAPI.createSession({
        title: text.substring(0, 50) + (text.length > 50 ? '...' : ''),
        llm_provider: getProviderFromModel(modelName),
        model_name: modelName
      });
      sessionId = newSession.id;
      chatStore.activeSessionId = sessionId;
      await chatStore.fetchHistoryList();
    }

    // 使用联网搜索API（后台执行所有步骤）
    const response = await fetch('http://localhost:8000/api/chat/chat/web-search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')}`
      },
      body: JSON.stringify({
        session_id: sessionId,
        message: text,
        stream: false
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    const result = await response.json();

    // 搜索完成，更新为最终答案
    chatStore.updateMessageContent({ 
      messageId: assistantMessageId, 
      contentChunk: result.message.content 
    });

    chatStore.setTypingStatus(false);
    if (!chatStore.activeSessionId) {
      chatStore.fetchHistoryList();
    }
  } catch (error) {
    const msg = handleAPIError(error);
    chatStore.updateMessageContent({ 
      messageId: assistantMessageId, 
      contentChunk: `联网搜索失败: ${msg}` 
    });
    chatStore.setTypingStatus(false);
  }
};

/**
 * ✅ 处理深度研究请求 - 使用 SSE 接收后端推送，不再轮询
 */
const handleSendResearch = async (text) => {
  if (!text.trim()) return;

  const { researchAPI } = await import('@/api/index');

  chatStore.addMessage({
    role: 'user',
    content: text,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  });

  const assistantMessageId = chatStore.addMessage({
    role: 'assistant',
    content: null,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    metadata: {
      type: 'research',
      evidence: [],
      tools_used: []
    }
  });

  chatStore.setTypingStatus(true);

  try {
    const modelName = chatStore.currentModel || 'glm-4-plus';
    const provider = getProviderFromModel(modelName);

    const researchResponse = await researchAPI.startResearch({
      query: text,
      research_type: 'comprehensive',
      sources: ['web', 'academic'],
      include_images: false,
      llm_config: {
        provider: provider,
        model_name: modelName
      }
    });

    if (researchResponse.success) {
      chatStore.setResearchMode(true, researchResponse.session_id);

      // ✅ 使用 SSE 监听后端推送，不再轮询！
      const eventSource = new EventSource(
        `http://localhost:8000/api/research/stream/${researchResponse.session_id}`
      );

      eventSource.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('收到 SSE 事件:', data.type, '完整数据:', data);

          if (data.type === 'connected') {
            console.log('✓ SSE 连接成功，等待后端推送...');
          } 
          else if (data.type === 'status_update') {
            const status = data.status;
            console.log('状态更新:', status);
            
            if (status === 'in_progress') {
              const progress = data.data?.progress || {};
              
              let progressMsg = '🔍 正在进行深度研究...\n\n';
              
              if (progress.tools_used && progress.tools_used.length > 0) {
                progressMsg += `**使用的工具**: ${progress.tools_used.join(', ')}\n`;
              }
              
              if (progress.findings_count > 0) {
                progressMsg += `**发现数量**: ${progress.findings_count}\n`;
              }
              
              progressMsg += '\n*研究进行中，请稍候...*';
              
              chatStore.updateMessageContent({
                messageId: assistantMessageId,
                contentChunk: progressMsg,
                keepThinking: true
              });
            }
            // ✅ 处理 status_update 中的 completed 状态
            else if (status === 'completed') {
              console.log('✓ 通过 status_update 收到完成通知');
              // 不关闭连接，等待 completed 事件推送完整报告
            }
          }
          else if (data.type === 'completed') {
            console.log('✓ 研究完成，收到最终报告');
            eventSource.close();
            
            // ✅ 直接使用后端生成的完整报告文本
            const responseData = data.data;
            const reportText = responseData?.report_text || '研究完成，但报告为空。';
            const metadata = responseData?.metadata || { type: 'research', session_id: responseData?.session_id };
            
            console.log('报告长度:', reportText.length, '字符');
            console.log('证据数量:', metadata.evidence?.length || 0);
            
            chatStore.updateMessageContent({
              messageId: assistantMessageId,
              contentChunk: reportText,
              metadata: metadata  // ✅ 传递完整的 metadata（包含证据链）
            });
            
            chatStore.setTypingStatus(false);
            chatStore.setResearchMode(false, null);
          }
          else if (data.type === 'failed' || data.type === 'error') {
            console.error('✗ 研究失败:', data.error);
            eventSource.close();
            
            chatStore.updateMessageContent({
              messageId: assistantMessageId,
              contentChunk: `深度研究失败: ${data.error || '未知错误'}`
            });
            chatStore.setTypingStatus(false);
            chatStore.setResearchMode(false, null);
          }
        } catch (error) {
          console.error('处理 SSE 事件失败:', error);
        }
      };

      eventSource.onerror = (error) => {
        console.error('SSE 连接错误:', error);
        eventSource.close();
        
        chatStore.updateMessageContent({
          messageId: assistantMessageId,
          contentChunk: '深度研究连接中断，请重试'
        });
        chatStore.setTypingStatus(false);
        chatStore.setResearchMode(false, null);
      };

      // ✅ 增加超时时间到 30 分钟，研究可能需要较长时间
      const timeoutId = setTimeout(() => {
        console.warn('⚠️ 研究超时（30分钟）');
        if (eventSource.readyState !== EventSource.CLOSED) {
          eventSource.close();
          if (chatStore.isTyping) {
            chatStore.updateMessageContent({
              messageId: assistantMessageId,
              contentChunk: '深度研究超时（30分钟），请稍后重试'
            });
            chatStore.setTypingStatus(false);
            chatStore.setResearchMode(false, null);
          }
        }
      }, 18000000); // 300分钟

      // ✅ 在连接关闭时清除超时
      const originalClose = eventSource.close.bind(eventSource);
      eventSource.close = () => {
        clearTimeout(timeoutId);
        originalClose();
      };
    } else {
      throw new Error(researchResponse.error || '启动研究失败');
    }
    
  } catch (error) {
    const msg = handleAPIError(error);
    chatStore.updateMessageContent({ 
      messageId: assistantMessageId, 
      contentChunk: `深度研究失败: ${msg}` 
    });
    chatStore.setTypingStatus(false);
    chatStore.setResearchMode(false, null);
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
    // 获取认证token
    const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
    if (!token) {
      throw new Error('请先登录');
    }

    // 如果没有活动会话，先创建一个
    let sessionId = chatStore.activeSessionId;
    if (!sessionId) {
      const modelName = chatStore.currentModel || 'deepseek-chat';
      const newSession = await chatAPI.createSession({
        title: text.substring(0, 50) + (text.length > 50 ? '...' : ''),
        llm_provider: getProviderFromModel(modelName),
        model_name: modelName
      });
      sessionId = newSession.id;
      chatStore.activeSessionId = sessionId;
      // 刷新历史列表
      await chatStore.fetchHistoryList();
    }

    // 使用后端API进行对话
    const response = await fetch('http://localhost:8000/api/chat/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        session_id: sessionId,
        message: text,
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
