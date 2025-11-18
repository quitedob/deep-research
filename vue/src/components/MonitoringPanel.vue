<template>
  <div class="monitoring-panel">
    <div class="monitoring-header">
      <h2>系统监控</h2>
      <div class="header-actions">
        <div class="auto-refresh">
          <input
            type="checkbox"
            v-model="autoRefresh"
            id="auto-refresh"
          />
          <label for="auto-refresh">自动刷新</label>
          <select v-model="refreshInterval" class="refresh-interval">
            <option value="5000">5秒</option>
            <option value="10000">10秒</option>
            <option value="30000">30秒</option>
            <option value="60000">1分钟</option>
          </select>
        </div>
        <button @click="refreshAllData" class="btn btn-primary" :disabled="refreshing">
          {{ refreshing ? '刷新中...' : '立即刷新' }}
        </button>
      </div>
    </div>

    <div class="monitoring-content">
      <!-- 系统概览 -->
      <div class="overview-section">
        <h3>系统概览</h3>
        <div class="overview-grid">
          <div class="metric-card">
            <div class="metric-header">
              <span class="metric-icon">💻</span>
              <span class="metric-title">CPU使用率</span>
            </div>
            <div class="metric-value">
              <span class="value">{{ systemOverview.cpu_usage }}%</span>
              <div class="progress-bar">
                <div
                  class="progress-fill"
                  :class="getUsageClass(systemOverview.cpu_usage)"
                  :style="{ width: `${systemOverview.cpu_usage}%` }"
                ></div>
              </div>
            </div>
            <div class="metric-trend">
              <span :class="getTrendClass(systemOverview.cpu_trend)">
                {{ getTrendIcon(systemOverview.cpu_trend) }}
              </span>
              <span>{{ systemOverview.cpu_trend }}%</span>
            </div>
          </div>

          <div class="metric-card">
            <div class="metric-header">
              <span class="metric-icon">🧠</span>
              <span class="metric-title">内存使用率</span>
            </div>
            <div class="metric-value">
              <span class="value">{{ systemOverview.memory_usage }}%</span>
              <div class="progress-bar">
                <div
                  class="progress-fill"
                  :class="getUsageClass(systemOverview.memory_usage)"
                  :style="{ width: `${systemOverview.memory_usage}%` }"
                ></div>
              </div>
            </div>
            <div class="metric-trend">
              <span :class="getTrendClass(systemOverview.memory_trend)">
                {{ getTrendIcon(systemOverview.memory_trend) }}
              </span>
              <span>{{ systemOverview.memory_trend }}%</span>
            </div>
          </div>

          <div class="metric-card">
            <div class="metric-header">
              <span class="metric-icon">💾</span>
              <span class="metric-title">磁盘使用率</span>
            </div>
            <div class="metric-value">
              <span class="value">{{ systemOverview.disk_usage }}%</span>
              <div class="progress-bar">
                <div
                  class="progress-fill"
                  :class="getUsageClass(systemOverview.disk_usage)"
                  :style="{ width: `${systemOverview.disk_usage}%` }"
                ></div>
              </div>
            </div>
            <div class="metric-trend">
              <span :class="getTrendClass(systemOverview.disk_trend)">
                {{ getTrendIcon(systemOverview.disk_trend) }}
              </span>
              <span>{{ systemOverview.disk_trend }}%</span>
            </div>
          </div>

          <div class="metric-card">
            <div class="metric-header">
              <span class="metric-icon">🌐</span>
              <span class="metric-title">网络流量</span>
            </div>
            <div class="metric-value">
              <span class="value">{{ formatBytes(systemOverview.network_in) }}/s</span>
              <div class="network-info">
                <span>↓ {{ formatBytes(systemOverview.network_in) }}/s</span>
                <span>↑ {{ formatBytes(systemOverview.network_out) }}/s</span>
              </div>
            </div>
            <div class="metric-trend">
              <span class="trend-indicator">
                {{ systemOverview.network_connections }} 连接
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 性能指标图表 -->
      <div class="charts-section">
        <div class="chart-container">
          <div class="chart-header">
            <h3>性能指标趋势</h3>
            <div class="chart-controls">
              <select v-model="timeRange" class="time-range-select">
                <option value="1h">最近1小时</option>
                <option value="6h">最近6小时</option>
                <option value="24h">最近24小时</option>
                <option value="7d">最近7天</option>
              </select>
            </div>
          </div>
          <div class="chart-content">
            <div class="performance-chart">
              <canvas ref="performanceChart" width="800" height="300"></canvas>
            </div>
          </div>
        </div>
      </div>

      <!-- 服务状态 -->
      <div class="services-section">
        <h3>服务状态</h3>
        <div class="services-grid">
          <div
            v-for="service in services"
            :key="service.name"
            class="service-card"
            :class="{
              'service-healthy': service.status === 'healthy',
              'service-warning': service.status === 'warning',
              'service-error': service.status === 'error'
            }"
          >
            <div class="service-header">
              <span class="service-name">{{ service.name }}</span>
              <span class="service-status" :class="service.status">
                {{ getStatusText(service.status) }}
              </span>
            </div>
            <div class="service-metrics">
              <div class="service-metric">
                <span class="metric-label">响应时间:</span>
                <span class="metric-value">{{ service.response_time }}ms</span>
              </div>
              <div class="service-metric">
                <span class="metric-label">可用性:</span>
                <span class="metric-value">{{ service.uptime }}%</span>
              </div>
              <div class="service-metric">
                <span class="metric-label">请求/秒:</span>
                <span class="metric-value">{{ service.requests_per_sec }}</span>
              </div>
            </div>
            <div class="service-actions">
              <button @click="restartService(service.name)" class="btn btn-sm btn-outline">
                重启
              </button>
              <button @click="viewServiceLogs(service.name)" class="btn btn-sm btn-outline">
                日志
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 告警信息 -->
      <div class="alerts-section">
        <div class="section-header">
          <h3>告警信息</h3>
          <div class="alert-filters">
            <select v-model="alertSeverity" class="severity-filter">
              <option value="">全部级别</option>
              <option value="critical">严重</option>
              <option value="warning">警告</option>
              <option value="info">信息</option>
            </select>
            <button @click="showCreateAlertModal = true" class="btn btn-sm btn-primary">
              新建告警规则
            </button>
          </div>
        </div>
        <div class="alerts-list">
          <div
            v-for="alert in filteredAlerts"
            :key="alert.id"
            class="alert-item"
            :class="alert.severity"
          >
            <div class="alert-header">
              <div class="alert-title">{{ alert.title }}</div>
              <div class="alert-time">{{ formatTime(alert.timestamp) }}</div>
            </div>
            <div class="alert-message">{{ alert.message }}</div>
            <div class="alert-actions">
              <button @click="acknowledgeAlert(alert.id)" class="btn btn-xs btn-outline">
                确认
              </button>
              <button @click="dismissAlert(alert.id)" class="btn btn-xs btn-outline">
                忽略
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 日志查看器 -->
      <div class="logs-section">
        <div class="section-header">
          <h3>系统日志</h3>
          <div class="log-controls">
            <select v-model="logLevel" class="log-level-select">
              <option value="">全部级别</option>
              <option value="error">错误</option>
              <option value="warning">警告</option>
              <option value="info">信息</option>
              <option value="debug">调试</option>
            </select>
            <select v-model="logSource" class="log-source-select">
              <option value="">全部来源</option>
              <option value="api">API服务</option>
              <option value="database">数据库</option>
              <option value="cache">缓存</option>
              <option value="queue">消息队列</option>
            </select>
            <button @click="exportLogs" class="btn btn-sm btn-outline">
              导出日志
            </button>
          </div>
        </div>
        <div class="logs-container">
          <div class="logs-viewer">
            <div
              v-for="log in filteredLogs"
              :key="log.id"
              class="log-entry"
              :class="log.level"
            >
              <div class="log-timestamp">{{ formatTimestamp(log.timestamp) }}</div>
              <div class="log-level">{{ log.level.toUpperCase() }}</div>
              <div class="log-source">{{ log.source }}</div>
              <div class="log-message">{{ log.message }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建告警规则模态框 -->
    <div v-if="showCreateAlertModal" class="modal-overlay" @click="closeCreateAlertModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>创建告警规则</h3>
          <button @click="closeCreateAlertModal" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>规则名称</label>
            <input v-model="alertRule.name" type="text" class="form-input" placeholder="输入规则名称" />
          </div>

          <div class="form-group">
            <label>监控指标</label>
            <select v-model="alertRule.metric" class="form-select">
              <option value="">选择监控指标</option>
              <option value="cpu_usage">CPU使用率</option>
              <option value="memory_usage">内存使用率</option>
              <option value="disk_usage">磁盘使用率</option>
              <option value="response_time">响应时间</option>
              <option value="error_rate">错误率</option>
            </select>
          </div>

          <div class="form-group">
            <label>条件</label>
            <div class="condition-row">
              <select v-model="alertRule.operator" class="form-select">
                <option value=">">大于</option>
                <option value="<">小于</option>
                <option value=">=">大于等于</option>
                <option value="<=">小于等于</option>
                <option value="==">等于</option>
              </select>
              <input v-model="alertRule.threshold" type="number" class="form-input" placeholder="阈值" />
              <span class="condition-unit">%</span>
            </div>
          </div>

          <div class="form-group">
            <label>告警级别</label>
            <select v-model="alertRule.severity" class="form-select">
              <option value="info">信息</option>
              <option value="warning">警告</option>
              <option value="critical">严重</option>
            </select>
          </div>

          <div class="form-group">
            <label>通知方式</label>
            <div class="notification-methods">
              <label class="checkbox-label">
                <input type="checkbox" v-model="alertRule.notify_email" />
                邮件通知
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="alertRule.notify_webhook" />
                Webhook通知
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="alertRule.notify_slack" />
                Slack通知
              </label>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeCreateAlertModal" class="btn btn-outline">取消</button>
          <button @click="createAlertRule" class="btn btn-primary" :disabled="!canCreateAlert">
            创建规则
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

// 响应式数据
const refreshing = ref(false)
const autoRefresh = ref(true)
const refreshInterval = ref(10000)
const timeRange = ref('1h')
const alertSeverity = ref('')
const logLevel = ref('')
const logSource = ref('')

// 模态框状态
const showCreateAlertModal = ref(false)

// 告警规则表单
const alertRule = ref({
  name: '',
  metric: '',
  operator: '>',
  threshold: '',
  severity: 'warning',
  notify_email: false,
  notify_webhook: false,
  notify_slack: false
})

// 系统概览数据
const systemOverview = ref({
  cpu_usage: 65,
  cpu_trend: 2.3,
  memory_usage: 78,
  memory_trend: -1.2,
  disk_usage: 45,
  disk_trend: 0.5,
  network_in: 1048576, // 1MB/s
  network_out: 524288,  // 512KB/s
  network_connections: 156
})

// 服务状态数据
const services = ref([
  {
    name: 'API服务',
    status: 'healthy',
    response_time: 120,
    uptime: 99.9,
    requests_per_sec: 245
  },
  {
    name: '数据库',
    status: 'healthy',
    response_time: 15,
    uptime: 99.99,
    requests_per_sec: 1250
  },
  {
    name: 'Redis缓存',
    status: 'warning',
    response_time: 2,
    uptime: 98.5,
    requests_per_sec: 3200
  },
  {
    name: '消息队列',
    status: 'healthy',
    response_time: 8,
    uptime: 99.8,
    requests_per_sec: 180
  },
  {
    name: '文件存储',
    status: 'error',
    response_time: 5000,
    uptime: 85.2,
    requests_per_sec: 45
  }
])

// 告警数据
const alerts = ref([
  {
    id: 1,
    title: '文件存储服务响应超时',
    message: '文件存储服务响应时间超过5秒，可能影响文件上传下载功能',
    severity: 'critical',
    timestamp: new Date(Date.now() - 1000 * 60 * 5),
    acknowledged: false
  },
  {
    id: 2,
    title: 'Redis缓存内存使用率过高',
    message: 'Redis缓存内存使用率达到85%，建议清理过期数据或扩容',
    severity: 'warning',
    timestamp: new Date(Date.now() - 1000 * 60 * 15),
    acknowledged: false
  },
  {
    id: 3,
    title: 'API服务QPS异常',
    message: 'API服务请求量突增，当前QPS为245，正常值为150左右',
    severity: 'info',
    timestamp: new Date(Date.now() - 1000 * 60 * 30),
    acknowledged: true
  }
])

// 日志数据
const logs = ref([
  {
    id: 1,
    timestamp: new Date(Date.now() - 1000 * 60 * 2),
    level: 'error',
    source: 'api',
    message: 'File storage service timeout after 5000ms'
  },
  {
    id: 2,
    timestamp: new Date(Date.now() - 1000 * 60 * 5),
    level: 'warning',
    source: 'cache',
    message: 'Redis memory usage reached 85%'
  },
  {
    id: 3,
    timestamp: new Date(Date.now() - 1000 * 60 * 8),
    level: 'info',
    source: 'api',
    message: 'User login successful: user@example.com'
  },
  {
    id: 4,
    timestamp: new Date(Date.now() - 1000 * 60 * 12),
    level: 'debug',
    source: 'database',
    message: 'Query executed in 15ms: SELECT * FROM users WHERE id = ?'
  },
  {
    id: 5,
    timestamp: new Date(Date.now() - 1000 * 60 * 15),
    level: 'error',
    source: 'queue',
    message: 'Failed to process message: Invalid message format'
  }
])

// 定时器
let refreshTimer = null

// 计算属性
const filteredAlerts = computed(() => {
  if (!alertSeverity.value) return alerts.value
  return alerts.value.filter(alert => alert.severity === alertSeverity.value)
})

const filteredLogs = computed(() => {
  let filtered = logs.value

  if (logLevel.value) {
    filtered = filtered.filter(log => log.level === logLevel.value)
  }

  if (logSource.value) {
    filtered = filtered.filter(log => log.source === logSource.value)
  }

  return filtered
})

const canCreateAlert = computed(() => {
  return alertRule.value.name.trim() &&
         alertRule.value.metric &&
         alertRule.value.threshold
})

// 方法
const refreshAllData = async () => {
  refreshing.value = true
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))

    // 更新系统概览数据
    systemOverview.value = {
      ...systemOverview.value,
      cpu_usage: Math.floor(Math.random() * 30) + 50,
      memory_usage: Math.floor(Math.random() * 20) + 70,
      disk_usage: Math.floor(Math.random() * 10) + 40,
      network_in: Math.floor(Math.random() * 2048576) + 524288,
      network_out: Math.floor(Math.random() * 1048576) + 262144,
      network_connections: Math.floor(Math.random() * 100) + 100
    }

    // 更新服务状态
    services.value.forEach(service => {
      service.response_time = Math.floor(Math.random() * 200) + 50
      service.requests_per_sec = Math.floor(Math.random() * 500) + 100
    })
  } catch (error) {
    console.error('刷新数据失败:', error)
  } finally {
    refreshing.value = false
  }
}

