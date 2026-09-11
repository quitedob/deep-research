<template>
  <div class="research-report-container">
    <div class="report-header">
      <span class="header-icon">📄</span>
      <h3>{{ report.title }}</h3>
    </div>
    <div class="report-content">
      <p class="report-summary">{{ report.summary }}</p>
      <div v-for="(section, index) in report.sections" :key="index" class="report-section">
        <h4>{{ section.title }}</h4>
        <p>{{ section.content }}</p>
      </div>
    </div>
    <div class="report-footer">
      <span>报告生成于 {{ report.timestamp }}</span>
    </div>
  </div>
</template>

<script setup>
// 定义组件的 props
defineProps({
  report: {
    type: Object,
    required: true,
    // 简化注释：report prop 必须是一个对象
  },
});
</script>

<style scoped>
.research-report-container {
  background: var(--card-bg); /* 使用卡片背景 */
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 25px;
  animation: fadeIn 0.5s ease;
  box-shadow: 0 4px 15px rgba(0,0,0,0.05);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(15px); }
  to { opacity: 1; transform: translateY(0); }
}

.report-header {
  display: flex;
  align-items: center;
  gap: 15px;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 15px;
  margin-bottom: 20px;
}
.header-icon {
  font-size: 24px;
}
.report-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.report-summary {
  font-size: 16px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 25px;
}

.report-section {
  margin-bottom: 20px;
}
.report-section h4 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 10px;
  color: var(--text-primary);
}
.report-section p {
  font-size: 15px;
  line-height: 1.7;
  color: var(--text-primary);
  margin: 0;
}

.report-footer {
  margin-top: 25px;
  padding-top: 15px;
  border-top: 1px solid var(--border-color);
  text-align: right;
  font-size: 12px;
  color: var(--text-secondary);
}
</style>