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
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  position: relative;
}

.documents-page::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(circle at 20% 80%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.1) 0%, transparent 50%);
  pointer-events: none;
}

.page-header {
  text-align: center;
  margin-bottom: 3rem;
  position: relative;
  z-index: 1;
}

.page-header h1 {
  font-size: 2.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 1rem;
}

.page-header p {
  font-size: 1.2rem;
  color: #64748b;
  font-weight: 500;
}

.documents-container {
  max-width: 1200px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
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