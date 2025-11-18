<template>
  <teleport to="body">
    <div class="toast-container" :class="positionClass">
      <transition-group name="toast" tag="div">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="toast"
          :class="getToastClass(toast)"
          :style="getToastStyle(toast)"
          @click="handleToastClick(toast)"
          @mouseenter="pauseTimer(toast.id)"
          @mouseleave="resumeTimer(toast.id)"
        >
          <div class="toast-content">
            <div class="toast-icon">
              <span>{{ getIcon(toast.type) }}</span>
            </div>
            <div class="toast-message">
              <h4 v-if="toast.title" class="toast-title">{{ toast.title }}</h4>
              <p class="toast-text">{{ toast.message }}</p>
            </div>
            <button
              v-if="toast.closable !== false"
              @click.stop="removeToast(toast.id)"
              class="toast-close"
            >
              ×
            </button>
          </div>

          <div v-if="toast.progress" class="toast-progress">
            <div
              class="progress-bar"
              :style="{ width: `${toast.progress}%` }"
            ></div>
          </div>

          <div v-if="toast.actions && toast.actions.length > 0" class="toast-actions">
            <button
              v-for="action in toast.actions"
              :key="action.label"
              @click.stop="handleAction(toast, action)"
              class="toast-action"
              :class="action.type || 'default'"
            >
              {{ action.label }}
            </button>
          </div>
        </div>
      </transition-group>
    </div>
  </teleport>
</template>

<script setup>
import { ref, computed } from 'vue'

// Toast状态管理
const toasts = ref([])
const timers = ref(new Map())
const pausedTimers = ref(new Set())

// Props
const props = defineProps({
  position: {
    type: String,
    default: 'top-right',
    validator: (value) => [
      'top-left',
      'top-right',
      'top-center',
      'bottom-left',
      'bottom-right',
      'bottom-center'
    ].includes(value)
  },
  maxToasts: {
    type: Number,
    default: 5
  },
  defaultDuration: {
    type: Number,
    default: 5000
  }
})

// 计算位置类
const positionClass = computed(() => {
  return `position-${props.position}`
})

// 添加toast
const addToast = (options) => {
  const toast = {
    id: Date.now() + Math.random(),
    type: 'info',
    title: '',
    message: '',
    duration: props.defaultDuration,
    closable: true,
    pauseOnHover: true,
    progress: false,
    actions: [],
    onClick: null,
    onClose: null,
    ...options
  }

  // 检查是否超过最大数量
  if (toasts.value.length >= props.maxToasts) {
    const oldestToast = toasts.value[0]
    removeToast(oldestToast.id)
  }

  toasts.value.push(toast)

  // 设置自动关闭定时器
  if (toast.duration > 0) {
    setTimer(toast)
  }

  return toast.id
}

// 设置定时器
const setTimer = (toast) => {
  if (timers.value.has(toast.id)) {
    clearTimeout(timers.value.get(toast.id))
  }

  const timer = setTimeout(() => {
    if (!pausedTimers.value.has(toast.id)) {
      removeToast(toast.id)
    }
  }, toast.duration)

  timers.value.set(toast.id, timer)
}

// 暂停定时器
const pauseTimer = (toastId) => {
  const toast = toasts.value.find(t => t.id === toastId)
  if (toast && toast.pauseOnHover) {
    pausedTimers.value.add(toastId)
  }
}

// 恢复定时器
const resumeTimer = (toastId) => {
  const toast = toasts.value.find(t => t.id === toastId)
  if (toast && toast.pauseOnHover && pausedTimers.value.has(toastId)) {
    pausedTimers.value.delete(toastId)
    setTimer(toast)
  }
}

// 移除toast
const removeToast = (toastId) => {
  const index = toasts.value.findIndex(t => t.id === toastId)
  if (index > -1) {
    const toast = toasts.value[index]

    // 清除定时器
    if (timers.value.has(toastId)) {
      clearTimeout(timers.value.get(toastId))
      timers.value.delete(toastId)
    }

    pausedTimers.value.delete(toastId)

    // 调用关闭回调
    if (toast.onClose) {
      toast.onClose(toast)
    }

    // 移除toast
    toasts.value.splice(index, 1)
  }
}

