<template>
  <div class="card">
    <h3 class="card-title">{{ title }}</h3>
    <p class="card-description">{{ description }}</p>
  </div>
</template>

<script setup>
// 定义组件的 props
defineProps({
  title: String,
  description: String
})
</script>

<style scoped>
.card {
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.2s;
  height: 120px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.card:hover {
  background-color: var(--hover-bg);
  transform: translateY(-4px); /* 悬停时轻微上浮 */
}

.card-title {
  font-size: 16px;
  font-weight: 500;
  margin: 0 0 8px 0;
  color: var(--text-primary);
}

.card-description {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}
</style>