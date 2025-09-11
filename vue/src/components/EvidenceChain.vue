<template>
  <div class="evidence-chain">
    <div class="evidence-header">
      <h3 class="evidence-title">
        <i class="icon-document"></i>
        证据链 ({{ evidenceList.length }})
      </h3>
      <div class="evidence-controls">
        <button
          class="btn-filter"
          :class="{ active: filterType }"
          @click="toggleFilter"
        >
          <i class="icon-filter"></i>
          {{ filterType ? '全部' : '已验证' }}
        </button>
        <button class="btn-refresh" @click="refreshEvidence" :disabled="loading">
          <i class="icon-refresh" :class="{ spinning: loading }"></i>
          刷新
        </button>
      </div>
    </div>

    <div class="evidence-stats" v-if="stats">
      <div class="stat-item">
        <span class="stat-label">文档来源:</span>
        <span class="stat-value">{{ stats.evidence_by_type?.document || 0 }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">网络来源:</span>
        <span class="stat-value">{{ stats.evidence_by_type?.web || 0 }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">平均评分:</span>
        <span class="stat-value">{{ (stats.avg_relevance_score || 0).toFixed(2) }}</span>
      </div>
    </div>

    <div class="evidence-list">
      <div
        v-for="evidence in filteredEvidence"
        :key="evidence.id"
        class="evidence-item"
        :class="{
          verified: evidence.verified_by_user,
          used: evidence.used_in_response
        }"
      >
        <div class="evidence-meta">
          <div class="evidence-source">
            <span class="source-type" :class="evidence.source_type">
              {{ getSourceTypeLabel(evidence.source_type) }}
            </span>
            <span class="source-title" v-if="evidence.source_title">
              {{ evidence.source_title }}
            </span>
          </div>
          <div class="evidence-actions">
            <button
              class="btn-mark-used"
              :class="{ active: evidence.used_in_response }"
              @click="toggleEvidenceUsed(evidence.id, !evidence.used_in_response)"
              :disabled="markingUsed === evidence.id"
            >
              <i class="icon-check"></i>
              {{ evidence.used_in_response ? '已使用' : '标记使用' }}
            </button>
            <button
              class="btn-verify"
              :class="{ active: evidence.verified_by_user }"
              @click="toggleEvidenceVerified(evidence.id, !evidence.verified_by_user)"
              :disabled="verifying === evidence.id"
            >
              <i class="icon-verified"></i>
              {{ evidence.verified_by_user ? '已验证' : '验证' }}
            </button>
          </div>
        </div>

        <div class="evidence-content">
          <div class="evidence-snippet" v-if="evidence.snippet">
            {{ evidence.snippet }}
          </div>
          <div class="evidence-full-content" v-if="showFullContent[evidence.id]">
            {{ evidence.content }}
          </div>
          <button
            class="btn-toggle-content"
            @click="toggleFullContent(evidence.id)"
            v-if="evidence.content && evidence.content.length > 200"
          >
            {{ showFullContent[evidence.id] ? '收起' : '展开全文' }}
          </button>
        </div>

        <div class="evidence-info">
          <div class="evidence-scores">
            <span class="score-item">
              <i class="icon-star"></i>
              相关性: {{ (evidence.relevance_score || 0).toFixed(2) }}
            </span>
            <span class="score-item">
              <i class="icon-target"></i>
              置信度: {{ (evidence.confidence_score || 0).toFixed(2) }}
            </span>
            <span class="score-item" v-if="evidence.quality_score">
              <i class="icon-quality"></i>
              质量: {{ evidence.quality_score.toFixed(2) }}
            </span>
          </div>
          <div class="evidence-url" v-if="evidence.source_url">
            <a :href="evidence.source_url" target="_blank" rel="noopener noreferrer">
              <i class="icon-link"></i>
              查看来源
            </a>
          </div>
        </div>

        <div class="evidence-position" v-if="evidence.start_pos">
          <span class="position-info">
            位置: 第{{ evidence.start_pos }}-{{ evidence.end_pos }}字符
            <span v-if="evidence.page_number"> (第{{ evidence.page_number }}页)</span>
          </span>
        </div>
      </div>

      <div v-if="filteredEvidence.length === 0" class="no-evidence">
        <i class="icon-empty"></i>
        <p>{{ filterType ? '暂无已验证的证据' : '暂无证据数据' }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { evidenceAPI } from '@/services/api.js'

// Props
const props = defineProps({
  conversationId: {
    type: String,
    default: null
  },
  researchSessionId: {
    type: String,
    default: null
  }
})

// Emits
const emit = defineEmits(['evidence-updated'])

// Reactive data
const evidenceList = ref([])
const stats = ref(null)
const loading = ref(false)
const markingUsed = ref(null)
const verifying = ref(null)
const showFullContent = ref({})
const filterType = ref(false) // false: all, true: verified only

// Computed
const filteredEvidence = computed(() => {
  if (!filterType.value) {
    return evidenceList.value
  }
  return evidenceList.value.filter(item => item.verified_by_user)
})

// Methods
const getSourceTypeLabel = (type) => {
  const labels = {
    document: '文档',
    web: '网页',
    api: 'API',
    search: '搜索',
    database: '数据库'
  }
  return labels[type] || type
}

const toggleFilter = () => {
  filterType.value = !filterType.value
}

const toggleFullContent = (evidenceId) => {
  showFullContent.value[evidenceId] = !showFullContent.value[evidenceId]
}

const toggleEvidenceUsed = async (evidenceId, used) => {
  markingUsed.value = evidenceId
  try {
    await evidenceAPI.markEvidenceUsed(evidenceId, used)
    // 更新本地状态
    const evidence = evidenceList.value.find(e => e.id === evidenceId)
    if (evidence) {
      evidence.used_in_response = used
    }
    emit('evidence-updated')
  } catch (error) {
    console.error('标记证据使用状态失败:', error)
    alert('操作失败，请重试')
  } finally {
    markingUsed.value = null
  }
}

const toggleEvidenceVerified = async (evidenceId, verified) => {
  verifying.value = evidenceId
  try {
    // 这里需要一个新的API端点来标记验证状态
    // 暂时使用标记使用状态的API作为替代
    await evidenceAPI.markEvidenceUsed(evidenceId, verified)
    const evidence = evidenceList.value.find(e => e.id === evidenceId)
    if (evidence) {
      evidence.verified_by_user = verified
    }
    emit('evidence-updated')
  } catch (error) {
    console.error('标记证据验证状态失败:', error)
    alert('操作失败，请重试')
  } finally {
    verifying.value = null
  }
}

const refreshEvidence = async () => {
  await loadEvidence()
}

const loadEvidence = async () => {
  if (!props.conversationId && !props.researchSessionId) {
    return
  }

  loading.value = true
  try {
    let result
    if (props.conversationId) {
      result = await evidenceAPI.getConversationEvidence(props.conversationId)
    } else {
      result = await evidenceAPI.getResearchEvidence(props.researchSessionId)
    }

    evidenceList.value = result.evidence_list || []
    stats.value = {
      total_evidence: result.total_evidence || 0,
      evidence_by_type: result.evidence_by_type || {},
      avg_relevance_score: 0 // 需要从单独的统计API获取
    }

    // 获取统计信息
    try {
      const statsResult = await evidenceAPI.getEvidenceStats()
      stats.value.avg_relevance_score = statsResult.avg_relevance_score || 0
    } catch (error) {
      console.warn('获取证据统计失败:', error)
    }

  } catch (error) {
    console.error('加载证据链失败:', error)
    evidenceList.value = []
    stats.value = null
  } finally {
    loading.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadEvidence()
})

// Watchers
watch(() => props.conversationId, loadEvidence)
watch(() => props.researchSessionId, loadEvidence)
</script>

<style scoped>
.evidence-chain {
  background: var(--primary-bg);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.evidence-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  background: var(--secondary-bg);
}

.evidence-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.evidence-controls {
  display: flex;
  gap: 8px;
}

.btn-filter, .btn-refresh, .btn-mark-used, .btn-verify {
  padding: 6px 12px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--primary-bg);
  color: var(--text-primary);
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.btn-filter:hover, .btn-refresh:hover {
  background: var(--hover-bg);
}

.btn-filter.active, .btn-mark-used.active, .btn-verify.active {
  background: var(--accent-color);
  color: white;
  border-color: var(--accent-color);
}

.btn-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.evidence-stats {
  display: flex;
  gap: 20px;
  padding: 12px 20px;
  background: var(--secondary-bg);
  border-bottom: 1px solid var(--border-color);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}

.stat-label {
  font-weight: 500;
}

.stat-value {
  color: var(--accent-color);
  font-weight: 600;
}

.evidence-list {
  max-height: 600px;
  overflow-y: auto;
}

.evidence-item {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  transition: background-color 0.2s;
}

.evidence-item:hover {
  background: var(--hover-bg);
}

.evidence-item.verified {
  border-left: 3px solid var(--success-color);
}

.evidence-item.used {
  background: rgba(59, 130, 246, 0.05);
}

.evidence-meta {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.evidence-source {
  display: flex;
  align-items: center;
  gap: 8px;
}

.source-type {
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
}

.source-type.document {
  background: #10b981;
  color: white;
}

.source-type.web {
  background: #3b82f6;
  color: white;
}

.source-type.api {
  background: #8b5cf6;
  color: white;
}

.source-type.search {
  background: #f59e0b;
  color: white;
}

.source-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.evidence-actions {
  display: flex;
  gap: 6px;
}

.btn-mark-used:disabled, .btn-verify:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.evidence-content {
  margin-bottom: 12px;
}

.evidence-snippet, .evidence-full-content {
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.evidence-snippet {
  color: var(--text-secondary);
  font-style: italic;
}

.btn-toggle-content {
  padding: 4px 8px;
  border: none;
  background: none;
  color: var(--accent-color);
  cursor: pointer;
  font-size: 12px;
  text-decoration: underline;
}

.btn-toggle-content:hover {
  color: var(--accent-hover);
}

.evidence-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.evidence-scores {
  display: flex;
  gap: 12px;
}

.score-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}

.evidence-url a {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--accent-color);
  text-decoration: none;
  font-size: 12px;
}

.evidence-url a:hover {
  text-decoration: underline;
}

.evidence-position {
  font-size: 11px;
  color: var(--text-tertiary);
}

.position-info {
  background: var(--secondary-bg);
  padding: 4px 8px;
  border-radius: 3px;
}

.no-evidence {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-secondary);
}

.no-evidence i {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.no-evidence p {
  margin: 0;
  font-size: 14px;
}
</style>
