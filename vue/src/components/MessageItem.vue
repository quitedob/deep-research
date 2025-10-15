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
        <div v-else class="message-text" v-html="formattedContent" @click="handleCitationClick"></div>
      </div>

      <!-- Citation Panel (Gemini-style) -->
      <div v-if="showCitationPanel && selectedCitation" class="citation-panel" @click.stop>
        <div class="citation-header">
          <div class="citation-source">
            <span class="source-icon" :class="selectedCitation.source_type">{{ getSourceIcon(selectedCitation.source_type) }}</span>
            <span class="source-title">{{ selectedCitation.source_title || '来源详情' }}</span>
          </div>
          <button @click="hideCitation" class="close-citation">×</button>
        </div>
        <div class="citation-content">
          <div class="citation-snippet" v-if="selectedCitation.snippet">
            {{ selectedCitation.snippet }}
          </div>
          <div class="citation-scores" v-if="selectedCitation.relevance_score">
            <span class="score">相关性: {{ (selectedCitation.relevance_score * 100).toFixed(0) }}%</span>
            <span class="score">置信度: {{ (selectedCitation.confidence_score * 100).toFixed(0) }}%</span>
          </div>
          <div class="citation-actions">
            <a v-if="selectedCitation.source_url" :href="selectedCitation.source_url" target="_blank" rel="noopener noreferrer" class="source-link">
              查看原始来源
            </a>
          </div>
        </div>
      </div>

      <!-- Evidence Chain for Assistant Messages (folded by default) -->
      <div v-if="message.role === 'assistant' && conversationId" class="evidence-section">
        <button @click="toggleEvidenceExpanded" class="evidence-toggle">
          <span class="toggle-icon">{{ evidenceExpanded ? '▼' : '▶' }}</span>
          <span>来源证据 ({{ evidenceCount }})</span>
        </button>
        <div v-if="evidenceExpanded" class="evidence-content">
          <EvidenceChain
            :conversation-id="conversationId"
            :research-session-id="null"
            @evidence-updated="$emit('evidence-updated', $event)"
          />
        </div>
      </div>

      <div class="message-actions" v-if="!isThinking">
        <!-- Timer Display -->
        <div v-if="message.role === 'assistant' && message.duration" class="timer-display">
          <span>{{ message.duration }}s</span>
        </div>

        <button @click="copyContent" title="复制">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
        </button>

        <!-- Feedback Buttons for AI Messages -->
        <div v-if="message.role === 'assistant'" class="feedback-buttons">
          <button
            @click="submitFeedback(1)"
            :class="['feedback-btn', 'thumbs-up', { 'active': localFeedback === 1 }]"
            title="赞 👍"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28"></path>
              <path d="M18 15l-6-6"></path>
              <path d="M2 12v6h6"></path>
            </svg>
          </button>
          <button
            @click="submitFeedback(-1)"
            :class="['feedback-btn', 'thumbs-down', { 'active': localFeedback === -1 }]"
            title="踩 👎"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10 15V5a3 3 0 0 0-3-3l-4 9v11h11.28"></path>
              <path d="M18 15l-6-6"></path>
              <path d="M2 12v6h6"></path>
            </svg>
          </button>
        </div>
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

        <!-- Report Button -->
        <button @click="showReportDialog" title="举报内容" class="report-btn">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L2 7L2 17L12 22L22 17L22 7L12 2Z"></path>
            <path d="M12 22L12 12"></path>
            <path d="M12 12L2 7"></path>
            <path d="M12 12L22 7"></path>
          </svg>
        </button>

        <!-- Share Button -->
        <button @click="showShareDialog" title="分享对话" class="share-btn">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"></path>
            <polyline points="16 6 12 2 8 6"></polyline>
            <line x1="12" y1="2" x2="12" y2="15"></line>
          </svg>
        </button>
      </div>
    </div>

    <!-- Report Dialog -->
    <div v-if="showReportModal" class="report-modal-overlay" @click="hideReportDialog">
      <div class="report-modal" @click.stop>
        <div class="report-header">
          <h3>举报内容</h3>
          <button @click="hideReportDialog" class="close-btn">×</button>
        </div>
        <div class="report-content">
          <p class="report-message">举报以下内容：</p>
          <div class="reported-content">
            {{ message.content.substring(0, 200) }}{{ message.content.length > 200 ? '...' : '' }}
          </div>

          <div class="form-group">
            <label for="report-reason">举报原因：</label>
            <select id="report-reason" v-model="reportForm.reason" class="report-select">
              <option value="">请选择举报原因</option>
              <option value="spam">垃圾信息</option>
              <option value="harassment">骚扰或欺凌</option>
              <option value="violence">暴力或威胁</option>
              <option value="inappropriate_content">不当内容</option>
              <option value="misinformation">虚假信息</option>
              <option value="other">其他</option>
            </select>
          </div>

          <div class="form-group">
            <label for="report-description">详细描述（可选）：</label>
            <textarea
              id="report-description"
              v-model="reportForm.description"
              class="report-textarea"
              rows="3"
              placeholder="请详细描述您举报的原因..."
            ></textarea>
          </div>
        </div>
        <div class="report-actions">
          <button @click="hideReportDialog" class="cancel-btn">取消</button>
          <button
            @click="submitReport"
            :disabled="!reportForm.reason || reportSubmitting"
            class="submit-btn"
          >
            {{ reportSubmitting ? '提交中...' : '提交举报' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Share Dialog -->
    <div v-if="showShareModal" class="share-modal-overlay" @click="hideShareDialog">
      <div class="share-modal" @click.stop>
        <div class="share-header">
          <h3>分享对话</h3>
          <button @click="hideShareDialog" class="close-btn">×</button>
        </div>
        <div class="share-content">
          <div class="form-group">
            <label for="share-title">标题（可选）：</label>
            <input
              id="share-title"
              v-model="shareForm.title"
              type="text"
              class="share-input"
              placeholder="为这个对话起个标题..."
              maxlength="100"
            />
          </div>

          <div class="form-group">
            <label for="share-description">描述（可选）：</label>
            <textarea
              id="share-description"
              v-model="shareForm.description"
              class="share-textarea"
              rows="3"
              placeholder="简单描述一下这个对话的内容..."
              maxlength="500"
            ></textarea>
          </div>

          <div class="form-group">
            <label for="share-expire">有效期：</label>
            <select id="share-expire" v-model="shareForm.expireDays" class="share-select">
              <option value="7">7天</option>
              <option value="30" selected>30天</option>
              <option value="90">90天</option>
              <option value="365">1年</option>
            </select>
          </div>
        </div>
        <div class="share-actions">
          <button @click="hideShareDialog" class="cancel-btn">取消</button>
          <button
            @click="createShare"
            :disabled="shareSubmitting"
            class="submit-btn"
          >
            {{ shareSubmitting ? '创建中...' : '创建分享链接' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Share Success Dialog -->
    <div v-if="showShareSuccess" class="share-modal-overlay" @click="hideShareSuccess">
      <div class="share-modal" @click.stop>
        <div class="share-header">
          <h3>分享链接已创建</h3>
          <button @click="hideShareSuccess" class="close-btn">×</button>
        </div>
        <div class="share-content">
          <div class="success-message">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
            <p>分享链接已成功创建！</p>
          </div>

          <div class="form-group">
            <label>分享链接：</label>
            <div class="share-link-container">
              <input
                ref="shareLinkRef"
                :value="shareLink"
                type="text"
                class="share-link-input"
                readonly
              />
              <button @click="copyShareLink" class="copy-btn">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                </svg>
              </button>
            </div>
          </div>

          <div class="share-info">
            <p><strong>标题：</strong>{{ shareSuccessData?.title || '无标题' }}</p>
            <p><strong>有效期至：</strong>{{ formatShareExpiry(shareSuccessData?.expires_at) }}</p>
            <p><strong>访问次数：</strong>{{ shareSuccessData?.view_count || 0 }} 次</p>
          </div>
        </div>
        <div class="share-actions">
          <button @click="hideShareSuccess" class="submit-btn">完成</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, nextTick, onMounted } from 'vue';
import markdownit from 'markdown-it';
import hljs from 'highlight.js';
import EvidenceChain from '@/components/EvidenceChain.vue';

const props = defineProps({
  message: { type: Object, required: true },
  conversationId: { type: String, default: null }
});

const emit = defineEmits(['edit-and-send', 'regenerate', 'evidence-updated', 'show-citation']);

const isEditing = ref(false);
const editedContent = ref('');
const textareaRef = ref(null);

// 引用相关状态
const showCitationPanel = ref(false);
const selectedCitation = ref(null);
const citations = ref([]);

// 证据展开状态
const evidenceExpanded = ref(false);
const evidenceCount = ref(0);

// 反馈相关状态
const localFeedback = ref(null);
const feedbackLoading = ref(false);

// 举报相关状态
const showReportModal = ref(false);
const reportSubmitting = ref(false);
const reportForm = ref({
  reason: '',
  description: ''
});

// 分享相关状态
const showShareModal = ref(false);
const showShareSuccess = ref(false);
const shareSubmitting = ref(false);
const shareForm = ref({
  title: '',
  description: '',
  expireDays: 30
});
const shareLink = ref('');
const shareSuccessData = ref(null);
const shareLinkRef = ref(null);

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

const formattedContent = computed(() => {
  const content = props.message.content || '';
  const contentWithCitations = formatContentWithCitations(content);
  return md.render(contentWithCitations);
});

const copyContent = async () => {
  try {
    await navigator.clipboard.writeText(props.message.content);
  } catch (err) {
    console.error('Failed to copy: ', err);
  }
};

// 反馈提交方法
const submitFeedback = async (rating) => {
  if (feedbackLoading.value) return;

  try {
    feedbackLoading.value = true;

    // 如果已经提交了相同的反馈，则取消反馈
    if (localFeedback.value === rating) {
      await deleteFeedback();
      localFeedback.value = null;
      return;
    }

    // 提交反馈
    const response = await fetch('/api/feedback/submit', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        message_id: props.message.id,
        rating: rating,
        feedback_type: 'helpfulness'
      })
    });

    if (!response.ok) {
      throw new Error('提交反馈失败');
    }

    const result = await response.json();
    localFeedback.value = rating;

    // 可选：显示成功提示
    console.log('反馈提交成功:', result);

  } catch (error) {
    console.error('反馈提交失败:', error);
    // 可选：显示错误提示
  } finally {
    feedbackLoading.value = false;
  }
};

