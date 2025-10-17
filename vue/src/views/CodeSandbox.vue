<template>
  <div class="code-sandbox-page">
    <div class="page-header">
      <h1>代码沙盒</h1>
      <p>在安全的隔离环境中执行Python代码</p>
    </div>

    <div class="sandbox-container">
      <div class="sandbox-main">
        <div class="editor-section">
          <CodeSandbox
            @execution-complete="handleExecutionComplete"
            @code-change="handleCodeChange"
          />
        </div>

        <div class="output-section">
          <CodeResult
            :result="currentResult"
            :execution-id="currentExecutionId"
          />
        </div>
      </div>

      <div class="history-section">
        <CodeHistory
          @rerun-code="handleRerunCode"
          @copy-code="handleCopyCode"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import CodeSandbox from '@/components/CodeSandbox.vue'
import CodeResult from '@/components/CodeResult.vue'
import CodeHistory from '@/components/CodeHistory.vue'

// 响应式数据
const currentResult = ref(null)
const currentExecutionId = ref('')
const currentCode = ref('')

// 方法
const handleExecutionComplete = (result) => {
  currentResult.value = result
  currentExecutionId.value = `exec_${Date.now()}`
}

const handleCodeChange = (code) => {
  currentCode.value = code
}

const handleRerunCode = (code) => {
  // 将代码传递给编辑器组件执行
  // 这里可以通过事件总线或状态管理来实现
  console.log('重新执行代码:', code)
}

const handleCopyCode = (code) => {
  navigator.clipboard.writeText(code).then(() => {
    console.log('代码已复制到剪贴板')
  }).catch(error => {
    console.error('复制失败:', error)
  })
}

onMounted(() => {
  console.log('代码沙盒页面加载完成')
})
</script>

<style scoped>
.code-sandbox-page {
  min-height: 100vh;
  background: #f8f9fa;
}

.page-header {
  text-align: center;
  padding: 2rem 1rem 1rem;
  background: white;
  border-bottom: 1px solid #e9ecef;
}

.page-header h1 {
  font-size: 2.5rem;
  color: #333;
  margin-bottom: 0.5rem;
}

.page-header p {
  font-size: 1.2rem;
  color: #666;
  margin: 0;
}

.sandbox-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
}

.sandbox-main {
  display: flex;
  flex: 1;
  min-height: 0;
  background: white;
  border-bottom: 1px solid #e9ecef;
}

.editor-section {
  flex: 1;
  border-right: 1px solid #e9ecef;
}

.output-section {
  width: 400px;
  min-width: 300px;
}

.history-section {
  height: 300px;
  background: white;
  border-top: 1px solid #e9ecef;
}

@media (max-width: 1024px) {
  .sandbox-main {
    flex-direction: column;
  }

  .editor-section {
    border-right: none;
    border-bottom: 1px solid #e9ecef;
  }

  .output-section {
    width: 100%;
    height: 300px;
    min-width: auto;
  }
}

@media (max-width: 768px) {
  .page-header {
    padding: 1.5rem 1rem 0.75rem;
  }

  .page-header h1 {
    font-size: 2rem;
  }

  .page-header p {
    font-size: 1rem;
  }

  .sandbox-container {
    height: calc(100vh - 100px);
  }

  .history-section {
    height: 250px;
  }
}

@media (max-width: 480px) {
  .page-header {
    padding: 1rem 0.75rem 0.5rem;
  }

  .page-header h1 {
    font-size: 1.8rem;
  }

  .sandbox-main {
    height: calc(100vh - 80px);
  }

  .output-section {
    height: 250px;
  }

  .history-section {
    height: 200px;
  }
}
</style>