const getUsageClass = (usage) => {
  if (usage >= 90) return 'danger'
  if (usage >= 75) return 'warning'
  return 'normal'
}

const getTrendClass = (trend) => {
  if (trend > 5) return 'trend-up'
  if (trend < -5) return 'trend-down'
  return 'trend-stable'
}

const getTrendIcon = (trend) => {
  if (trend > 5) return '📈'
  if (trend < -5) return '📉'
  return '➡️'
}

const getStatusText = (status) => {
  const statusMap = {
    healthy: '正常',
    warning: '警告',
    error: '错误'
  }
  return statusMap[status] || status
}

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatTime = (date) => {
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  return date.toLocaleDateString('zh-CN')
}

const formatTimestamp = (date) => {
  return date.toLocaleString('zh-CN')
}

const restartService = async (serviceName) => {
  if (confirm(`确定要重启 ${serviceName} 吗？`)) {
    console.log('重启服务:', serviceName)
    // 模拟重启
    const service = services.value.find(s => s.name === serviceName)
    if (service) {
      service.status = 'warning'
      setTimeout(() => {
        service.status = 'healthy'
      }, 3000)
    }
  }
}

const viewServiceLogs = (serviceName) => {
  console.log('查看服务日志:', serviceName)
  logSource.value = serviceName.toLowerCase().replace('服务', '')
}

