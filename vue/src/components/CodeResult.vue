<template>
  <div class="code-result">
    <div class="result-header">
      <div class="result-status" :class="statusClass">
        <span class="status-icon">{{ statusIcon }}</span>
        <span class="status-text">{{ statusText }}</span>
      </div>
      <div class="result-actions">
        <button @click="copyResult" class="btn btn-sm btn-outline" title="复制结果">
          📋
        </button>
        <button @click="downloadResult" class="btn btn-sm btn-outline" title="下载结果">
          💾
        </button>
        <button @click="shareResult" class="btn btn-sm btn-outline" title="分享结果">
          🔗
        </button>
      </div>
    </div>

    <div class="result-content">
      <!-- 执行成功的结果 -->
      <div v-if="result?.success" class="success-result">
        <div v-if="result.output" class="output-section">
          <div class="section-header">
            <h4>标准输出</h4>
            <button @click="toggleSection('output')" class="toggle-btn">
              {{ expandedSections.output ? '▼' : '▶' }}
            </button>
          </div>
          <div v-show="expandedSections.output" class="section-content">
            <pre class="output-text">{{ result.output }}</pre>
            <div class="output-stats">
              <span>行数: {{ result.output.split('\n').length }}</span>
              <span>字符数: {{ result.output.length }}</span>
            </div>
          </div>
        </div>

        <div v-if="result.error" class="error-section">
          <div class="section-header">
            <h4>错误输出</h4>
            <button @click="toggleSection('error')" class="toggle-btn">
              {{ expandedSections.error ? '▼' : '▶' }}
            </button>
          </div>
          <div v-show="expandedSections.error" class="section-content">
            <pre class="error-text">{{ result.error }}</pre>
          </div>
        </div>

        <div v-if="result.variables && Object.keys(result.variables).length > 0" class="variables-section">
          <div class="section-header">
            <h4>变量状态</h4>
            <button @click="toggleSection('variables')" class="toggle-btn">
              {{ expandedSections.variables ? '▼' : '▶' }}
            </button>
          </div>
          <div v-show="expandedSections.variables" class="section-content">
            <div class="variables-grid">
              <div v-for="(value, name) in result.variables" :key="name" class="variable-item">
                <div class="variable-header" @click="toggleVariable(name)">
                  <span class="variable-name">{{ name }}</span>
                  <span class="variable-type">{{ getVariableType(value) }}</span>
                  <span class="toggle-icon">{{ expandedVariables[name] ? '▼' : '▶' }}</span>
                </div>
                <div v-show="expandedVariables[name]" class="variable-value">
                  <pre>{{ formatVariable(value) }}</pre>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="execution-info">
          <div class="info-item">
            <span class="info-label">执行时间:</span>
            <span class="info-value">{{ result.execution_time }}ms</span>
          </div>
          <div class="info-item">
            <span class="info-label">内存使用:</span>
            <span class="info-value">{{ getMemoryUsage() }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">执行ID:</span>
            <span class="info-value">{{ executionId }}</span>
          </div>
        </div>
      </div>

      <!-- 执行失败的结果 -->
      <div v-else-if="result" class="error-result">
        <div class="error-main">
          <div class="error-icon">❌</div>
          <h3>执行失败</h3>
          <p class="error-message">{{ result.error || '未知错误' }}</p>
        </div>

        <div v-if="result.output" class="partial-output">
          <h4>部分输出</h4>
          <pre class="output-text">{{ result.output }}</pre>
        </div>

        <div class="error-details">
          <h4>错误详情</h4>
          <div class="error-info">
            <div class="info-item">
              <span class="info-label">错误类型:</span>
              <span class="info-value">{{ getErrorType(result.error) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">执行时间:</span>
              <span class="info-value">{{ result.execution_time }}ms</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 无结果时的占位符 -->
      <div v-else class="no-result">
        <div class="placeholder-icon">📝</div>
        <p>暂无执行结果</p>
        <p class="placeholder-text">执行代码后结果将显示在这里</p>
      </div>
    </div>

    <!-- 结果分享模态框 -->
    <div v-if="showShareModal" class="modal-overlay" @click="closeShareModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>分享执行结果</h3>
          <button @click="closeShareModal" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div class="share-options">
            <button @click="shareAsText" class="share-option">
              <span class="option-icon">📄</span>
              <div class="option-content">
                <h4>复制为文本</h4>
                <p>将结果复制为纯文本格式</p>
              </div>
            </button>
            <button @click="shareAsJSON" class="share-option">
              <span class="option-icon">📋</span>
              <div class="option-content">
                <h4>复制为JSON</h4>
                <p>将结果复制为JSON格式</p>
              </div>
            </button>
            <button @click="generateShareLink" class="share-option">
              <span class="option-icon">🔗</span>
              <div class="option-content">
                <h4>生成分享链接</h4>
                <p>创建可分享的链接</p>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  result: {
    type: Object,
    default: null
  },
  executionId: {
    type: String,
    default: () => `exec_${Date.now()}`
  }
})

// 响应式数据
const expandedSections = ref({
  output: true,
  error: true,
  variables: true
})

const expandedVariables = ref({})
const showShareModal = ref(false)

// 计算属性
const statusClass = computed(() => {
  if (!props.result) return 'no-result'
  return props.result.success ? 'success' : 'error'
})

const statusIcon = computed(() => {
  if (!props.result) return '⏳'
  return props.result.success ? '✅' : '❌'
})

const statusText = computed(() => {
  if (!props.result) return '等待执行'
  return props.result.success ? '执行成功' : '执行失败'
})

// 监听结果变化，自动展开所有变量
watch(() => props.result?.variables, (variables) => {
  if (variables) {
    expandedVariables.value = Object.keys(variables).reduce((acc, key) => {
      acc[key] = true
      return acc
    }, {})
  }
}, { immediate: true })

// 方法
const toggleSection = (section) => {
  expandedSections.value[section] = !expandedSections.value[section]
}

const toggleVariable = (variableName) => {
  expandedVariables.value[variableName] = !expandedVariables.value[variableName]
}

const getVariableType = (value) => {
  if (value === null) return 'null'
  if (value === undefined) return 'undefined'
  if (Array.isArray(value)) return `Array(${value.length})`
  if (typeof value === 'object') {
    const keys = Object.keys(value)
    return `Object(${keys.length} keys)`
  }
  return typeof value
}

const formatVariable = (value) => {
  if (value === null) return 'null'
  if (value === undefined) return 'undefined'
  if (typeof value === 'string') return `"${value}"`
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value, null, 2)
    } catch {
      return String(value)
    }
  }
  return String(value)
}

