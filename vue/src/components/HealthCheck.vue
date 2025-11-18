<template>
  <div class="health-check">
    <div class="health-status" :class="status">
      <div class="status-icon">
        <i :class="statusIcon"></i>
      </div>
      <div class="status-info">
        <h4>{{ statusText }}</h4>
        <p v-if="errorMessage">{{ errorMessage }}</p>
        <p v-else-if="lastCheck">最后检查: {{ formatTime(lastCheck) }}</p>
      </div>
      <button
        class="refresh-btn"
        @click="checkHealth"
        :disabled="checking"
      >
        <i class="icon-refresh" :class="{ spinning: checking }"></i>
      </button>
    </div>

    <div v-if="details && showDetails" class="health-details">
      <div class="detail-item">
        <span class="label">后端服务:</span>
        <span class="value" :class="{ healthy: details.services?.database === 'healthy', unhealthy: details.services?.database === 'unhealthy' }">
          {{ getServiceStatus(details.services?.database) }}
        </span>
      </div>
      <div class="detail-item">
        <span class="label">Redis缓存:</span>
        <span class="value" :class="{ healthy: details.services?.redis === 'healthy', unhealthy: details.services?.redis === 'unhealthy' }">
          {{ getServiceStatus(details.services?.redis) }}
        </span>
      </div>
      <div class="detail-item">
        <span class="label">响应时间:</span>
        <span class="value">{{ details.performance?.avg_request_duration ? details.performance.avg_request_duration.toFixed(2) + 's' : 'N/A' }}</span>
      </div>
    </div>

    <button
      v-if="details"
      class="toggle-details-btn"
      @click="showDetails = !showDetails"
    >
      {{ showDetails ? '隐藏详情' : '显示详情' }}
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { healthAPI } from '@/services/api.js'

// Props
const props = defineProps({
  autoCheck: {
    type: Boolean,
    default: true
  },
  checkInterval: {
    type: Number,
    default: 30000  // 30秒
  }
})

// Emits
const emit = defineEmits(['status-changed', 'health-checked'])

// Reactive data
const status = ref('unknown')  // 'healthy', 'unhealthy', 'unknown'
const statusText = ref('检查中...')
const errorMessage = ref('')
const checking = ref(false)
const lastCheck = ref(null)
const details = ref(null)
const showDetails = ref(false)
const checkTimer = ref(null)

// Computed
const statusIcon = computed(() => {
  switch (status.value) {
    case 'healthy': return 'icon-check-circle'
    case 'unhealthy': return 'icon-error-circle'
    default: return 'icon-question-circle'
  }
})

// Methods
const getServiceStatus = (serviceStatus) => {
  switch (serviceStatus) {
    case 'healthy': return '正常'
    case 'unhealthy': return '异常'
    default: return '未知'
  }
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const checkHealth = async () => {
  checking.value = true
  errorMessage.value = ''

  try {
    const result = await healthAPI.checkHealth()

    if (result.status === 'healthy') {
      status.value = 'healthy'
      statusText.value = '服务正常'
    } else {
      status.value = 'unhealthy'
      statusText.value = '服务异常'
    }

    lastCheck.value = Date.now()

    // 获取详细信息
    try {
      const detailedResult = await healthAPI.getDetailedHealth()
      details.value = detailedResult
    } catch (detailError) {
      console.warn('获取健康详情失败:', detailError)
    }

    emit('status-changed', {
      status: status.value,
      details: details.value
    })

  } catch (error) {
    console.error('健康检查失败:', error)
    status.value = 'unhealthy'
    statusText.value = '连接失败'
    errorMessage.value = error.message || '无法连接到服务器'
    lastCheck.value = Date.now()

    emit('status-changed', {
      status: status.value,
      error: error.message
    })
  } finally {
    checking.value = false
    emit('health-checked', {
      status: status.value,
      timestamp: lastCheck.value
    })
  }
}

const startAutoCheck = () => {
  if (props.autoCheck && props.checkInterval > 0) {
    checkTimer.value = setInterval(checkHealth, props.checkInterval)
  }
}

const stopAutoCheck = () => {
  if (checkTimer.value) {
    clearInterval(checkTimer.value)
    checkTimer.value = null
  }
}

// Lifecycle
onMounted(async () => {
  await checkHealth()
  startAutoCheck()
})

// Cleanup
onUnmounted(() => {
  stopAutoCheck()
})

// Watch for prop changes
watch(() => props.autoCheck, (newValue) => {
  if (newValue) {
    startAutoCheck()
  } else {
    stopAutoCheck()
  }
})

watch(() => props.checkInterval, () => {
  stopAutoCheck()
  startAutoCheck()
})
</script>

<style scoped>
.health-check {
  background: var(--secondary-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
}

.health-status {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  gap: 12px;
}

.health-status.healthy {
  background: rgba(34, 197, 94, 0.1);
  border-left: 3px solid var(--success-color);
}

.health-status.unhealthy {
  background: rgba(239, 68, 68, 0.1);
  border-left: 3px solid var(--error-color);
}

.health-status.unknown {
  background: rgba(156, 163, 175, 0.1);
  border-left: 3px solid var(--text-secondary);
}

.status-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--accent-color);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
}

.health-status.healthy .status-icon {
  background: var(--success-color);
}

.health-status.unhealthy .status-icon {
  background: var(--error-color);
}

.health-status.unknown .status-icon {
  background: var(--text-secondary);
}

.status-info {
  flex: 1;
}

.status-info h4 {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.status-info p {
  margin: 0;
  font-size: 12px;
  color: var(--text-secondary);
}

.refresh-btn {
  padding: 8px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--primary-bg);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: var(--hover-bg);
}

.refresh-btn:disabled {
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

.health-details {
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
  background: var(--primary-bg);
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color);
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-item .label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.detail-item .value {
  font-size: 12px;
  color: var(--text-primary);
  font-weight: 600;
}

.detail-item .value.healthy {
  color: var(--success-color);
}

.detail-item .value.unhealthy {
  color: var(--error-color);
}

.toggle-details-btn {
  width: 100%;
  padding: 8px 16px;
  border: none;
  border-top: 1px solid var(--border-color);
  background: var(--secondary-bg);
  color: var(--accent-color);
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.toggle-details-btn:hover {
  background: var(--hover-bg);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .health-status {
    padding: 12px 16px;
  }

  .status-icon {
    width: 32px;
    height: 32px;
    font-size: 14px;
  }

  .status-info h4 {
    font-size: 14px;
  }

  .health-details {
    padding: 12px 16px;
  }
}
</style>
