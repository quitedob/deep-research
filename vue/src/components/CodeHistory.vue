<template>
  <div class="code-history">
    <div class="history-header">
      <h3>执行历史</h3>
      <div class="header-actions">
        <button @click="refreshHistory" class="btn btn-sm btn-outline" :disabled="loading">
          🔄 刷新
        </button>
        <button @click="clearHistory" class="btn btn-sm btn-outline" :disabled="loading || !historyItems.length">
          🗑️ 清空历史
        </button>
      </div>
    </div>

    <div class="history-filters">
      <div class="filter-group">
        <label>状态筛选:</label>
        <select v-model="statusFilter" class="filter-select">
          <option value="">全部</option>
          <option value="success">成功</option>
          <option value="error">失败</option>
        </select>
      </div>

      <div class="filter-group">
        <label>时间范围:</label>
        <select v-model="timeFilter" class="filter-select">
          <option value="">全部时间</option>
          <option value="today">今天</option>
          <option value="week">最近7天</option>
          <option value="month">最近30天</option>
        </select>
      </div>

      <div class="search-group">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索代码或结果..."
          class="search-input"
        />
      </div>
    </div>

    <div class="history-content">
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner">⟳</div>
        <p>加载历史记录...</p>
      </div>

      <div v-else-if="filteredHistory.length === 0" class="empty-state">
        <div class="empty-icon">📝</div>
        <h4>暂无执行记录</h4>
        <p>{{ getEmptyMessage() }}</p>
      </div>

      <div v-else class="history-list">
        <div
          v-for="item in paginatedHistory"
          :key="item.id"
          class="history-item"
          :class="{ 'expanded': expandedItems.includes(item.id) }"
        >
          <div class="item-header" @click="toggleItem(item.id)">
            <div class="item-status">
              <span class="status-icon" :class="item.success ? 'success' : 'error'">
                {{ item.success ? '✅' : '❌' }}
              </span>
              <span class="status-text">{{ item.success ? '成功' : '失败' }}</span>
            </div>

            <div class="item-info">
              <div class="item-time">{{ formatTime(item.timestamp) }}</div>
              <div class="item-duration">{{ item.execution_time }}ms</div>
            </div>

            <div class="item-actions">
              <button @click.stop="rerunCode(item)" class="action-btn" title="重新运行">
                ▶️
              </button>
              <button @click.stop="copyCode(item)" class="action-btn" title="复制代码">
                📋
              </button>
              <button @click.stop="deleteItem(item.id)" class="action-btn" title="删除记录">
                🗑️
              </button>
            </div>
          </div>

          <div v-show="expandedItems.includes(item.id)" class="item-content">
            <div class="code-section">
              <div class="section-header">
                <h4>执行代码</h4>
                <button @click="copyCode(item)" class="btn btn-xs btn-outline">
                  复制
                </button>
              </div>
              <pre class="code-content">{{ item.code }}</pre>
            </div>

            <div v-if="item.output" class="output-section">
              <div class="section-header">
                <h4>输出结果</h4>
                <button @click="copyOutput(item)" class="btn btn-xs btn-outline">
                  复制
                </button>
              </div>
              <pre class="output-content">{{ item.output }}</pre>
            </div>

            <div v-if="item.error" class="error-section">
              <div class="section-header">
                <h4>错误信息</h4>
              </div>
              <pre class="error-content">{{ item.error }}</pre>
            </div>

            <div v-if="item.variables" class="variables-section">
              <div class="section-header">
                <h4>变量状态</h4>
              </div>
              <div class="variables-preview">
                <span v-for="(value, name) in Object.keys(item.variables).slice(0, 3)" :key="name" class="variable-tag">
                  {{ name }}
                </span>
                <span v-if="Object.keys(item.variables).length > 3" class="variable-more">
                  +{{ Object.keys(item.variables).length - 3 }} 更多
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="filteredHistory.length > pageSize" class="pagination">
        <button
          @click="prevPage"
          :disabled="currentPage === 1"
          class="btn btn-sm btn-outline"
        >
          ← 上一页
        </button>
        <span class="page-info">
          第 {{ currentPage }} 页，共 {{ totalPages }} 页
        </span>
        <button
          @click="nextPage"
          :disabled="currentPage === totalPages"
          class="btn btn-sm btn-outline"
        >
          下一页 →
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'

const emit = defineEmits(['rerun-code', 'copy-code'])

// 响应式数据
const loading = ref(false)
const historyItems = ref([])
const expandedItems = ref([])
const statusFilter = ref('')
const timeFilter = ref('')
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(10)