// 处理toast点击
const handleToastClick = (toast) => {
  if (toast.onClick) {
    toast.onClick(toast)
  }
}

// 处理动作按钮点击
const handleAction = (toast, action) => {
  if (action.handler) {
    action.handler(toast)
  }

  // 如果动作指定了关闭，则关闭toast
  if (action.closeOnClick !== false) {
    removeToast(toast.id)
  }
}

// 获取toast样式类
const getToastClass = (toast) => {
  return `toast-${toast.type}`
}

// 获取toast样式
const getToastStyle = (toast) => {
  return {
    '--toast-color': getToastColor(toast.type),
    '--toast-bg': getToastBg(toast.type)
  }
}

// 获取toast颜色
const getToastColor = (type) => {
  const colors = {
    success: '#28a745',
    error: '#dc3545',
    warning: '#ffc107',
    info: '#17a2b8'
  }
  return colors[type] || colors.info
}

// 获取toast背景色
const getToastBg = (type) => {
  const colors = {
    success: '#d4edda',
    error: '#f8d7da',
    warning: '#fff3cd',
    info: '#d1ecf1'
  }
  return colors[type] || colors.info
}

// 获取图标
const getIcon = (type) => {
  const icons = {
    success: '✅',
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️'
  }
  return icons[type] || icons.info
}

// 便捷方法
const showSuccess = (message, options = {}) => {
  return addToast({ type: 'success', message, ...options })
}

const showError = (message, options = {}) => {
  return addToast({ type: 'error', message, duration: 0, ...options })
}

const showWarning = (message, options = {}) => {
  return addToast({ type: 'warning', message, ...options })
}

const showInfo = (message, options = {}) => {
  return addToast({ type: 'info', message, ...options })
}

// 显示带标题的toast
const showWithTitle = (type, title, message, options = {}) => {
  return addToast({ type, title, message, ...options })
}

// 显示带动作的toast
const showWithActions = (type, message, actions, options = {}) => {
  return addToast({ type, message, actions, ...options })
}

// 显示进度toast
const showProgress = (message, progress, options = {}) => {
  return addToast({
    type: 'info',
    message,
    progress,
    closable: false,
    ...options
  })
}

// 清除所有toast
const clearAll = () => {
  toasts.value.forEach(toast => {
    removeToast(toast.id)
  })
}

// 清除指定类型的toast
const clearByType = (type) => {
  const toastsToRemove = toasts.value.filter(toast => toast.type === type)
  toastsToRemove.forEach(toast => {
    removeToast(toast.id)
  })
}

// 暴露方法给外部使用
defineExpose({
  addToast,
  showSuccess,
  showError,
  showWarning,
  showInfo,
  showWithTitle,
  showWithActions,
  showProgress,
  clearAll,
  clearByType,
  removeToast
})
</script>

<style scoped>
.toast-container {
  position: fixed;
  z-index: 10000;
  pointer-events: none;
}

/* 位置样式 */
.position-top-right {
  top: 20px;
  right: 20px;
}

.position-top-left {
  top: 20px;
  left: 20px;
}

.position-top-center {
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
}

.position-bottom-right {
  bottom: 20px;
  right: 20px;
}

.position-bottom-left {
  bottom: 20px;
  left: 20px;
}

.position-bottom-center {
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
}

/* Toast样式 */
.toast {
  pointer-events: auto;
  margin-bottom: 10px;
  min-width: 300px;
  max-width: 500px;
  background: var(--toast-bg);
  border: 1px solid var(--toast-color);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  transition: all 0.3s ease;
}

.toast:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
}

.toast-content {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
}

.toast-icon {
  flex-shrink: 0;
  font-size: 20px;
  line-height: 1;
  margin-top: 2px;
}

