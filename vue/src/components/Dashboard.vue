<template>
  <div class="dashboard">
    <!-- 顶部导航栏 -->
    <div class="dashboard-header">
      <div class="header-left">
        <h1 class="dashboard-title">Deep Research 控制台</h1>
        <div class="system-status" :class="systemHealth?.status">
          <i class="icon-circle"></i>
          <span>{{ getStatusText(systemHealth?.status) }}</span>
        </div>
      </div>
      <div class="header-right">
        <button
          class="btn-refresh"
          @click="refreshAllData"
          :disabled="loading"
        >
          <i class="icon-refresh" :class="{ spinning: loading }"></i>
          刷新数据
        </button>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="dashboard-content">
      <!-- 统计卡片 -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">
            <i class="icon-file"></i>
          </div>
          <div class="stat-content">
            <h3>{{ documentStats?.total_documents || 0 }}</h3>
            <p>文档总数</p>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">
            <i class="icon-search"></i>
          </div>
          <div class="stat-content">
            <h3>{{ performanceStats?.vector_searches_total || 0 }}</h3>
            <p>向量搜索</p>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">
            <i class="icon-zap"></i>
          </div>
          <div class="stat-content">
            <h3>{{ performanceStats?.llm_calls_total || 0 }}</h3>
            <p>AI调用</p>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">
            <i class="icon-activity"></i>
          </div>
          <div class="stat-content">
            <h3>{{ formatDuration(performanceStats?.avg_request_duration || 0) }}</h3>
            <p>平均响应</p>
          </div>
        </div>
      </div>

      <!-- 主要功能区域 -->
      <div class="main-content">
        <!-- 左侧面板 -->
        <div class="left-panel">
          <!-- 文档管理 -->
          <div class="panel-section">
            <div class="panel-header">
              <h3>文档管理</h3>
              <button class="btn-toggle" @click="showDocumentManager = !showDocumentManager">
                <i :class="showDocumentManager ? 'icon-chevron-up' : 'icon-chevron-down'"></i>
              </button>
            </div>
            <div v-if="showDocumentManager" class="panel-content">
              <DocumentManager
                @document-selected="onDocumentSelected"
                @search-in-document="onSearchInDocument"
              />
            </div>
          </div>

          <!-- 文档搜索 -->
          <div class="panel-section">
            <div class="panel-header">
              <h3>文档搜索</h3>
              <button class="btn-toggle" @click="showDocumentSearch = !showDocumentSearch">
                <i :class="showDocumentSearch ? 'icon-chevron-up' : 'icon-chevron-down'"></i>
              </button>
            </div>
            <div v-if="showDocumentSearch" class="panel-content">
              <DocumentSearch
                :conversation-id="currentConversationId"
                @result-selected="onSearchResultSelected"
                @evidence-viewed="onEvidenceViewed"
              />
            </div>
          </div>
        </div>

        <!-- 右侧面板 -->
        <div class="right-panel">
          <!-- 证据链 -->
          <div class="panel-section">
            <div class="panel-header">
              <h3>证据链</h3>
              <button class="btn-toggle" @click="showEvidenceChain = !showEvidenceChain">
                <i :class="showEvidenceChain ? 'icon-chevron-up' : 'icon-chevron-down'"></i>
              </button>
            </div>
            <div v-if="showEvidenceChain" class="panel-content">
              <EvidenceChain
                :conversation-id="currentConversationId"
                :research-session-id="currentResearchSessionId"
                @evidence-updated="onEvidenceUpdated"
              />
            </div>
          </div>

          <!-- 系统监控 -->
          <div class="panel-section">
            <div class="panel-header">
              <h3>系统监控</h3>
              <button class="btn-toggle" @click="showSystemMonitor = !showSystemMonitor">
                <i :class="showSystemMonitor ? 'icon-chevron-up' : 'icon-chevron-down'"></i>
              </button>
            </div>
            <div v-if="showSystemMonitor" class="panel-content">
              <SystemMonitor />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useChatStore } from '@/store'
