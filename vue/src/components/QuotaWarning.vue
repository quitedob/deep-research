<template>
  <div v-if="shouldShow" :class="['quota-warning', severityClass]">
    <div class="warning-content">
      <div class="warning-icon">{{ icon }}</div>
      <div class="warning-text">
        <div class="warning-title">{{ title }}</div>
        <div class="warning-message">{{ message }}</div>
        <div class="warning-details">
          已使用: {{ quota.used }} / {{ quota.limit }} ({{ quota.percentage_used.toFixed(0) }}%)
        </div>
      </div>
      <button v-if="quota.is_exceeded" @click="handleUpgrade" class="upgrade-btn">
        升级订阅
      </button>
      <button @click="dismiss" class="close-btn">×</button>
    </div>
    <div class="progress-bar">
      <div class="progress-fill" :style="{ width: progressWidth }"></div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'QuotaWarning',
  data() {
    return {
      quota: null,
      dismissed: false,
      checkInterval: null
    };
  },
  computed: {
    shouldShow() {
      if (!this.quota || this.dismissed) return false;
      // 显示条件：配额超过 80% 或已超限
      return this.quota.percentage_used >= 80 || this.quota.is_exceeded;
    },
    
    severityClass() {
      if (!this.quota) return '';
      if (this.quota.is_exceeded) return 'severity-error';
      if (this.quota.percentage_used >= 90) return 'severity-warning';
      return 'severity-info';
    },
    
    icon() {
      if (!this.quota) return '';
      if (this.quota.is_exceeded) return '🚫';
      if (this.quota.percentage_used >= 90) return '⚠️';
      return 'ℹ️';
    },
    
    title() {
      if (!this.quota) return '';
      if (this.quota.is_exceeded) return '配额已用完';
      if (this.quota.percentage_used >= 90) return '配额即将用完';
      return '配额提醒';
    },
    
    message() {
      if (!this.quota) return '';
      return this.quota.warning_message || '您的配额使用情况';
    },
    
    progressWidth() {
      if (!this.quota) return '0%';
      return Math.min(100, this.quota.percentage_used) + '%';
    }
  },
  async mounted() {
    await this.checkQuota();
    // 每 30 秒检查一次配额
    this.checkInterval = setInterval(() => {
      this.checkQuota();
    }, 30000);
  },
  beforeUnmount() {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
    }
  },
  methods: {
    async checkQuota() {
      try {
        const response = await axios.get('/api/quota/status');
        this.quota = response.data;
        
        // 如果配额已超限，触发全局事件
        if (this.quota.is_exceeded) {
          this.$emit('quota-exceeded', this.quota);
          // 可以在这里禁用某些功能
          this.disableFeatures();
        }
      } catch (error) {
        console.error('检查配额失败:', error);
      }
    },
    
    disableFeatures() {
      // 禁用对话和研究功能
      // 可以通过 Vuex 或事件总线通知其他组件
      if (window.EventBus) {
        window.EventBus.emit('disable-chat');
        window.EventBus.emit('disable-research');
      }
    },
    
    handleUpgrade() {
      // 跳转到订阅页面
      this.$router.push('/admin?tab=subscription');
    },
    
    dismiss() {
      this.dismissed = true;
      // 5 分钟后重新显示
      setTimeout(() => {
        this.dismissed = false;
      }, 300000);
    }
  }
};
</script>

<style scoped>
.quota-warning {
  position: fixed;
  top: 20px;
  right: 20px;
  width: 400px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  z-index: 1000;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.warning-content {
  padding: 16px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.warning-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.warning-text {
  flex: 1;
}

.warning-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
  color: #333;
}

.warning-message {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.warning-details {
  font-size: 12px;
  color: #999;
  font-family: monospace;
}

.upgrade-btn {
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
}

.upgrade-btn:hover {
  background: #0056b3;
}

.close-btn {
  padding: 4px 8px;
  background: none;
  border: none;
  font-size: 24px;
  color: #999;
  cursor: pointer;
  line-height: 1;
}

.close-btn:hover {
  color: #333;
}

.progress-bar {
  height: 4px;
  background: #f0f0f0;
  border-radius: 0 0 8px 8px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  transition: width 0.3s ease;
}

/* 严重程度样式 */
.severity-info {
  border-left: 4px solid #17a2b8;
}

.severity-info .progress-fill {
  background: #17a2b8;
}

.severity-warning {
  border-left: 4px solid #ffc107;
}

.severity-warning .progress-fill {
  background: #ffc107;
}

.severity-error {
  border-left: 4px solid #dc3545;
}

.severity-error .progress-fill {
  background: #dc3545;
}

/* 响应式 */
@media (max-width: 768px) {
  .quota-warning {
    width: calc(100% - 40px);
    right: 20px;
  }
}
</style>
