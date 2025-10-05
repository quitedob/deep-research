<template>
  <div v-if="quota && shouldShow" :class="['quota-display', severityClass]">
    <div class="quota-info">
      <span class="quota-label">配额:</span>
      <span class="quota-value">{{ quota.remaining }}/{{ quota.limit }}</span>
      <span v-if="quota.quota_type === 'hourly'" class="quota-type">(每小时)</span>
      <span v-else class="quota-type">(终身)</span>
    </div>
    <div v-if="quota.is_exceeded" class="quota-exceeded">
      <span>⚠️ 配额已用完</span>
      <button @click="handleUpgrade" class="upgrade-link">升级</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'QuotaDisplay',
  data() {
    return {
      quota: null,
      checkInterval: null
    };
  },
  computed: {
    shouldShow() {
      return this.quota && this.quota.user_role !== 'admin';
    },
    
    severityClass() {
      if (!this.quota) return '';
      if (this.quota.is_exceeded) return 'exceeded';
      if (this.quota.percentage_used >= 90) return 'warning';
      if (this.quota.percentage_used >= 80) return 'info';
      return '';
    }
  },
  async mounted() {
    await this.checkQuota();
    // 每分钟检查一次
    this.checkInterval = setInterval(() => {
      this.checkQuota();
    }, 60000);
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
        
        // 如果配额超限，发出事件
        if (this.quota.is_exceeded) {
          this.$emit('quota-exceeded', this.quota);
        }
      } catch (error) {
        console.error('检查配额失败:', error);
      }
    },
    
    handleUpgrade() {
      this.$router.push('/admin?tab=subscription');
    }
  }
};
</script>

<style scoped>
.quota-display {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: white;
  border-radius: 8px;
  padding: 12px 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  z-index: 999;
  min-width: 200px;
}

.quota-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.quota-label {
  color: #666;
}

.quota-value {
  font-weight: 600;
  color: #333;
}

.quota-type {
  color: #999;
  font-size: 12px;
}

.quota-exceeded {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #eee;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: #dc3545;
}

.upgrade-link {
  padding: 4px 12px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.upgrade-link:hover {
  background: #0056b3;
}

/* 严重程度样式 */
.quota-display.info {
  border-left: 4px solid #17a2b8;
}

.quota-display.warning {
  border-left: 4px solid #ffc107;
}

.quota-display.exceeded {
  border-left: 4px solid #dc3545;
  background: #fff5f5;
}
</style>
