<template>
  <div class="documents-page">
    <div class="page-header">
      <h1>文档管理</h1>
      <p>上传、处理和分析您的文档</p>
    </div>

    <div class="documents-container">
      <DocumentManager />
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import DocumentManager from '@/components/DocumentManager.vue'

onMounted(() => {
  console.log('文档管理页面加载')
})
</script>

<style scoped>
.documents-page {
  min-height: 100vh;
  padding: 2rem;
  background: #f8f9fa;
}

.page-header {
  text-align: center;
  margin-bottom: 3rem;
}

.page-header h1 {
  font-size: 2.5rem;
  color: #333;
  margin-bottom: 1rem;
}

.page-header p {
  font-size: 1.2rem;
  color: #666;
}

.documents-container {
  max-width: 1200px;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .documents-page {
    padding: 1rem;
  }

  .page-header h1 {
    font-size: 2rem;
  }
}
</style>