// 删除反馈方法
const deleteFeedback = async () => {
  try {
    const response = await fetch(`/api/feedback/message/${props.message.id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });

    if (!response.ok) {
      console.warn('删除反馈失败，但继续更新本地状态');
    }
  } catch (error) {
    console.warn('删除反馈请求失败，但继续更新本地状态:', error);
  }
};

// 初始化时加载已有的反馈状态
const loadExistingFeedback = async () => {
  try {
    const response = await fetch(`/api/feedback/message/${props.message.id}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });

    if (response.ok) {
      const data = await response.json();
      // API 返回当前用户的反馈信息
      if (data.total_feedbacks > 0) {
        // 如果有正面反馈，设置为点赞；如果有负面反馈，设置为点踩
        if (data.positive_feedbacks > 0) {
          localFeedback.value = 1;
        } else if (data.negative_feedbacks > 0) {
          localFeedback.value = -1;
        }
      }
    }
  } catch (error) {
    console.warn('加载已有反馈失败:', error);
  }
};

// 组件挂载时加载已有反馈
onMounted(() => {
  if (props.message.role === 'assistant' && props.message.id) {
    loadExistingFeedback();
  }
});

// 举报相关方法
const showReportDialog = () => {
  showReportModal.value = true;
  reportForm.value = {
    reason: '',
    description: ''
  };
};

