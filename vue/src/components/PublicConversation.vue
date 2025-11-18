<template>
  <div class="public-conversation-container">
    <!-- Header -->
    <header class="public-header">
      <div class="header-content">
        <div class="header-info">
          <h1 class="conversation-title">{{ conversationData?.title || '无标题对话' }}</h1>
          <p class="conversation-description" v-if="conversationData?.description">
            {{ conversationData.description }}
          </p>
          <div class="conversation-meta">
            <span class="meta-item">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
              </svg>
              创建于 {{ formatDate(conversationData?.created_at) }}
            </span>
            <span class="meta-item">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
              </svg>
              访问次数: {{ conversationData?.view_count || 0 }}
            </span>
            <span class="meta-item">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
              {{ messageCount }} 条消息
            </span>
          </div>
        </div>
        <div class="header-actions">
          <button @click="shareAgain" class="share-again-btn">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"></path>
              <polyline points="16 6 12 2 8 6"></polyline>
              <line x1="12" y1="2" x2="12" y2="15"></line>
            </svg>
            分享
          </button>
          <a href="/" class="back-to-app-btn">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 18l6-6-6-6"></path>
            </svg>
            返回应用
          </a>
        </div>
      </div>
    </header>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>加载对话中...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <div class="error-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="15" y1="9" x2="9" y2="15"></line>
          <line x1="9" y1="9" x2="15" y2="15"></line>
        </svg>
      </div>
      <h2>无法加载对话</h2>
      <p>{{ error }}</p>
      <a href="/" class="back-btn">返回首页</a>
    </div>

    <!-- Conversation Content -->
    <main v-else-if="conversationData" class="conversation-content">
      <div class="messages-container">
        <div
          v-for="(message, index) in conversationData.messages"
          :key="index"
          :class="['message-wrapper', message.role]"
        >
          <div class="avatar">
            <span v-if="message.role === 'user'">U</span>
            <span v-else>AI</span>
          </div>
          <div class="content-container">
            <div class="message-bubble">
              <div class="message-text" v-html="formatMessageContent(message.content)"></div>
            </div>
            <div class="message-timestamp" v-if="message.timestamp">
              {{ formatMessageTime(message.timestamp) }}
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Footer -->
    <footer class="public-footer">
      <div class="footer-content">
        <p>
          由
          <a href="/" target="_blank" class="app-link">Deep Research Platform</a>
          提供支持
        </p>
        <p class="expiry-info" v-if="conversationData?.expires_at">
          此分享链接将于 {{ formatDate(conversationData.expires_at) }} 过期
        </p>
      </div>
    </footer>

    <!-- Share Success Toast -->
    <div v-if="showShareToast" class="share-toast">
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="20 6 9 17 4 12"></polyline>
      </svg>
      <span>分享链接已复制到剪贴板</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import markdownit from 'markdown-it';

const route = useRoute();
const loading = ref(true);
const error = ref(null);
const conversationData = ref(null);
const showShareToast = ref(false);

// 获取分享ID
const shareId = computed(() => route.params.shareId);

// 计算消息数量
const messageCount = computed(() => {
  return conversationData.value?.messages?.length || 0;
});

// 格式化消息内容
const formatMessageContent = (content) => {
  if (!content) return '';

  const md = markdownit({
    html: true,
    linkify: true,
    typographer: true,
    highlight: (str, lang) => {
      if (!lang) return '';
      try {
        return `<pre class="hljs"><code>${str}</code></pre>`;
      } catch (__) {
        return `<pre class="hljs"><code>${str}</code></pre>`;
      }
    }
  });

  return md.render(content);
};

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '未知';
  try {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (error) {
    return '格式错误';
  }
};

// 格式化消息时间
const formatMessageTime = (timestamp) => {
  if (!timestamp) return '';
  try {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (error) {
    return '';
  }
};

// 加载公开对话
const loadPublicConversation = async () => {
  try {
    loading.value = true;
    error.value = null;

    const response = await fetch(`/api/public/conversation/${shareId.value}`);

    if (!response.ok) {
      if (response.status === 404) {
        error.value = '分享不存在或已被删除';
      } else if (response.status === 403) {
        error.value = '分享链接已过期或已失效';
      } else {
        error.value = '加载对话时发生错误';
      }
      return;
    }

    const data = await response.json();
    conversationData.value = data;

  } catch (err) {
    console.error('加载公开对话失败:', err);
    error.value = '网络连接错误，请稍后重试';
  } finally {
    loading.value = false;
  }
};

// 再次分享
const shareAgain = async () => {
  try {
    const shareUrl = window.location.href;
    await navigator.clipboard.writeText(shareUrl);

    // 显示成功提示
    showShareToast.value = true;
    setTimeout(() => {
      showShareToast.value = false;
    }, 3000);

    console.log('分享链接已复制到剪贴板');
  } catch (err) {
    console.error('复制失败:', err);
    alert('复制失败，请手动复制链接');
  }
};

// 页面加载时获取对话数据
onMounted(() => {
  if (shareId.value) {
    loadPublicConversation();
  } else {
    error.value = '无效的分享链接';
    loading.value = false;
  }
});
</script>

<style scoped>
/* --- Container --- */
.public-conversation-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
}

/* --- Header --- */
.public-header {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding: 20px 0;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
}

.header-info {
  flex: 1;
}