const getErrorType = (error) => {
  if (!error) return 'Unknown'

  const errorLower = error.toLowerCase()
  if (errorLower.includes('syntax')) return 'Syntax Error'
  if (errorLower.includes('timeout')) return 'Timeout Error'
  if (errorLower.includes('memory')) return 'Memory Error'
  if (errorLower.includes('import')) return 'Import Error'
  if (errorLower.includes('name')) return 'Name Error'
  if (errorLower.includes('type')) return 'Type Error'
  if (errorLower.includes('value')) return 'Value Error'
  if (errorLower.includes('index')) return 'Index Error'
  if (errorLower.includes('key')) return 'Key Error'
  if (errorLower.includes('attribute')) return 'Attribute Error'

  return 'Runtime Error'
}

const getMemoryUsage = () => {
  // 这里可以从result中获取实际的内存使用信息
  // 暂时返回估算值
  if (!props.result) return 'N/A'

  const variables = props.result.variables || {}
  const estimatedSize = JSON.stringify(variables).length
  return `${(estimatedSize / 1024).toFixed(2)} KB (估算)`
}

const copyResult = async () => {
  if (!props.result) return

  const text = formatResultAsText()
  try {
    await navigator.clipboard.writeText(text)
    // 可以添加成功提示
    console.log('结果已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    // 降级方案
    const textArea = document.createElement('textarea')
    textArea.value = text
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
  }
}

const downloadResult = () => {
  if (!props.result) return

  const content = formatResultAsText()
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `code_result_${props.executionId}.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const shareResult = () => {
  showShareModal.value = true
}

const closeShareModal = () => {
  showShareModal.value = false
}

const shareAsText = () => {
  copyResult()
  closeShareModal()
}

const shareAsJSON = async () => {
  if (!props.result) return

  try {
    const json = JSON.stringify(props.result, null, 2)
    await navigator.clipboard.writeText(json)
    console.log('JSON结果已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
  }
  closeShareModal()
}

const generateShareLink = () => {
  // 这里可以调用API生成分享链接
  console.log('生成分享链接功能待实现')
  closeShareModal()
}

const formatResultAsText = () => {
  if (!props.result) return ''

  const lines = [
    '=== 代码执行结果 ===',
    `执行ID: ${props.executionId}`,
    `状态: ${props.result.success ? '成功' : '失败'}`,
    `执行时间: ${props.result.execution_time}ms`,
    ''
  ]

  if (props.result.success) {
    if (props.result.output) {
      lines.push('=== 标准输出 ===')
      lines.push(props.result.output)
      lines.push('')
    }

    if (props.result.error) {
      lines.push('=== 错误输出 ===')
      lines.push(props.result.error)
      lines.push('')
    }

    if (props.result.variables) {
      lines.push('=== 变量状态 ===')
      Object.entries(props.result.variables).forEach(([name, value]) => {
        lines.push(`${name}: ${formatVariable(value)}`)
      })
      lines.push('')
    }
  } else {
    lines.push('=== 错误信息 ===')
    lines.push(props.result.error || '未知错误')
    lines.push('')
  }

  return lines.join('\n')
}
</script>

<style scoped>
.code-result {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #2d2d30;
  border-bottom: 1px solid #3e3e42;
}

.result-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.result-status.success {
  background: rgba(40, 167, 69, 0.2);
  color: #28a745;
}

.result-status.error {
  background: rgba(220, 53, 69, 0.2);
  color: #dc3545;
}

.result-status.no-result {
  background: rgba(108, 117, 125, 0.2);
  color: #6c757d;
}

.status-icon {
  font-size: 1rem;
}

.result-actions {
  display: flex;
  gap: 0.25rem;
}

.result-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.success-result,
.error-result {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.output-section,
.error-section,
.variables-section {
  background: #252526;
  border: 1px solid #3e3e42;
  border-radius: 6px;
  overflow: hidden;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #2d2d30;
  border-bottom: 1px solid #3e3e42;
}

.section-header h4 {
  margin: 0;
  font-size: 0.9rem;
  color: #ffffff;
}

.toggle-btn {
  background: none;
  border: none;
  color: #969696;
  cursor: pointer;
  font-size: 0.8rem;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.toggle-btn:hover {
  background: #3c3c3c;
  color: #d4d4d4;
}

.section-content {
  padding: 1rem;
}

.output-text,
.error-text {
  white-space: pre-wrap;
  font-family: inherit;
  font-size: 0.9rem;
  line-height: 1.4;
  margin: 0;
}

.output-text {
  color: #d4d4d4;
}

.error-text {
  color: #ff9999;
}

.output-stats {
  display: flex;
  gap: 1rem;
  margin-top: 0.75rem;
  font-size: 0.8rem;
  color: #969696;
}

.variables-grid {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.variable-item {
  background: #1e1e1e;
  border: 1px solid #3e3e42;
  border-radius: 4px;
  overflow: hidden;
}

.variable-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.variable-header:hover {
  background: #2d2d30;
}

.variable-name {
  color: #9cdcfe;
  font-weight: 600;
}

.variable-type {
  color: #4ec9b0;
  font-size: 0.85rem;
}

.toggle-icon {
  color: #969696;
  font-size: 0.8rem;
}

.variable-value {
  padding: 0 0.75rem 0.75rem;
  border-top: 1px solid #3e3e42;
}

.variable-value pre {
  margin: 0;
  font-size: 0.85rem;
  line-height: 1.4;
  color: #d4d4d4;
  white-space: pre-wrap;
  word-break: break-all;
}

.execution-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  padding: 1rem;
  background: #252526;
  border: 1px solid #3e3e42;
  border-radius: 6px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-label {
  color: #969696;
  font-size: 0.85rem;
}

.info-value {
  color: #ffffff;
  font-weight: 600;
  font-size: 0.9rem;
}

.error-main {
  text-align: center;
  padding: 2rem 1rem;
  background: rgba(220, 53, 69, 0.1);
  border: 1px solid rgba(220, 53, 69, 0.3);
  border-radius: 8px;
  margin-bottom: 1rem;
}

.error-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.error-main h3 {
  margin: 0 0 1rem 0;
  color: #dc3545;
  font-size: 1.3rem;
}

.error-message {
  margin: 0;
  color: #ff9999;
  font-size: 1rem;
}

.partial-output {
  background: #252526;
  border: 1px solid #3e3e42;
  border-radius: 6px;
  padding: 1rem;
}

.partial-output h4 {
  margin: 0 0 0.75rem 0;
  color: #ffffff;
  font-size: 0.9rem;
}

.error-details {
  background: #252526;
  border: 1px solid #3e3e42;
  border-radius: 6px;
  padding: 1rem;
}

.error-details h4 {
  margin: 0 0 1rem 0;
  color: #ffffff;
  font-size: 0.9rem;
}

.error-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.no-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: #969696;
}

.placeholder-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.no-result p {
  margin: 0.25rem 0;
}

.placeholder-text {
  font-size: 0.9rem;
  opacity: 0.7;
}

/* 按钮样式 */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  border: none;
  font-size: 0.8rem;
  transition: all 0.3s ease;
  min-width: 32px;
  height: 32px;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
}

.btn-outline {
  background: transparent;
  color: #969696;
  border: 1px solid #3e3e42;
}

.btn-outline:hover {
  background: #3c3c3c;
  color: #d4d4d4;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: #2d2d30;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
  border: 1px solid #3e3e42;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #3e3e42;
}

.modal-header h3 {
  margin: 0;
  color: #ffffff;
  font-size: 1.3rem;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #969696;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.btn-close:hover {
  background: #3c3c3c;
  color: #ffffff;
}

.modal-body {
  padding: 1.5rem;
}

.share-options {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.share-option {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #3c3c3c;
  border: 1px solid #3e3e42;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: left;
}

.share-option:hover {
  background: #4a4a4a;
  border-color: #667eea;
}

.option-icon {
  font-size: 1.5rem;
}

.option-content h4 {
  margin: 0 0 0.25rem 0;
  color: #ffffff;
  font-size: 1rem;
}

.option-content p {
  margin: 0;
  color: #969696;
  font-size: 0.85rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .result-header {
    flex-direction: column;
    gap: 0.75rem;
    align-items: stretch;
  }

  .execution-info {
    grid-template-columns: 1fr;
  }

  .modal-content {
    width: 95%;
    margin: 1rem;
  }

  .share-option {
    padding: 0.75rem;
  }
}

@media (max-width: 480px) {
  .section-header {
    padding: 0.5rem 0.75rem;
  }

  .section-content {
    padding: 0.75rem;
  }

  .execution-info {
    padding: 0.75rem;
  }
}
</style>