<template>
  <div class="code-sandbox">
    <div class="sandbox-header">
      <div class="header-left">
        <h2>代码沙盒</h2>
        <p>在安全的隔离环境中执行Python代码</p>
      </div>
      <div class="header-right">
        <div class="execution-info">
          <span class="status-indicator" :class="executionStatus">
            {{ getStatusText() }}
          </span>
          <span class="execution-time" v-if="lastExecutionTime">
            执行时间: {{ lastExecutionTime }}ms
          </span>
        </div>
      </div>
    </div>

    <div class="sandbox-main">
      <div class="editor-panel">
        <div class="panel-header">
          <h3>代码编辑器</h3>
          <div class="editor-controls">
            <select v-model="selectedLanguage" class="language-selector">
              <option value="python">Python</option>
            </select>
            <button @click="formatCode" class="btn btn-secondary btn-sm">
              格式化
            </button>
            <button @click="clearCode" class="btn btn-outline btn-sm">
              清空
            </button>
          </div>
        </div>

        <div class="code-editor">
          <textarea
            ref="codeEditor"
            v-model="code"
            :placeholder="codePlaceholder"
            class="code-textarea"
            @keydown.tab="handleTab"
            @keydown="handleKeyDown"
          ></textarea>
          <div class="line-numbers">
            <div v-for="n in lineCount" :key="n" class="line-number">{{ n }}</div>
          </div>
        </div>

        <div class="editor-footer">
          <div class="code-info">
            <span>行数: {{ lineCount }}</span>
            <span>字符数: {{ code.length }}</span>
          </div>
          <div class="templates">
            <select @change="loadTemplate($event.target.value)" class="template-selector">
              <option value="">选择模板...</option>
              <option value="hello_world">Hello World</option>
              <option value="data_analysis">数据分析示例</option>
              <option value="plotting">绘图示例</option>
              <option value="machine_learning">机器学习示例</option>
            </select>
          </div>
        </div>
      </div>

      <div class="output-panel">
        <div class="panel-header">
          <h3>执行结果</h3>
          <div class="output-controls">
            <button @click="clearOutput" class="btn btn-outline btn-sm">
              清空输出
            </button>
            <button @click="downloadOutput" class="btn btn-secondary btn-sm" :disabled="!hasOutput">
              下载结果
            </button>
          </div>
        </div>

        <div class="output-container" ref="outputContainer">
          <div v-if="!hasOutput && !executionError" class="output-placeholder">
            <div class="placeholder-icon">📝</div>
            <p>点击"执行代码"查看结果</p>
          </div>

          <div v-if="executionError" class="error-output">
            <div class="error-header">
              <span class="error-icon">❌</span>
              <span>执行错误</span>
            </div>
            <pre class="error-message">{{ executionError }}</pre>
          </div>

          <div v-if="executionResult" class="success-output">
            <div class="output-section" v-if="executionResult.output">
              <h4>标准输出</h4>
              <pre class="output-text">{{ executionResult.output }}</pre>
            </div>

            <div class="output-section" v-if="executionResult.error">
              <h4>错误输出</h4>
              <pre class="error-text">{{ executionResult.error }}</pre>
            </div>

            <div class="output-section" v-if="executionResult.variables && Object.keys(executionResult.variables).length > 0">
              <h4>变量状态</h4>
              <div class="variables-grid">
                <div v-for="(value, name) in executionResult.variables" :key="name" class="variable-item">
                  <div class="variable-name">{{ name }}</div>
                  <div class="variable-value">{{ formatVariable(value) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="sandbox-footer">
      <div class="execution-controls">
        <button @click="validateCode" class="btn btn-outline" :disabled="isExecuting">
          <span class="btn-icon">✓</span>
          验证代码
        </button>
        <button @click="executeCode" class="btn btn-primary" :disabled="isExecuting || !code.trim()">
          <span class="btn-icon" v-if="!isExecuting">▶</span>
          <span class="btn-icon spinner" v-else>⟳</span>
          {{ isExecuting ? '执行中...' : '执行代码' }}
        </button>
      </div>

      <div class="settings-panel">
        <div class="setting-item">
          <label>超时时间 (秒):</label>
          <input v-model.number="timeout" type="number" min="1" max="60" class="setting-input" />
        </div>
        <div class="setting-item">
          <label>内存限制 (MB):</label>
          <input v-model.number="memoryLimit" type="number" min="50" max="500" step="50" class="setting-input" />
        </div>
      </div>
    </div>

    <!-- 代码验证结果模态框 -->
    <div v-if="showValidationModal" class="modal-overlay" @click="closeValidationModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>代码验证结果</h3>
          <button @click="closeValidationModal" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div class="validation-status" :class="{ 'valid': validationResult?.is_safe, 'invalid': !validationResult?.is_safe }">
            <span class="status-icon">{{ validationResult?.is_safe ? '✓' : '✗' }}</span>
            <span>{{ validationResult?.is_safe ? '代码安全' : '代码不安全' }}</span>
          </div>

          <div v-if="validationResult?.errors?.length > 0" class="validation-errors">
            <h4>安全错误:</h4>
            <ul>
              <li v-for="error in validationResult.errors" :key="error">{{ error }}</li>
            </ul>
          </div>

          <div v-if="validationResult?.warnings?.length > 0" class="validation-warnings">
            <h4>警告:</h4>
            <ul>
              <li v-for="warning in validationResult.warnings" :key="warning">{{ warning }}</li>
            </ul>
          </div>

          <div v-if="validationResult?.stats" class="validation-stats">
            <h4>统计信息:</h4>
            <div class="stats-grid">
              <div class="stat-item">
                <span class="stat-label">可用模块:</span>
                <span class="stat-value">{{ validationResult.stats.available_safe_modules?.length || 0 }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">超时时间:</span>
                <span class="stat-value">{{ validationResult.stats.timeout }}s</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">内存限制:</span>
                <span class="stat-value">{{ validationResult.stats.memory_limit_mb }}MB</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { executePythonCode, validatePythonCode } from '@/services/codeExecution'

// 响应式数据
const code = ref(`# 欢迎使用代码沙盒！
# 在这里输入您的Python代码

# 示例代码：
print("Hello, World!")
x = 10
y = 20
result = x + y
print(f"计算结果: {result}")

# 您可以修改或替换上面的代码
`)

const executionResult = ref(null)
const executionError = ref(null)
const isExecuting = ref(false)
const lastExecutionTime = ref(null)
const selectedLanguage = ref('python')
const timeout = ref(30)
const memoryLimit = ref(100)
const showValidationModal = ref(false)
const validationResult = ref(null)

// DOM引用
const codeEditor = ref(null)
const outputContainer = ref(null)

// 计算属性
const lineCount = computed(() => {
  if (!code.value) return 1
  return code.value.split('\n').length
})

const hasOutput = computed(() => {
  return executionResult.value || executionError.value
})

const executionStatus = computed(() => {
  if (isExecuting.value) return 'running'
  if (executionError.value) return 'error'
  if (executionResult.value) return 'success'
  return 'idle'
})

const codePlaceholder = ref('在此输入Python代码...')

// 代码模板
const codeTemplates = {
  hello_world: `# Hello World 示例
print("Hello, World!")

# 基本变量操作
name = "Python"
version = 3.9
print(f"欢迎使用 {name} {version}!")`,

  data_analysis: `# 数据分析示例
import numpy as np
import pandas as pd

# 创建示例数据
data = {
    'name': ['Alice', 'Bob', 'Charlie', 'David'],
    'age': [25, 30, 35, 28],
    'score': [85, 92, 78, 88]
}

# 创建DataFrame
df = pd.DataFrame(data)
print("数据表:")
print(df)

# 基本统计
print("\\n统计信息:")
print(df.describe())`,

  plotting: `# 绘图示例
import matplotlib.pyplot as plt
import numpy as np

# 生成数据
x = np.linspace(0, 2*np.pi, 100)
y1 = np.sin(x)
y2 = np.cos(x)

# 创建图表
plt.figure(figsize=(10, 6))
plt.plot(x, y1, label='sin(x)', linewidth=2)
plt.plot(x, y2, label='cos(x)', linewidth=2)
plt.xlabel('x')
plt.ylabel('y')
plt.title('正弦和余弦函数')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()

print("图表已生成!")`,

  machine_learning: `# 机器学习示例
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# 生成示例数据
X, y = make_classification(
    n_samples=1000,
    n_features=20,
    n_informative=10,
    n_redundant=5,
    random_state=42
)

# 分割数据
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 训练模型
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 预测和评估
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"模型准确率: {accuracy:.4f}")
print("\\n分类报告:")
print(classification_report(y_test, y_pred))`
}

// 方法
const getStatusText = () => {
  const statusMap = {
    idle: '就绪',
    running: '执行中',
    success: '成功',
    error: '错误'
  }
  return statusMap[executionStatus.value] || '未知'
}

const executeCode = async () => {
  if (!code.value.trim()) {
    alert('请输入代码后再执行')
    return
  }

  isExecuting.value = true
  executionError.value = null
  executionResult.value = null

  try {
    const startTime = Date.now()
    const result = await executePythonCode(code.value, {
      timeout: timeout.value,
      memory_limit_mb: memoryLimit.value
    })
    const endTime = Date.now()

    lastExecutionTime.value = endTime - startTime

    if (result.success) {
      executionResult.value = result
    } else {
      executionError.value = result.error
    }

    // 滚动到输出区域
    await nextTick()
    if (outputContainer.value) {
      outputContainer.value.scrollTop = outputContainer.value.scrollHeight
    }
  } catch (error) {
    executionError.value = `执行错误: ${error.message}`
  } finally {
    isExecuting.value = false
  }
}

const validateCode = async () => {
  if (!code.value.trim()) {
    alert('请输入代码后再验证')
    return
  }

  try {
    validationResult.value = await validatePythonCode(code.value, {
      timeout: timeout.value,
      memory_limit_mb: memoryLimit.value
    })
    showValidationModal.value = true
  } catch (error) {
    alert(`验证失败: ${error.message}`)
  }
}

const formatCode = () => {
  // 简单的代码格式化（可以集成更复杂的格式化工具）
  const lines = code.value.split('\n')
  const formatted = lines.map(line => {
    const trimmed = line.trim()
    if (trimmed && !trimmed.startsWith('#')) {
      // 简单的缩进处理
      const indent = line.match(/^\s*/)[0].length
      return ' '.repeat(Math.floor(indent / 4) * 4) + trimmed
    }
    return line
  })
  code.value = formatted.join('\n')
}

const clearCode = () => {
  if (confirm('确定要清空代码吗？')) {
    code.value = ''
  }
}

const clearOutput = () => {
  executionResult.value = null
  executionError.value = null
  lastExecutionTime.value = null
}

const downloadOutput = () => {
  if (!executionResult.value) return

  const content = [
    '=== 执行结果 ===',
    `执行时间: ${lastExecutionTime.value}ms`,
    '',
    '=== 标准输出 ===',
    executionResult.value.output || '(无输出)',
    '',
    '=== 错误输出 ===',
    executionResult.value.error || '(无错误)',
    '',
    '=== 变量状态 ===',
    JSON.stringify(executionResult.value.variables || {}, null, 2)
  ].join('\n')

  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `code_output_${new Date().getTime()}.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const loadTemplate = (templateName) => {
  if (templateName && codeTemplates[templateName]) {
    code.value = codeTemplates[templateName]
  }
}

const handleTab = (event) => {
  event.preventDefault()
  const start = event.target.selectionStart
  const end = event.target.selectionEnd
  code.value = code.value.substring(0, start) + '    ' + code.value.substring(end)
  event.target.selectionStart = event.target.selectionEnd = start + 4
}

const handleKeyDown = (event) => {
  // Ctrl+Enter 执行代码
  if (event.ctrlKey && event.key === 'Enter') {
    event.preventDefault()
    executeCode()
  }
  // Ctrl+Shift+Enter 验证代码
  if (event.ctrlKey && event.shiftKey && event.key === 'Enter') {
    event.preventDefault()
    validateCode()
  }
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

const closeValidationModal = () => {
  showValidationModal.value = false
  validationResult.value = null
}

// 生命周期
onMounted(() => {
  // 可以在这里添加初始化逻辑
})

onUnmounted(() => {
  // 清理资源
})
</script>

<style scoped>
.code-sandbox {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.sandbox-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: #2d2d30;
  border-bottom: 1px solid #3e3e42;
}

.header-left h2 {
  margin: 0 0 0.25rem 0;
  font-size: 1.3rem;
  color: #ffffff;
}

.header-left p {
  margin: 0;
  color: #969696;
  font-size: 0.9rem;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.execution-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.status-indicator {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.status-indicator.idle {
  background: #6c757d;
  color: white;
}

.status-indicator.running {
  background: #007bff;
  color: white;
  animation: pulse 1.5s infinite;
}

.status-indicator.success {
  background: #28a745;
  color: white;
}

.status-indicator.error {
  background: #dc3545;
  color: white;
}

.execution-time {
  color: #969696;
  font-size: 0.85rem;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.sandbox-main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.editor-panel,
.output-panel {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.editor-panel {
  border-right: 1px solid #3e3e42;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #252526;
  border-bottom: 1px solid #3e3e42;
}

.panel-header h3 {
  margin: 0;
  font-size: 1rem;
  color: #ffffff;
}

.editor-controls,
.output-controls {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.language-selector,
.template-selector {
  background: #3c3c3c;
  color: #d4d4d4;
  border: 1px solid #3e3e42;
  border-radius: 4px;
  padding: 0.25rem 0.5rem;
  font-size: 0.85rem;
}

.code-editor {
  display: flex;
  flex: 1;
  position: relative;
  background: #1e1e1e;
  overflow: hidden;
}

.code-textarea {
  flex: 1;
  background: transparent;
  color: #d4d4d4;
  border: none;
  outline: none;
  padding: 1rem;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.5;
  resize: none;
  tab-size: 4;
  white-space: pre;
  overflow-x: auto;
}

.line-numbers {
  background: #2d2d30;
  color: #858585;
  padding: 1rem 0.5rem;
  text-align: right;
  user-select: none;
  border-right: 1px solid #3e3e42;
}

.line-number {
  font-size: 14px;
  line-height: 1.5;
}

.editor-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  background: #252526;
  border-top: 1px solid #3e3e42;
  font-size: 0.85rem;
  color: #969696;
}

.code-info {
  display: flex;
  gap: 1rem;
}

.output-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.output-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #969696;
  text-align: center;
}

.placeholder-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.error-output {
  background: #2d1b1b;
  border: 1px solid #8b0000;
  border-radius: 6px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.error-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  font-weight: 600;
  color: #ff6b6b;
}

.error-message {
  color: #ff9999;
  white-space: pre-wrap;
  font-family: inherit;
  margin: 0;
}

.success-output {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.output-section {
  background: #1e1e1e;
  border: 1px solid #3e3e42;
  border-radius: 6px;
  padding: 1rem;
}

.output-section h4 {
  margin: 0 0 0.75rem 0;
  color: #ffffff;
  font-size: 0.9rem;
}

.output-text,
.error-text {
  white-space: pre-wrap;
  font-family: inherit;
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.4;
}

.output-text {
  color: #d4d4d4;
}

.error-text {
  color: #ff9999;
}

.variables-grid {
  display: grid;
  gap: 0.5rem;
}

.variable-item {
  display: grid;
  grid-template-columns: 150px 1fr;
  gap: 1rem;
  padding: 0.5rem;
  background: #2d2d30;
  border-radius: 4px;
}

.variable-name {
  color: #9cdcfe;
  font-weight: 600;
}

.variable-value {
  color: #d4d4d4;
  word-break: break-all;
  font-family: inherit;
  font-size: 0.85rem;
}

.sandbox-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: #2d2d30;
  border-top: 1px solid #3e3e42;
}

.execution-controls {
  display: flex;
  gap: 1rem;
}

.settings-panel {
  display: flex;
  gap: 1.5rem;
  align-items: center;
}

.setting-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.setting-item label {
  color: #969696;
}

.setting-input {
  background: #3c3c3c;
  color: #d4d4d4;
  border: 1px solid #3e3e42;
  border-radius: 4px;
  padding: 0.25rem 0.5rem;
  width: 60px;
  font-size: 0.85rem;
}

/* 按钮样式 */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  border: none;
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-sm {
  padding: 0.25rem 0.75rem;
  font-size: 0.85rem;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #5a6268;
}

.btn-outline {
  background: transparent;
  color: #969696;
  border: 1px solid #3e3e42;
}

.btn-outline:hover:not(:disabled) {
  background: #3c3c3c;
  color: #d4d4d4;
}

.btn-icon {
  font-size: 1rem;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
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
  max-width: 600px;
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

.validation-status {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  font-size: 1.1rem;
  font-weight: 600;
}

.validation-status.valid {
  background: rgba(40, 167, 69, 0.2);
  color: #28a745;
}

.validation-status.invalid {
  background: rgba(220, 53, 69, 0.2);
  color: #dc3545;
}

.validation-errors,
.validation-warnings {
  margin-bottom: 1.5rem;
}

.validation-errors h4,
.validation-warnings h4 {
  color: #ffffff;
  margin-bottom: 0.75rem;
}

.validation-errors ul,
.validation-warnings ul {
  margin: 0;
  padding-left: 1.5rem;
}

.validation-errors li {
  color: #ff9999;
  margin-bottom: 0.5rem;
}

.validation-warnings li {
  color: #ffd700;
  margin-bottom: 0.5rem;
}

.validation-stats h4 {
  color: #ffffff;
  margin-bottom: 1rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem;
  background: #3c3c3c;
  border-radius: 6px;
}

.stat-label {
  color: #969696;
}

.stat-value {
  color: #ffffff;
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sandbox-header {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }

  .sandbox-main {
    flex-direction: column;
  }

  .editor-panel {
    border-right: none;
    border-bottom: 1px solid #3e3e42;
  }

  .sandbox-footer {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .execution-controls {
    justify-content: center;
  }

  .settings-panel {
    justify-content: center;
  }

  .modal-content {
    width: 95%;
    margin: 1rem;
  }
}

@media (max-width: 480px) {
  .editor-controls,
  .output-controls {
    flex-wrap: wrap;
  }

  .editor-footer {
    flex-direction: column;
    gap: 0.75rem;
    align-items: flex-start;
  }

  .settings-panel {
    flex-direction: column;
    gap: 0.75rem;
  }
}
</style>