const hideReportDialog = () => {
  showReportModal.value = false;
  reportForm.value = {
    reason: '',
    description: ''
  };
};

const submitReport = async () => {
  if (!reportForm.value.reason || reportSubmitting.value) return;

  try {
    reportSubmitting.value = true;

    const response = await fetch('/api/moderation/report', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        message_id: props.message.id,
        report_reason: reportForm.value.reason,
        report_description: reportForm.value.description,
        context_data: {
          conversation_id: props.conversationId,
          message_role: props.message.role,
          timestamp: new Date().toISOString()
        }
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || '提交举报失败');
    }

    const result = await response.json();

    // 显示成功提示
    console.log('举报提交成功:', result);

    // 可以添加一个简单的提示消息
    alert('举报已提交，我们会尽快处理。');

    hideReportDialog();

  } catch (error) {
    console.error('举报提交失败:', error);
    alert(`举报提交失败: ${error.message}`);
  } finally {
    reportSubmitting.value = false;
  }
};

// 引用相关方法
const showCitation = (citationId) => {
  selectedCitation.value = citations.value.find(c => c.id === citationId);
  showCitationPanel.value = true;
};

const hideCitation = () => {
  showCitationPanel.value = false;
  selectedCitation.value = null;
};

const formatContentWithCitations = (content) => {
  if (!content || !citations.value.length) return content;

  // 在文本中查找引用标记 [1], [2] 等，并替换为可点击的引用
  let formattedContent = content;
  citations.value.forEach((citation, index) => {
    const citationNumber = index + 1;
    const citationMark = `[${citationNumber}]`;
    formattedContent = formattedContent.replace(
      new RegExp(`\\[${citationNumber}\\]`, 'g'),
      `<sup class="citation-mark" data-citation="${citation.id}">[${citationNumber}]</sup>`
    );
  });

  return formattedContent;
};

