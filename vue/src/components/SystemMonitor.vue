<template>
  <div class="system-monitor">
    <div class="monitor-header">
      <h3 class="monitor-title">
        <i class="icon-monitor"></i>
        系统监控
      </h3>
      <div class="monitor-controls">
        <button class="btn-refresh" @click="refreshStatus" :disabled="loading">
          <i class="icon-refresh" :class="{ spinning: loading }"></i>
          刷新
        </button>
        <div class="auto-refresh">
          <label>
            <input
              type="checkbox"
              v-model="autoRefresh"
              @change="toggleAutoRefresh"
            />
            自动刷新
          </label>
          <select v-model="refreshInterval" @change="updateRefreshTimer">
            <option value="5000">5秒</option>
            <option value="10000">10秒</option>
            <option value="30000">30秒</option>
            <option value="60000">1分钟</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 健康状态概览 -->
    <div class="health-overview">
      <div class="overview-cards">
        <div class="overview-card">
          <div class="card-icon">
            <i class="icon-heart" :class="{ healthy: healthData?.status === 'healthy', unhealthy: healthData?.status === 'unhealthy' }"></i>
          </div>
          <div class="card-content">
            <h4>系统状态</h4>
            <p class="status-text" :class="healthData?.status">
              {{ getStatusText(healthData?.status) }}
            </p>
          </div>
        </div>

        <div class="overview-card">
          <div class="card-icon">
            <i class="icon-server"></i>
          </div>
          <div class="card-content">
            <h4>服务状态</h4>
            <div class="service-status">
              <span class="service-item" :class="{ healthy: healthData?.services?.database === 'healthy', unhealthy: healthData?.services?.database === 'unhealthy' }">
                数据库
              </span>
              <span class="service-item" :class="{ healthy: healthData?.services?.redis === 'healthy', unhealthy: healthData?.services?.redis === 'unhealthy' }">
                Redis
              </span>
            </div>
          </div>
        </div>

        <div class="overview-card">
          <div class="card-icon">
            <i class="icon-activity"></i>
          </div>
          <div class="card-content">
            <h4>性能指标</h4>
            <p class="metric-text">
              响应时间: {{ formatDuration(performanceData?.avg_request_duration || 0) }}
            </p>
            <p class="metric-text">
              错误率: {{ ((performanceData?.error_rate || 0) * 100).toFixed(1) }}%
            </p>
          </div>
        </div>

        <div class="overview-card">
          <div class="card-icon">
            <i class="icon-zap"></i>
          </div>
          <div class="card-content">
            <h4>AI调用</h4>
            <p class="metric-text">
              总调用: {{ performanceData?.llm_calls_total || 0 }}
            </p>
            <p class="metric-text">
              Token使用: {{ formatNumber(performanceData?.llm_tokens_total || 0) }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- 详细状态面板 -->
    <div class="detail-panels">
      <div class="panel">
        <div class="panel-header">
          <h4>请求统计</h4>
        </div>
        <div class="panel-content">
          <div class="metric-grid">
            <div class="metric-item">
              <span class="metric-label">总请求数</span>
              <span class="metric-value">{{ formatNumber(performanceData?.requests_total || 0) }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">错误请求</span>
              <span class="metric-value error">{{ formatNumber(performanceData?.errors_total || 0) }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">平均响应时间</span>
              <span class="metric-value">{{ formatDuration(performanceData?.avg_request_duration || 0) }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">95%响应时间</span>
              <span class="metric-value">{{ formatDuration(performanceData?.p95_request_duration || 0) }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">缓存命中率</span>
              <span class="metric-value">{{ ((performanceData?.cache_hit_rate || 0) * 100).toFixed(1) }}%</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">向量搜索</span>
              <span class="metric-value">{{ formatNumber(performanceData?.vector_searches_total || 0) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <h4>数据库统计</h4>
        </div>
        <div class="panel-content">
          <div class="metric-grid">
            <div class="metric-item">
              <span class="metric-label">文档总数</span>
              <span class="metric-value">{{ formatNumber(databaseStats?.total_documents || 0) }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">分块总数</span>
              <span class="metric-value">{{ formatNumber(databaseStats?.total_chunks || 0) }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">嵌入总数</span>
              <span class="metric-value">{{ formatNumber(databaseStats?.total_embeddings || 0) }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">证据总数</span>
              <span class="metric-value">{{ formatNumber(databaseStats?.total_evidence || 0) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <h4>系统信息</h4>
        </div>
        <div class="panel-content">
          <div class="system-info-grid">
            <div class="info-item">
              <span class="info-label">平台</span>
              <span class="info-value">{{ systemInfo?.platform || '未知' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Python版本</span>
              <span class="info-value">{{ systemInfo?.python_version || '未知' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">CPU核心数</span>
              <span class="info-value">{{ systemInfo?.cpu_count || '未知' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">内存总量</span>
              <span class="info-value">{{ formatBytes(systemInfo?.memory_total || 0) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">可用内存</span>
              <span class="info-value">{{ formatBytes(systemInfo?.memory_available || 0) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">运行时间</span>
              <span class="info-value">{{ formatUptime(systemInfo?.uptime || 0) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <h4>最近活动</h4>
        </div>
        <div class="panel-content">
          <div class="recent-activity">
            <div
              v-for="activity in recentActivities"
              :key="activity.id"
              class="activity-item"
              :class="activity.type"
            >
              <div class="activity-icon">
                <i :class="getActivityIcon(activity.type)"></i>
              </div>
              <div class="activity-content">
                <p class="activity-text">{{ activity.text }}</p>
                <span class="activity-time">{{ formatTime(activity.timestamp) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { healthAPI } from '@/services/api.js'

// Reactive data
const healthData = ref(null)
const performanceData = ref(null)
const databaseStats = ref(null)
const systemInfo = ref(null)
const loading = ref(false)
const autoRefresh = ref(false)
const refreshInterval = ref('30000') // 30秒
const refreshTimer = ref(null)
const recentActivities = ref([
  {
    id: 1,
    type: 'request',
    text: '收到新的聊天请求',
    timestamp: Date.now() - 30000
  },
  {
    id: 2,
    type: 'document',
    text: '文档处理完成',
    timestamp: Date.now() - 60000
  },
  {
    id: 3,
    type: 'search',
    text: '向量搜索请求',
    timestamp: Date.now() - 120000
  },
  {
    id: 4,
    type: 'error',
    text: 'API调用失败',
    timestamp: Date.now() - 180000
  }
])

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

const formatNumber = (num) => {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`
  }
  return num.toString()
}

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatUptime = (seconds) => {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)

  if (days > 0) {
    return `${days}天 ${hours}小时 ${minutes}分钟`
  }
  if (hours > 0) {
    return `${hours}小时 ${minutes}分钟`
  }
  return `${minutes}分钟`
}

const formatTime = (timestamp) => {
  const now = Date.now()
  const diff = now - timestamp

  if (diff < 60000) { // 1分钟内
    return `${Math.floor(diff / 1000)}秒前`
  }
  if (diff < 3600000) { // 1小时内
    return `${Math.floor(diff / 60000)}分钟前`
  }
  if (diff < 86400000) { // 1天内
    return `${Math.floor(diff / 3600000)}小时前`
  }
  return `${Math.floor(diff / 86400000)}天前`
}

const getActivityIcon = (type) => {
  const icons = {
    request: 'icon-message',
    document: 'icon-file',
    search: 'icon-search',
    error: 'icon-error',
    success: 'icon-check'
  }
  return icons[type] || 'icon-info'
}

const refreshStatus = async () => {
  loading.value = true
  try {
    // 并行加载各种状态信息
    const [
      healthResult,
      performanceResult,
      databaseResult,
      systemResult
    ] = await Promise.allSettled([
      healthAPI.checkHealth(),
      healthAPI.getPerformanceStats(),
      healthAPI.getDatabaseStats(),
      healthAPI.getSystemInfo()
    ])

    if (healthResult.status === 'fulfilled') {
      healthData.value = healthResult.value
    }

    if (performanceResult.status === 'fulfilled') {
      performanceData.value = performanceResult.value
    }

    if (databaseResult.status === 'fulfilled') {
      databaseStats.value = databaseResult.value
    }

    if (systemResult.status === 'fulfilled') {
      systemInfo.value = systemResult.value
    }

  } catch (error) {
    console.error('刷新状态失败:', error)
  } finally {
    loading.value = false
  }
}

const toggleAutoRefresh = () => {
  if (autoRefresh.value) {
    updateRefreshTimer()
  } else {
    clearRefreshTimer()
  }
}

const updateRefreshTimer = () => {
  clearRefreshTimer()
  if (autoRefresh.value) {
    const interval = parseInt(refreshInterval.value)
    refreshTimer.value = setInterval(refreshStatus, interval)
  }
}

const clearRefreshTimer = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
}

// Lifecycle
onMounted(async () => {
  await refreshStatus()
  if (autoRefresh.value) {
    updateRefreshTimer()
  }
})

onUnmounted(() => {
  clearRefreshTimer()
})
</script>

<style scoped>
.system-monitor {
  background: var(--primary-bg);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  background: var(--secondary-bg);
}

.monitor-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.monitor-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.btn-refresh {
  padding: 6px 12px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--primary-bg);
  color: var(--text-primary);
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s;
}

.btn-refresh:hover {
  background: var(--hover-bg);
}

.btn-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.auto-refresh {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.auto-refresh label {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.auto-refresh select {
  padding: 2px 6px;
  border: 1px solid var(--border-color);
  border-radius: 3px;
  background: var(--primary-bg);
  color: var(--text-primary);
  font-size: 11px;
}

.health-overview {
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.overview-card {
  background: var(--secondary-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-icon {
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

.card-icon .icon-heart.healthy {
  background: var(--success-color);
}

.card-icon .icon-heart.unhealthy {
  background: var(--error-color);
}

.card-content {
  flex: 1;
}

.card-content h4 {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.status-text {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.status-text.healthy {
  color: var(--success-color);
}

.status-text.unhealthy {
  color: var(--error-color);
}

.service-status {
  display: flex;
  gap: 8px;
}

.service-item {
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 500;
  background: var(--error-color);
  color: white;
}

.service-item.healthy {
  background: var(--success-color);
}

.metric-text {
  margin: 2px 0;
  font-size: 12px;
  color: var(--text-secondary);
}

.detail-panels {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 16px;
  padding: 20px;
}

.panel {
  background: var(--secondary-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  background: var(--primary-bg);
}

.panel-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.panel-content {
  padding: 16px 20px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color);
}

.metric-item:last-child {
  border-bottom: none;
}

.metric-label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.metric-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.metric-value.error {
  color: var(--error-color);
}

.system-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
}

.info-label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.info-value {
  font-size: 12px;
  color: var(--text-primary);
  font-family: 'Courier New', monospace;
}

.recent-activity {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 6px;
  background: var(--primary-bg);
}

.activity-item.request {
  border-left: 3px solid var(--accent-color);
}

.activity-item.document {
  border-left: 3px solid var(--success-color);
}

.activity-item.search {
  border-left: 3px solid var(--warning-color);
}

.activity-item.error {
  border-left: 3px solid var(--error-color);
}

.activity-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--accent-color);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 14px;
}

.activity-item.document .activity-icon {
  background: var(--success-color);
}

.activity-item.search .activity-icon {
  background: var(--warning-color);
}

.activity-item.error .activity-icon {
  background: var(--error-color);
}

.activity-content {
  flex: 1;
}

.activity-text {
  margin: 0 0 2px 0;
  font-size: 13px;
  color: var(--text-primary);
}

.activity-time {
  font-size: 11px;
  color: var(--text-tertiary);
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
