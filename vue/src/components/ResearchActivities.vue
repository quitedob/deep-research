<template>
  <div class="research-activities-container">
    <div class="activities-header">
      <div class="spinner"></div>
      <h4 class="header-title">正在为您研究...</h4>
    </div>
    <ul class="activities-list">
      <li v-for="(activity, index) in activities" :key="index" :class="['activity-item', activity.status]">
        <div class="status-icon">
          <span v-if="activity.status === 'done'">✅</span>
          <span v-else-if="activity.status === 'loading'">⏳</span>
          <span v-else>⚪️</span>
        </div>
        <div class="activity-content">
          <p class="activity-title">{{ activity.title }}</p>
          <p v-if="activity.detail" class="activity-detail">{{ activity.detail }}</p>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup>
// 定义组件的 props
defineProps({
  activities: {
    type: Array,
    required: true,
    // 简化注释：activities prop 必须是一个数组
  },
});
</script>

<style scoped>
.research-activities-container {
  background: rgba(59, 130, 246, 0.05); /* 使用淡蓝色背景 */
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.activities-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.header-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--button-bg);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.activities-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  transition: opacity 0.3s;
}

/* 根据状态改变样式 */
.activity-item.done {
  opacity: 0.7;
}
.activity-item .status-icon {
  font-size: 16px;
  margin-top: 2px;
}

.activity-content {
  flex: 1;
}

.activity-title {
  margin: 0 0 4px 0;
  font-weight: 500;
  color: var(--text-primary);
}

.activity-detail {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
}
</style>