// 分享相关方法
const showShareDialog = () => {
  showShareModal.value = true;
  shareForm.value = {
    title: '',
    description: '',
    expireDays: 30
  };
};

const hideShareDialog = () => {
  showShareModal.value = false;
  shareForm.value = {
    title: '',
    description: '',
    expireDays: 30
  };
};

const createShare = async () => {
  if (shareSubmitting.value) return;

  try {
    shareSubmitting.value = true;

    const response = await fetch('/api/share/conversation', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        session_id: props.conversationId,
        title: shareForm.value.title || undefined,
        description: shareForm.value.description || undefined,
        expire_days: parseInt(shareForm.value.expireDays)
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || '创建分享链接失败');
    }

    const result = await response.json();

    // 构建完整的分享链接
    const baseUrl = window.location.origin;
    shareLink.value = `${baseUrl}${result.public_url}`;
    shareSuccessData.value = result;

    hideShareDialog();
    showShareSuccess.value = true;

    console.log('分享链接创建成功:', result);

  } catch (error) {
    console.error('创建分享链接失败:', error);
    alert(`创建分享链接失败: ${error.message}`);
  } finally {
    shareSubmitting.value = false;
  }
};

const hideShareSuccess = () => {
  showShareSuccess.value = false;
  shareLink.value = '';
  shareSuccessData.value = null;
};

const copyShareLink = async () => {
  try {
    await navigator.clipboard.writeText(shareLink.value);

    // 可以添加一个简单的提示消息
    const originalText = shareLinkRef.value?.parentElement?.querySelector('.copy-btn')?.innerHTML;
    const copyBtn = shareLinkRef.value?.parentElement?.querySelector('.copy-btn');
    if (copyBtn) {
      copyBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';

      setTimeout(() => {
        copyBtn.innerHTML = originalText || '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>';
      }, 2000);
    }

    console.log('分享链接已复制到剪贴板');
  } catch (err) {
    console.error('复制失败: ', err);
    alert('复制失败，请手动复制链接');
  }
};

const formatShareExpiry = (expiryString) => {
  if (!expiryString) return '未知';
  try {
    const expiryDate = new Date(expiryString);
    return expiryDate.toLocaleString('zh-CN', {
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

/* --- Evidence Section Styles --- */
.evidence-section {
  margin-top: 12px;
  padding: 8px;
  background: rgba(59, 130, 246, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(59, 130, 246, 0.2);
}
.typing-indicator { display: flex; align-items: center; gap: 8px; }
.typing-dots { display: flex; gap: 4px; align-items: center; }
.typing-dot { width: 8px; height: 8px; background: #93c5fd; border-radius: 50%; animation: typing 1.4s infinite ease-in-out both; }
.typing-dot:nth-child(1) { animation-delay: -0.32s; }
.typing-dot:nth-child(2) { animation-delay: -0.16s; }
.typing-dot:nth-child(3) { animation-delay: 0s; }
@keyframes typing { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1.0); } }

/* --- Feedback Buttons Styles --- */
.feedback-buttons {
  display: flex;
  gap: 4px;
  margin-left: 8px;
}

.feedback-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  opacity: 0.7;
}

.feedback-btn:hover {
  background-color: var(--hover-bg);
  color: var(--text-primary);
  opacity: 1;
  transform: scale(1.05);
}

.feedback-btn.active {
  color: var(--accent-color);
  opacity: 1;
  background-color: rgba(59, 130, 246, 0.1);
}

.feedback-btn.thumbs-up.active {
  color: #10b981; /* Green for thumbs up */
  background-color: rgba(16, 185, 129, 0.1);
}

.feedback-btn.thumbs-down.active {
  color: #ef4444; /* Red for thumbs down */
  background-color: rgba(239, 68, 68, 0.1);
}

.feedback-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
}

/* User message feedback buttons with different colors */
.user .feedback-btn {
  color: #a0bdf6;
}

.user .feedback-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: white;
}

.user .feedback-btn.thumbs-up.active {
  color: #86efac; /* Lighter green for user messages */
  background-color: rgba(134, 239, 172, 0.1);
}

.user .feedback-btn.thumbs-down.active {
  color: #fca5a5; /* Lighter red for user messages */
  background-color: rgba(252, 165, 165, 0.1);
}

/* --- Report Button Styles --- */
.report-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  opacity: 0.7;
}

