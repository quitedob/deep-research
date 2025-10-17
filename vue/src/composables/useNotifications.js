import { ref, reactive } from 'vue'

// 全局toast状态
const toastComponent = ref(null)
const notifications = ref([])

// 通知队列管理
const notificationQueue = reactive({
  pending: [],
  active: [],
  history: []
})

// 通知配置
const config = reactive({
  maxNotifications: 5,
  defaultDuration: 5000,
  position: 'top-right',
  enableSound: false,
  enableDesktop: false
})

// 声音管理
const sounds = {
  success: 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBTGH0fPTgjMGHm7A7+OZURE',
  error: 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBTGH0fPTgjMGHm7A7+OZURE',
  warning: 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBTGH0fPTgjMGHm7A7+OZURE',
  info: 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBTGH0fPTgjMGHm7A7+OZURE'
}

// 创建通知管理器
class NotificationManager {
  constructor() {
    this.init()
  }

  init() {
    // 请求桌面通知权限
    if ('Notification' in window && config.enableDesktop) {
      Notification.requestPermission()
    }
  }

  // 注册toast组件
  registerToast(component) {
    toastComponent.value = component
  }

  // 播放声音
  playSound(type) {
    if (!config.enableSound) return

    try {
      const audio = new Audio(sounds[type])
      audio.volume = 0.3
      audio.play().catch(() => {
        // 忽略播放错误
      })
    } catch (error) {
      console.warn('Failed to play notification sound:', error)
    }
  }

  // 显示桌面通知
  showDesktopNotification(title, options = {}) {
    if (!('Notification' in window) || Notification.permission !== 'granted') {
      return
    }

    try {
      const notification = new Notification(title, {
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        ...options
      })

      // 自动关闭
      if (options.duration > 0) {
        setTimeout(() => {
          notification.close()
        }, options.duration)
      }

      return notification
    } catch (error) {
      console.warn('Failed to show desktop notification:', error)
    }
  }

  // 添加通知到队列
  addNotification(notification) {
    const id = Date.now() + Math.random()
    const fullNotification = {
      id,
      timestamp: new Date(),
      read: false,
      ...notification
    }

    // 添加到历史记录
    notificationQueue.history.unshift(fullNotification)

    // 限制历史记录数量
    if (notificationQueue.history.length > 100) {
      notificationQueue.history = notificationQueue.history.slice(0, 100)
    }

    // 显示toast
    if (toastComponent.value) {
      toastComponent.value.addToast(fullNotification)
    }

    // 播放声音
    this.playSound(fullNotification.type)

    // 显示桌面通知
    if (fullNotification.desktop !== false) {
      this.showDesktopNotification(
        fullNotification.title || '通知',
        {
          body: fullNotification.message,
          duration: fullNotification.duration || config.defaultDuration
        }
      )
    }

    return id
  }

  // 基础通知方法
  success(message, options = {}) {
    return this.addNotification({
      type: 'success',
      message,
      ...options
    })
  }

  error(message, options = {}) {
    return this.addNotification({
      type: 'error',
      message,
      duration: 0, // 错误通知默认不自动关闭
      ...options
    })
  }

  warning(message, options = {}) {
    return this.addNotification({
      type: 'warning',
      message,
      ...options
    })
  }

  info(message, options = {}) {
    return this.addNotification({
      type: 'info',
      message,
      ...options
    })
  }

  // 带标题的通知
  notify(title, message, options = {}) {
    return this.addNotification({
      title,
      message,
      ...options
    })
  }

  // 确认对话框
  confirm(message, options = {}) {
    return new Promise((resolve) => {
      const id = this.addNotification({
        type: 'info',
        title: options.title || '确认',
        message,
        duration: 0,
        closable: false,
        actions: [
          {
            label: options.confirmText || '确定',
            type: 'primary',
            handler: () => {
              resolve(true)
            }
          },
          {
            label: options.cancelText || '取消',
            handler: () => {
              resolve(false)
            }
          }
        ],
        ...options
      })
    })
  }