.conversation-title {
  margin: 0 0 8px 0;
  color: white;
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

.conversation-description {
  margin: 0 0 16px 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
  line-height: 1.5;
}

.conversation-meta {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
}

.meta-item svg {
  flex-shrink: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
  flex-shrink: 0;
}

.share-again-btn,
.back-to-app-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s ease;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.share-again-btn {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  cursor: pointer;
}

.share-again-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

.back-to-app-btn {
  background: rgba(255, 255, 255, 0.9);
  color: #667eea;
}

.back-to-app-btn:hover {
  background: white;
  transform: translateY(-1px);
}

/* --- Loading State --- */
.loading-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  text-align: center;
  padding: 40px 20px;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top: 4px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* --- Error State --- */
.error-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  text-align: center;
  padding: 40px 20px;
}

.error-icon {
  margin-bottom: 20px;
}

.error-container h2 {
  margin: 0 0 12px 0;
  font-size: 24px;
  font-weight: 600;
}

.error-container p {
  margin: 0 0 24px 0;
  color: rgba(255, 255, 255, 0.8);
  font-size: 16px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.2s ease;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

/* --- Conversation Content --- */
.conversation-content {
  flex: 1;
  padding: 40px 20px;
}

.messages-container {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* --- Message Styles --- */
.message-wrapper {
  display: flex;
  gap: 15px;
  width: 100%;
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  color: white;
  font-size: 16px;
}

.user .avatar {
  background: rgba(255, 255, 255, 0.9);
  color: #667eea;
}

.assistant .avatar {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.content-container {
  display: flex;
  flex-direction: column;
  max-width: 90%;
  flex: 1;
}

.message-bubble {
  padding: 16px 20px;
  border-radius: 20px;
  line-height: 1.7;
  word-wrap: break-word;
  font-size: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.assistant .message-bubble {
  background: rgba(255, 255, 255, 0.95);
  color: #333;
  border-bottom-left-radius: 8px;
}

.user .message-bubble {
  background: rgba(255, 255, 255, 0.9);
  color: #667eea;
  border-bottom-right-radius: 8px;
  margin-left: auto;
}

.user {
  flex-direction: row-reverse;
}

.user .content-container {
  align-items: flex-end;
}

.message-timestamp {
  margin-top: 6px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  text-align: right;
}

.user .message-timestamp {
  text-align: left;
}

/* --- Footer --- */
.public-footer {
  background: rgba(0, 0, 0, 0.2);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding: 20px 0;
  margin-top: auto;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  text-align: center;
}

.footer-content p {
  margin: 0 0 8px 0;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
}

.app-link {
  color: white;
  text-decoration: none;
  font-weight: 500;
}

.app-link:hover {
  text-decoration: underline;
}

.expiry-info {
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
}

/* --- Share Toast --- */
.share-toast {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: rgba(16, 185, 129, 0.9);
  color: white;
  padding: 12px 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(10px);
  animation: slideIn 0.3s ease;
  z-index: 1000;
}

@keyframes slideIn {
  from { transform: translateY(100%); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

/* --- Responsive Design --- */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .conversation-title {
    font-size: 24px;
  }

  .conversation-meta {
    gap: 12px;
  }

  .messages-container {
    gap: 16px;
  }

  .avatar {
    width: 40px;
    height: 40px;
    font-size: 14px;
  }

  .message-bubble {
    padding: 12px 16px;
    font-size: 15px;
  }

  .content-container {
    max-width: 85%;
  }
}

@media (max-width: 480px) {
  .public-header {
    padding: 16px 0;
  }

  .header-content {
    padding: 0 16px;
  }

  .conversation-title {
    font-size: 20px;
  }

  .conversation-description {
    font-size: 15px;
  }

  .meta-item {
    font-size: 13px;
  }

  .conversation-content {
    padding: 20px 16px;
  }

  .content-container {
    max-width: 80%;
  }

  .message-bubble {
    padding: 10px 14px;
    font-size: 14px;
  }
}

/* --- Markdown Content Styles --- */
:deep(.message-text) {
  white-space: pre-wrap;
  line-height: 1.7;
}

:deep(.message-text p) {
  margin: 0 0 12px 0;
}

:deep(.message-text p:last-child) {
  margin-bottom: 0;
}

:deep(.message-text pre) {
  background: rgba(0, 0, 0, 0.8);
  color: #f8f8f2;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
  font-family: 'Fira Code', 'Courier New', monospace;
  font-size: 14px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

:deep(.message-text pre code) {
  background: transparent;
  padding: 0;
}

:deep(.message-text p code),
:deep(.message-text li code) {
  background: rgba(0, 0, 0, 0.2);
  padding: 3px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', 'Courier New', monospace;
  font-size: 13px;
  color: #e83e8c;
}

:deep(.message-text strong) {
  font-weight: 600;
  color: inherit;
}

:deep(.message-text em) {
  font-style: italic;
}

:deep(.message-text ul),
:deep(.message-text ol) {
  padding-left: 20px;
  margin: 12px 0;
}

:deep(.message-text li) {
  margin-bottom: 4px;
}

:deep(.message-text blockquote) {
  border-left: 4px solid rgba(255, 255, 255, 0.3);
  padding-left: 16px;
  margin: 12px 0;
  font-style: italic;
  color: rgba(255, 255, 255, 0.8);
}

:deep(.message-text a) {
  color: #667eea;
  text-decoration: none;
  border-bottom: 1px solid rgba(102, 126, 234, 0.5);
  transition: border-color 0.2s ease;
}

:deep(.message-text a:hover) {
  border-bottom-color: #667eea;
}

:deep(.message-text table) {
  border-collapse: collapse;
  margin: 12px 0;
  width: 100%;
}

:deep(.message-text th),
:deep(.message-text td) {
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 8px 12px;
  text-align: left;
}

:deep(.message-text th) {
  background: rgba(255, 255, 255, 0.1);
  font-weight: 600;
}
</style>