const acknowledgeAlert = (alertId) => {
  const alert = alerts.value.find(a => a.id === alertId)
  if (alert) {
    alert.acknowledged = true
  }
}

const dismissAlert = (alertId) => {
  const index = alerts.value.findIndex(a => a.id === alertId)
  if (index > -1) {
    alerts.value.splice(index, 1)
  }
}

const exportLogs = () => {
  console.log('导出日志')
  // 模拟导出功能
  const logText = filteredLogs.value.map(log =>
    `${formatTimestamp(log.timestamp)} [${log.level.toUpperCase()}] ${log.source}: ${log.message}`
  ).join('\n')

  const blob = new Blob([logText], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `system_logs_${new Date().toISOString().slice(0, 10)}.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const createAlertRule = () => {
  console.log('创建告警规则:', alertRule.value)
  closeCreateAlertModal()
}

const closeCreateAlertModal = () => {
  showCreateAlertModal.value = false
  alertRule.value = {
    name: '',
    metric: '',
    operator: '>',
    threshold: '',
    severity: 'warning',
    notify_email: false,
    notify_webhook: false,
    notify_slack: false
  }
}

// 设置自动刷新
const setupAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }

  if (autoRefresh.value) {
    refreshTimer = setInterval(() => {
      refreshAllData()
    }, refreshInterval.value)
  }
}

// 监听自动刷新设置变化
watch([autoRefresh, refreshInterval], () => {
  setupAutoRefresh()
})

// 生命周期
onMounted(() => {
  refreshAllData()
  setupAutoRefresh()
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.monitoring-panel {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}

.monitoring-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  background: white;
  border-bottom: 1px solid #e1e8ed;
}

.monitoring-header h2 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.5rem;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.auto-refresh {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.refresh-interval {
  padding: 0.25rem 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.8rem;
}

.monitoring-content {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.overview-section,
.charts-section,
.services-section,
.alerts-section,
.logs-section {
  margin-bottom: 2rem;
}

.overview-section h3,
.charts-section h3,
.services-section h3 {
  margin: 0 0 1.5rem 0;
  color: #2c3e50;
  font-size: 1.2rem;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

.metric-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.metric-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.metric-icon {
  font-size: 1.5rem;
}

.metric-title {
  font-weight: 600;
  color: #2c3e50;
}

.metric-value {
  margin-bottom: 1rem;
}

.value {
  font-size: 2rem;
  font-weight: bold;
  color: #2c3e50;
  display: block;
  margin-bottom: 0.5rem;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.progress-fill.normal {
  background: #28a745;
}

.progress-fill.warning {
  background: #ffc107;
}

.progress-fill.danger {
  background: #dc3545;
}

.metric-trend {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.trend-up {
  color: #dc3545;
}

.trend-down {
  color: #28a745;
}

.trend-stable {
  color: #6c757d;
}

.network-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: #5a6c7d;
  margin-top: 0.5rem;
}

.chart-container {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.time-range-select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.performance-chart {
  width: 100%;
  height: 300px;
}

.services-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem;
}

.service-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-left: 4px solid #e9ecef;
}

.service-card.service-healthy {
  border-left-color: #28a745;
}

.service-card.service-warning {
  border-left-color: #ffc107;
}

.service-card.service-error {
  border-left-color: #dc3545;
}

.service-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.service-name {
  font-weight: 600;
  color: #2c3e50;
}

.service-status {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}

.service-status.healthy {
  background: #d4edda;
  color: #155724;
}

.service-status.warning {
  background: #fff3cd;
  color: #856404;
}

.service-status.error {
  background: #f8d7da;
  color: #721c24;
}

.service-metrics {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.service-metric {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
}

.metric-label {
  color: #5a6c7d;
}

.service-actions {
  display: flex;
  gap: 0.5rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.2rem;
}

.alert-filters,
.log-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.severity-filter,
.log-level-select,
.log-source-select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.alert-item {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  border-left: 4px solid #e9ecef;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.alert-item.critical {
  border-left-color: #dc3545;
}

.alert-item.warning {
  border-left-color: #ffc107;
}

.alert-item.info {
  border-left-color: #17a2b8;
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.5rem;
}

.alert-title {
  font-weight: 600;
  color: #2c3e50;
}

.alert-time {
  font-size: 0.8rem;
  color: #5a6c7d;
}

.alert-message {
  color: #5a6c7d;
  margin-bottom: 1rem;
  line-height: 1.5;
}

.alert-actions {
  display: flex;
  gap: 0.5rem;
}

.logs-container {
  background: white;
  border-radius: 12px;
  padding: 1rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.logs-viewer {
  max-height: 400px;
  overflow-y: auto;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.9rem;
}

.log-entry {
  display: flex;
  gap: 1rem;
  padding: 0.5rem;
  border-bottom: 1px solid #f1f3f4;
}

.log-entry:last-child {
  border-bottom: none;
}

.log-entry.error {
  background: #fff5f5;
}

.log-entry.warning {
  background: #fffbf0;
}

.log-entry.info {
  background: #f0f9ff;
}

.log-entry.debug {
  background: #f8f9fa;
}

.log-timestamp {
  color: #5a6c7d;
  min-width: 150px;
}

.log-level {
  min-width: 60px;
  font-weight: 600;
}

.log-level.ERROR {
  color: #dc3545;
}

.log-level.WARNING {
  color: #ffc107;
}

.log-level.INFO {
  color: #17a2b8;
}

.log-level.DEBUG {
  color: #6c757d;
}

.log-source {
  color: #667eea;
  min-width: 100px;
}

.log-message {
  flex: 1;
  color: #2c3e50;
}

/* 按钮样式 */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  border: none;
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-sm {
  padding: 0.25rem 0.75rem;
  font-size: 0.8rem;
}

.btn-xs {
  padding: 0.125rem 0.5rem;
  font-size: 0.75rem;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #5a6fd8;
}

.btn-outline {
  background: transparent;
  color: #667eea;
  border: 1px solid #667eea;
}

.btn-outline:hover:not(:disabled) {
  background: #667eea;
  color: white;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e1e8ed;
}

.modal-header h3 {
  margin: 0;
  color: #2c3e50;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #5a6c7d;
  padding: 0.25rem;
  border-radius: 4px;
}

.btn-close:hover {
  background: #f1f3f4;
}

.modal-body {
  padding: 1.5rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid #e1e8ed;
}

/* 表单样式 */
.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #2c3e50;
}

.form-input,
.form-select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.9rem;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

.condition-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.condition-row .form-select {
  flex: 1;
}

.condition-row .form-input {
  flex: 2;
}

.condition-unit {
  color: #5a6c7d;
  font-size: 0.9rem;
}

.notification-methods {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .overview-grid {
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  }

  .services-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .monitoring-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .header-actions {
    justify-content: center;
  }

  .monitoring-content {
    padding: 1rem;
  }

  .overview-grid {
    grid-template-columns: 1fr;
  }

  .chart-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .section-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .alert-filters,
  .log-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .log-entry {
    flex-direction: column;
    gap: 0.25rem;
  }

  .modal-content {
    width: 95%;
    margin: 1rem;
  }
}

@media (max-width: 480px) {
  .service-header {
    flex-direction: column;
    gap: 0.5rem;
    align-items: stretch;
  }

  .service-metrics {
    gap: 0.75rem;
  }

  .alert-header {
    flex-direction: column;
    gap: 0.5rem;
    align-items: stretch;
  }

  .alert-actions {
    justify-content: center;
  }
}
</style>