.toast-message {
  flex: 1;
  min-width: 0;
}

.toast-title {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--toast-color);
  line-height: 1.4;
}

.toast-text {
  margin: 0;
  font-size: 14px;
  color: #2c3e50;
  line-height: 1.5;
  word-wrap: break-word;
}

.toast-close {
  flex-shrink: 0;
  background: none;
  border: none;
  font-size: 18px;
  color: #6c757d;
  cursor: pointer;
  padding: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.toast-close:hover {
  background: rgba(0, 0, 0, 0.1);
  color: #2c3e50;
}

/* 进度条 */
.toast-progress {
  height: 3px;
  background: rgba(0, 0, 0, 0.1);
}

.progress-bar {
  height: 100%;
  background: var(--toast-color);
  transition: width 0.3s ease;
}

/* 动作按钮 */
.toast-actions {
  display: flex;
  gap: 8px;
  padding: 0 16px 12px 16px;
}

.toast-action {
  padding: 6px 12px;
  border: 1px solid var(--toast-color);
  border-radius: 4px;
  background: transparent;
  color: var(--toast-color);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.toast-action:hover {
  background: var(--toast-color);
  color: white;
}

.toast-action.primary {
  background: var(--toast-color);
  color: white;
}

.toast-action.primary:hover {
  opacity: 0.8;
}

/* 过渡动画 */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.toast-move {
  transition: transform 0.3s ease;
}

/* 不同位置的进入动画 */
.position-top-left .toast-enter-from,
.position-bottom-left .toast-enter-from {
  transform: translateX(-100%);
}

.position-top-left .toast-leave-to,
.position-bottom-left .toast-leave-to {
  transform: translateX(-100%);
}

.position-top-center .toast-enter-from,
.position-bottom-center .toast-enter-from {
  transform: translateY(-100%);
}

.position-top-center .toast-leave-to,
.position-bottom-center .toast-leave-to {
  transform: translateY(-100%);
}

/* 成功样式 */
.toast-success {
  --toast-color: #28a745;
  --toast-bg: #d4edda;
  border-color: #c3e6cb;
}

/* 错误样式 */
.toast-error {
  --toast-color: #dc3545;
  --toast-bg: #f8d7da;
  border-color: #f5c6cb;
}

/* 警告样式 */
.toast-warning {
  --toast-color: #ffc107;
  --toast-bg: #fff3cd;
  border-color: #ffeaa7;
}

/* 信息样式 */
.toast-info {
  --toast-color: #17a2b8;
  --toast-bg: #d1ecf1;
  border-color: #bee5eb;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .toast-container {
    left: 10px !important;
    right: 10px !important;
    transform: none !important;
  }

  .position-top-right,
  .position-top-left,
  .position-top-center {
    top: 10px;
  }

  .position-bottom-right,
  .position-bottom-left,
  .position-bottom-center {
    bottom: 10px;
  }

  .toast {
    min-width: auto;
    max-width: none;
  }

  .toast-content {
    padding: 12px;
  }

  .toast-title {
    font-size: 13px;
  }

  .toast-text {
    font-size: 13px;
  }

  .toast-actions {
    padding: 0 12px 8px 12px;
  }

  .toast-action {
    font-size: 11px;
    padding: 4px 8px;
  }
}

@media (max-width: 480px) {
  .toast-container {
    left: 5px !important;
    right: 5px !important;
  }

  .position-top-right,
  .position-top-left,
  .position-top-center {
    top: 5px;
  }

  .position-bottom-right,
  .position-bottom-left,
  .position-bottom-center {
    bottom: 5px;
  }

  .toast {
    margin-bottom: 8px;
  }

  .toast-content {
    gap: 8px;
    padding: 10px;
  }

  .toast-icon {
    font-size: 16px;
    margin-top: 1px;
  }

  .toast-close {
    font-size: 16px;
    width: 18px;
    height: 18px;
  }
}
</style>