import DocumentManager from './DocumentManager.vue'
import DocumentSearch from './DocumentSearch.vue'
import EvidenceChain from './EvidenceChain.vue'
import SystemMonitor from './SystemMonitor.vue'
import { healthAPI } from '@/services/api.js'

// Props
const props = defineProps({
  currentConversationId: {
    type: String,
    default: null
  },
  currentResearchSessionId: {
    type: String,
    default: null
  }
})

// Emits
const emit = defineEmits([
  'document-selected',
  'search-result-selected',
  'evidence-viewed'
])

// Reactive data
const chatStore = useChatStore()
const loading = ref(false)
const showDocumentManager = ref(true)
const showDocumentSearch = ref(false)
const showEvidenceChain = ref(true)
const showSystemMonitor = ref(false)

// Computed
const systemHealth = computed(() => chatStore.systemHealth)
const performanceStats = computed(() => chatStore.systemPerformance)
const documentStats = computed(() => chatStore.documentStats)

// Methods
const getStatusText = (status) => {
  const statusMap = {
    healthy: '正常',
    unhealthy: '异常',
    unknown: '未知'
  }
  return statusMap[status] || '未知'
}

const formatDuration = (duration) => {
  if (duration < 1) {
    return `${(duration * 1000).toFixed(0)}ms`
  }
  return `${duration.toFixed(2)}s`
}

const refreshAllData = async () => {
  loading.value = true
  try {
    // 刷新系统健康状态
    await chatStore.checkConnection()

    // 刷新文档统计
    try {
      const docStats = await healthAPI.getDatabaseStats()
      chatStore.setDocumentStats(docStats)
    } catch (error) {
      console.warn('获取文档统计失败:', error)
    }

    // 刷新性能统计
    try {
      const perfStats = await healthAPI.getPerformanceStats()
      chatStore.setSystemPerformance(perfStats)
    } catch (error) {
      console.warn('获取性能统计失败:', error)
    }

  } catch (error) {
    console.error('刷新数据失败:', error)
  } finally {
    loading.value = false
  }
}

const onDocumentSelected = (document) => {
  emit('document-selected', document)
}

const onSearchInDocument = (jobId) => {
  // 在文档中搜索
  console.log('在文档中搜索:', jobId)
}

const onSearchResultSelected = (result) => {
  emit('search-result-selected', result)
}

const onEvidenceViewed = (evidence) => {
  emit('evidence-viewed', evidence)
}

const onEvidenceUpdated = () => {
  // 证据链更新后的处理
  console.log('证据链已更新')
}

// Lifecycle
onMounted(async () => {
  await refreshAllData()

  // 设置自动刷新（每30秒）
  setInterval(refreshAllData, 30000)
})
</script>

<style scoped>
.dashboard {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--primary-bg);
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-color);
  background: var(--secondary-bg);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.dashboard-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.system-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.system-status.healthy {
  background: rgba(34, 197, 94, 0.1);
  color: var(--success-color);
}

.system-status.unhealthy {
  background: rgba(239, 68, 68, 0.1);
  color: var(--error-color);
}

.header-right {
  display: flex;
  gap: 8px;
}

.btn-refresh {
  padding: 8px 16px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--primary-bg);
  color: var(--text-primary);
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.btn-refresh:hover {
  background: var(--hover-bg);
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

.dashboard-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--secondary-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background: var(--accent-color);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
}

.stat-content h3 {
  margin: 0 0 4px 0;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-content p {
  margin: 0;
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.main-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  height: calc(100vh - 200px);
}

.left-panel, .right-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.panel-section {
  background: var(--secondary-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  background: var(--primary-bg);
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.btn-toggle {
  padding: 4px;
  border: none;
  background: none;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 3px;
  transition: all 0.2s;
}

.btn-toggle:hover {
  background: var(--hover-bg);
  color: var(--text-primary);
}

.panel-content {
  padding: 0;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
    height: auto;
  }

  .right-panel {
    order: -1;
  }
}

@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .main-content {
    grid-template-columns: 1fr;
  }
}
</style>