// 模拟历史数据（实际应该从API获取）
const mockHistory = [
  {
    id: 'exec_001',
    timestamp: new Date(Date.now() - 1000 * 60 * 5), // 5分钟前
    code: 'print("Hello, World!")\nx = 10\nprint(f"Result: {x}")',
    output: 'Hello, World!\nResult: 10',
    error: null,
    execution_time: 125,
    success: true,
    variables: { x: 10 }
  },
  {
    id: 'exec_002',
    timestamp: new Date(Date.now() - 1000 * 60 * 15), // 15分钟前
    code: 'import numpy as np\narr = np.array([1, 2, 3, 4, 5])\nprint(f"Mean: {arr.mean()}")',
    output: 'Mean: 3.0',
    error: null,
    execution_time: 230,
    success: true,
    variables: { arr: 'ndarray([1, 2, 3, 4, 5])' }
  },
  {
    id: 'exec_003',
    timestamp: new Date(Date.now() - 1000 * 60 * 30), // 30分钟前
    code: 'print(undefined_variable)',
    output: '',
    error: 'NameError: name \'undefined_variable\' is not defined',
    execution_time: 45,
    success: false,
    variables: {}
  },
  {
    id: 'exec_004',
    timestamp: new Date(Date.now() - 1000 * 60 * 60), // 1小时前
    code: 'import matplotlib.pyplot as plt\nimport numpy as np\n\nx = np.linspace(0, 10, 100)\ny = np.sin(x)\n\nplt.plot(x, y)\nplt.show()',
    output: '图表已生成并显示',
    error: null,
    execution_time: 890,
    success: true,
    variables: { x: 'array([...])', y: 'array([...])' }
  },
  {
    id: 'exec_005',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2), // 2小时前
    code: '# 数据分析示例\nimport pandas as pd\ndata = {"name": ["Alice", "Bob"], "age": [25, 30]}\ndf = pd.DataFrame(data)\nprint(df)',
    output: '    name  age\n0  Alice   25\n1    Bob   30',
    error: null,
    execution_time: 156,
    success: true,
    variables: { data: 'Object', df: 'DataFrame object' }
  }
]

// 计算属性
const filteredHistory = computed(() => {
  let filtered = historyItems.value

  // 状态筛选
  if (statusFilter.value) {
    filtered = filtered.filter(item =>
      statusFilter.value === 'success' ? item.success : !item.success
    )
  }

  // 时间筛选
  if (timeFilter.value) {
    const now = new Date()
    const filterDate = new Date()

    switch (timeFilter.value) {
      case 'today':
        filterDate.setHours(0, 0, 0, 0)
        break
      case 'week':
        filterDate.setDate(now.getDate() - 7)
        break
      case 'month':
        filterDate.setDate(now.getDate() - 30)
        break
    }

    filtered = filtered.filter(item => item.timestamp >= filterDate)
  }

  // 搜索筛选
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(item =>
      item.code.toLowerCase().includes(query) ||
      (item.output && item.output.toLowerCase().includes(query)) ||
      (item.error && item.error.toLowerCase().includes(query))
    )
  }

  // 按时间倒序排列
  return filtered.sort((a, b) => b.timestamp - a.timestamp)
})

const totalPages = computed(() => {
  return Math.ceil(filteredHistory.value.length / pageSize.value)
})

const paginatedHistory = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredHistory.value.slice(start, end)
})

// 方法
const loadHistory = async () => {
  loading.value = true
  try {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 500))
    historyItems.value = mockHistory
  } catch (error) {
    console.error('加载历史记录失败:', error)
  } finally {
    loading.value = false
  }
}

const refreshHistory = () => {
  loadHistory()
}

const clearHistory = () => {
  if (confirm('确定要清空所有历史记录吗？此操作不可恢复。')) {
    historyItems.value = []
    expandedItems.value = []
    currentPage.value = 1
  }
}

const toggleItem = (itemId) => {
  const index = expandedItems.value.indexOf(itemId)
  if (index > -1) {
    expandedItems.value.splice(index, 1)
  } else {
    expandedItems.value.push(itemId)
  }
}

const rerunCode = (item) => {
  emit('rerun-code', item.code)
}

const copyCode = (item) => {
  navigator.clipboard.writeText(item.code).then(() => {
    console.log('代码已复制到剪贴板')
  }).catch(error => {
    console.error('复制失败:', error)
  })
}

const copyOutput = (item) => {
  if (!item.output) return

  navigator.clipboard.writeText(item.output).then(() => {
    console.log('输出已复制到剪贴板')
  }).catch(error => {
    console.error('复制失败:', error)
  })
}

const deleteItem = (itemId) => {
  if (confirm('确定要删除这条记录吗？')) {
    const index = historyItems.value.findIndex(item => item.id === itemId)
    if (index > -1) {
      historyItems.value.splice(index, 1)
      // 同时从展开列表中移除
      const expandedIndex = expandedItems.value.indexOf(itemId)
      if (expandedIndex > -1) {
        expandedItems.value.splice(expandedIndex, 1)
      }
    }
  }
}

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