.report-btn:hover {
  background-color: var(--hover-bg);
  color: #ef4444; /* Red for report */
  opacity: 1;
  transform: scale(1.05);
}

.user .report-btn {
  color: #a0bdf6;
}

.user .report-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: #fca5a5;
}

/* --- Report Modal Styles --- */
.report-modal-overlay {
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
  backdrop-filter: blur(4px);
}

.report-modal {
  background-color: var(--primary-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--border-color);
}

.report-header h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: 18px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 24px;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  line-height: 1;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background-color: var(--hover-bg);
  color: var(--text-primary);
}

.report-content {
  padding: 20px 24px;
}

.report-message {
  margin: 0 0 12px 0;
  color: var(--text-primary);
  font-weight: 500;
}

.reported-content {
  background-color: var(--secondary-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 20px;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.5;
  max-height: 100px;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  color: var(--text-primary);
  font-weight: 500;
  font-size: 14px;
}

.report-select,
.report-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background-color: var(--primary-bg);
  color: var(--text-primary);
  font-size: 14px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.report-select:focus,
.report-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.report-textarea {
  resize: vertical;
  min-height: 80px;
  font-family: inherit;
  line-height: 1.5;
}

.report-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px 20px;
  border-top: 1px solid var(--border-color);
}

.cancel-btn,
.submit-btn {
  padding: 8px 16px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cancel-btn {
  background-color: var(--secondary-bg);
  color: var(--text-primary);
  border-color: var(--border-color);
}

.cancel-btn:hover {
  background-color: var(--hover-bg);
}

.submit-btn {
  background-color: #ef4444;
  color: white;
  border-color: #ef4444;
}

.submit-btn:hover:not(:disabled) {
  background-color: #dc2626;
  border-color: #dc2626;
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: var(--text-secondary);
  border-color: var(--text-secondary);
}

/* --- Share Button Styles --- */
.share-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  opacity: 0.7;
}

.share-btn:hover {
  background-color: var(--hover-bg);
  color: #10b981; /* Green for share */
  opacity: 1;
  transform: scale(1.05);
}

.user .share-btn {
  color: #a0bdf6;
}

.user .share-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: #86efac;
}

/* --- Share Modal Styles --- */
.share-modal-overlay {
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
  backdrop-filter: blur(4px);
}

.share-modal {
  background-color: var(--primary-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.share-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--border-color);
}

.share-header h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: 18px;
  font-weight: 600;
}

.share-content {
  padding: 20px 24px;
}

.share-input,
.share-textarea,
.share-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background-color: var(--primary-bg);
  color: var(--text-primary);
  font-size: 14px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.share-input:focus,
.share-textarea:focus,
.share-select:focus {
  outline: none;
  border-color: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
}

.share-textarea {
  resize: vertical;
  min-height: 80px;
  font-family: inherit;
  line-height: 1.5;
}

.share-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px 20px;
  border-top: 1px solid var(--border-color);
}

.share-actions .submit-btn {
  background-color: #10b981;
  color: white;
  border-color: #10b981;
}

.share-actions .submit-btn:hover:not(:disabled) {
  background-color: #059669;
  border-color: #059669;
}

/* --- Share Success Styles --- */
.success-message {
  text-align: center;
  padding: 20px 0;
  color: var(--text-primary);
}

.success-message svg {
  margin-bottom: 12px;
}

.success-message p {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
}

.share-link-container {
  display: flex;
  gap: 8px;
  align-items: center;
}

.share-link-input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background-color: var(--secondary-bg);
  color: var(--text-primary);
  font-size: 14px;
  font-family: monospace;
}

.copy-btn {
  background: none;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 8px 12px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.copy-btn:hover {
  background-color: var(--hover-bg);
  color: var(--text-primary);
  border-color: var(--accent-color);
}

.share-info {
  background-color: var(--secondary-bg);
  border-radius: 8px;
  padding: 16px;
  margin-top: 16px;
}

.share-info p {
  margin: 0 0 8px 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.share-info p:last-child {
  margin-bottom: 0;
}

.share-info strong {
  color: var(--text-primary);
}
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