  // 进度通知
  progress(message, progress = 0, options = {}) {
    const existingProgress = notifications.value.find(n => n.type === 'progress' && !n.completed)

    if (existingProgress) {
      // 更新现有进度通知
      existingProgress.message = message
      existingProgress.progress = progress

      if (progress >= 100) {
        existingProgress.completed = true
        existingProgress.type = 'success'
        existingProgress.duration = 3000

        setTimeout(() => {
          this.removeNotification(existingProgress.id)
        }, 3000)
      }
    } else {
      // 创建新进度通知
      const notification = {
        type: 'progress',
        message,
        progress,
        completed: false,
        duration: 0,
        ...options
      }

      return this.addNotification(notification)
    }
  }

  // 自定义通知
  custom(notification) {
    return this.addNotification(notification)
  }

  // 移除通知
  removeNotification(id) {
    if (toastComponent.value) {
      toastComponent.value.removeToast(id)
    }
  }

  // 清除所有通知
  clearAll() {
    if (toastComponent.value) {
      toastComponent.value.clearAll()
    }
  }

  // 清除指定类型的通知
  clearByType(type) {
    if (toastComponent.value) {
      toastComponent.value.clearByType(type)
    }
  }

  // 获取未读通知数量
  getUnreadCount() {
    return notifications.value.filter(n => !n.read).length
  }

  // 标记为已读
  markAsRead(id) {
    const notification = notifications.value.find(n => n.id === id)
    if (notification) {
      notification.read = true
    }
  }

  // 标记所有为已读
  markAllAsRead() {
    notifications.value.forEach(n => {
      n.read = true
    })
  }

  // 配置管理
  updateConfig(newConfig) {
    Object.assign(config, newConfig)
  }

  getConfig() {
    return { ...config }
  }

  // 获取通知历史
  getHistory(limit = 50) {
    return notificationQueue.history.slice(0, limit)
  }

  // 搜索通知
  searchHistory(query, filters = {}) {
    let results = notificationQueue.history

    // 文本搜索
    if (query) {
      const searchQuery = query.toLowerCase()
      results = results.filter(n =>
        (n.title && n.title.toLowerCase().includes(searchQuery)) ||
        (n.message && n.message.toLowerCase().includes(searchQuery))
      )
    }

    // 类型过滤
    if (filters.type) {
      results = results.filter(n => n.type === filters.type)
    }

    // 时间过滤
    if (filters.dateFrom) {
      results = results.filter(n => n.timestamp >= filters.dateFrom)
    }

    if (filters.dateTo) {
      results = results.filter(n => n.timestamp <= filters.dateTo)
    }

    return results
  }
}

// 创建全局通知管理器实例
const notificationManager = new NotificationManager()

// Vue组合式函数
export function useNotifications() {
  return {
    // 基础方法
    success: notificationManager.success.bind(notificationManager),
    error: notificationManager.error.bind(notificationManager),
    warning: notificationManager.warning.bind(notificationManager),
    info: notificationManager.info.bind(notificationManager),
    notify: notificationManager.notify.bind(notificationManager),

    // 高级方法
    confirm: notificationManager.confirm.bind(notificationManager),
    progress: notificationManager.progress.bind(notificationManager),
    custom: notificationManager.custom.bind(notificationManager),

    // 管理方法
    remove: notificationManager.removeNotification.bind(notificationManager),
    clearAll: notificationManager.clearAll.bind(notificationManager),
    clearByType: notificationManager.clearByType.bind(notificationManager),

    // 状态方法
    getUnreadCount: notificationManager.getUnreadCount.bind(notificationManager),
    markAsRead: notificationManager.markAsRead.bind(notificationManager),
    markAllAsRead: notificationManager.markAllAsRead.bind(notificationManager),

    // 配置方法
    updateConfig: notificationManager.updateConfig.bind(notificationManager),
    getConfig: notificationManager.getConfig.bind(notificationManager),

    // 历史方法
    getHistory: notificationManager.getHistory.bind(notificationManager),
    searchHistory: notificationManager.searchHistory.bind(notificationManager),

    // 组件注册
    registerToast: notificationManager.registerToast.bind(notificationManager)
  }
}

// 导出通知管理器实例（用于全局访问）
export { notificationManager }

// 默认导出
export default useNotifications