const formatTime = (timestamp) => {
  const now = new Date()
  const diff = now - timestamp
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`

  return timestamp.toLocaleDateString('zh-CN')
}

const getEmptyMessage = () => {
  if (statusFilter.value) {
    return `没有找到${statusFilter.value === 'success' ? '成功' : '失败'}的执行记录`
  }
  if (timeFilter.value) {
    return `${timeFilter === 'today' ? '今天' : timeFilter === 'week' ? '最近7天' : '最近30天'}没有执行记录`
  }
  if (searchQuery.value) {
    return `没有找到包含 "${searchQuery.value}" 的记录`
  }
  return '还没有执行过任何代码'
}

// 监听筛选条件变化，重置分页
watch([statusFilter, timeFilter, searchQuery], () => {
  currentPage.value = 1
})

// 生命周期
onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.code-history {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #2d2d30;
  border-bottom: 1px solid #3e3e42;
}

.history-header h3 {
  margin: 0;
  font-size: 1.1rem;
  color: #ffffff;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.history-filters {
  display: flex;
  gap: 1rem;
  padding: 0.75rem 1rem;
  background: #252526;
  border-bottom: 1px solid #3e3e42;
  flex-wrap: wrap;
  align-items: center;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-group label {
  font-size: 0.85rem;
  color: #969696;
}

.filter-select {
  background: #3c3c3c;
  color: #d4d4d4;
  border: 1px solid #3e3e42;
  border-radius: 4px;
  padding: 0.25rem 0.5rem;
  font-size: 0.85rem;
}

.search-group {
  flex: 1;
  min-width: 200px;
}

.search-input {
  width: 100%;
  background: #3c3c3c;
  color: #d4d4d4;
  border: 1px solid #3e3e42;
  border-radius: 4px;
  padding: 0.25rem 0.5rem;
  font-size: 0.85rem;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
}

.history-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #969696;
}

.loading-spinner {
  font-size: 2rem;
  margin-bottom: 1rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  text-align: center;
  color: #969696;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-state h4 {
  margin: 0 0 0.5rem 0;
  color: #d4d4d4;
}

.empty-state p {
  margin: 0;
  font-size: 0.9rem;
  opacity: 0.8;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.history-item {
  background: #252526;
  border: 1px solid #3e3e42;
  border-radius: 6px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.history-item:hover {
  border-color: #667eea;
}

.history-item.expanded {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.item-header:hover {
  background: #2d2d30;
}

.item-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-icon {
  font-size: 1rem;
}

.status-icon.success {
  color: #28a745;
}

.status-icon.error {
  color: #dc3545;
}

.status-text {
  font-size: 0.85rem;
  font-weight: 600;
}

.item-info {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.item-time {
  font-size: 0.85rem;
  color: #969696;
}

.item-duration {
  font-size: 0.85rem;
  color: #4ec9b0;
}

.item-actions {
  display: flex;
  gap: 0.25rem;
}

.action-btn {
  background: none;
  border: none;
  color: #969696;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.3s ease;
  font-size: 0.9rem;
}

.action-btn:hover {
  background: #3c3c3c;
  color: #d4d4d4;
}

.item-content {
  border-top: 1px solid #3e3e42;
  background: #1e1e1e;
}

.code-section,
.output-section,
.error-section,
.variables-section {
  padding: 1rem;
  border-bottom: 1px solid #3e3e42;
}

.variables-section {
  border-bottom: none;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.section-header h4 {
  margin: 0;
  font-size: 0.9rem;
  color: #ffffff;
}

.code-content,
.output-content,
.error-content {
  background: #2d2d30;
  border: 1px solid #3e3e42;
  border-radius: 4px;
  padding: 0.75rem;
  font-size: 0.85rem;
  line-height: 1.4;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  overflow-x: auto;
}

.code-content {
  color: #d4d4d4;
}

.output-content {
  color: #4ec9b0;
}

.error-content {
  color: #ff9999;
}

.variables-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.variable-tag {
  background: #3c3c3c;
  color: #9cdcfe;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}

.variable-more {
  background: #3c3c3c;
  color: #969696;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #252526;
  border-top: 1px solid #3e3e42;
}

.page-info {
  color: #969696;
  font-size: 0.85rem;
}

/* 按钮样式 */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
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

.btn-xs {
  padding: 0.125rem 0.5rem;
  font-size: 0.75rem;
}

.btn-outline {
  background: transparent;
  color: #969696;
  border: 1px solid #3e3e42;
}

.btn-outline:hover:not(:disabled) {
  background: #3c3c3c;
  color: #d4d4d4;
  border-color: #667eea;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .history-header {
    flex-direction: column;
    gap: 0.75rem;
    align-items: stretch;
  }

  .history-filters {
    flex-direction: column;
    gap: 0.75rem;
    align-items: stretch;
  }

  .filter-group {
    justify-content: space-between;
  }

  .search-group {
    min-width: auto;
  }

  .item-header {
    flex-direction: column;
    gap: 0.75rem;
    align-items: stretch;
  }

  .item-info {
    justify-content: space-between;
  }

  .pagination {
    flex-direction: column;
    gap: 0.75rem;
  }
}

@media (max-width: 480px) {
  .history-content {
    padding: 0.5rem;
  }

  .item-header {
    padding: 0.5rem;
  }

  .code-section,
  .output-section,
  .error-section,
  .variables-section {
    padding: 0.75rem;
  }

  .code-content,
  .output-content,
  .error-content {
    padding: 0.5rem;
    font-size: 0.8rem;
  }
}
</style>