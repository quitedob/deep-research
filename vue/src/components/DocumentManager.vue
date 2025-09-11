<template>
  <div class="document-manager">
    <div class="manager-header">
      <h3 class="manager-title">
        <i class="icon-folder"></i>
        文档管理
      </h3>
      <div class="manager-actions">
        <button class="btn-upload" @click="$refs.fileInput.click()">
          <i class="icon-upload"></i>
          上传文档
        </button>
        <input
          ref="fileInput"
          type="file"
          multiple
          accept=".pdf,.docx,.doc,.txt,.md"
          @change="handleFileSelect"
          style="display: none"
        />
        <button class="btn-refresh" @click="loadDocuments" :disabled="loading">
          <i class="icon-refresh" :class="{ spinning: loading }"></i>
          刷新
        </button>
      </div>
    </div>

    <!-- 上传进度 -->
    <div v-if="uploadQueue.length > 0" class="upload-progress">
      <h4>上传进度</h4>
      <div
        v-for="upload in uploadQueue"
        :key="upload.id"
        class="upload-item"
      >
        <div class="upload-info">
          <span class="upload-filename">{{ upload.file.name }}</span>
          <span class="upload-size">({{ formatFileSize(upload.file.size) }})</span>
        </div>
        <div class="upload-status">
          <div v-if="upload.status === 'uploading'" class="progress-bar">
            <div
              class="progress-fill"
              :style="{ width: upload.progress + '%' }"
            ></div>
          </div>
          <span class="status-text">{{ getUploadStatusText(upload.status) }}</span>
          <button
            v-if="upload.status === 'completed'"
            class="btn-view"
            @click="viewDocument(upload.jobId)"
          >
            查看
          </button>
        </div>
      </div>
    </div>

    <!-- 文档列表 -->
    <div class="documents-list">
      <div class="list-header">
        <div class="search-box">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索文档..."
            @input="filterDocuments"
          />
          <i class="icon-search"></i>
        </div>
        <div class="filter-tabs">
          <button
            v-for="status in statusFilters"
            :key="status.value"
            :class="['tab-btn', { active: activeStatusFilter === status.value }]"
            @click="setStatusFilter(status.value)"
          >
            {{ status.label }} ({{ getStatusCount(status.value) }})
          </button>
        </div>
      </div>

      <div class="documents-grid">
        <div
          v-for="doc in filteredDocuments"
          :key="doc.job_id"
          class="document-card"
          :class="doc.status"
        >
          <div class="card-header">
            <div class="document-icon">
              <i :class="getFileIcon(doc.filename)"></i>
            </div>
            <div class="document-info">
              <h4 class="document-title">{{ doc.filename }}</h4>
              <div class="document-meta">
                <span class="file-size">{{ formatFileSize(doc.file_size || 0) }}</span>
                <span class="upload-time">{{ formatDate(doc.created_at) }}</span>
              </div>
            </div>
          </div>

          <div class="card-body">
            <div class="processing-status">
              <div class="status-indicator" :class="doc.status">
                <i :class="getStatusIcon(doc.status)"></i>
                <span>{{ getStatusText(doc.status) }}</span>
              </div>
              <div v-if="doc.progress !== undefined" class="progress-info">
                <div class="progress-bar">
                  <div
                    class="progress-fill"
                    :style="{ width: doc.progress + '%' }"
                  ></div>
                </div>
                <span class="progress-text">{{ doc.progress }}%</span>
              </div>
            </div>

            <div v-if="doc.error_message" class="error-message">
              <i class="icon-error"></i>
              {{ doc.error_message }}
            </div>

            <div v-if="doc.result" class="processing-result">
              <div class="result-item">
                <span class="result-label">文本长度:</span>
                <span class="result-value">{{ doc.result.text_length || 0 }}</span>
              </div>
              <div class="result-item">
                <span class="result-label">分块数量:</span>
                <span class="result-value">{{ doc.result.chunks_count || 0 }}</span>
              </div>
            </div>
          </div>

          <div class="card-actions">
            <button
              v-if="doc.status === 'completed'"
              class="btn-search"
              @click="searchInDocument(doc.job_id)"
            >
              <i class="icon-search"></i>
              搜索
            </button>
            <button
              v-if="doc.status === 'failed'"
              class="btn-retry"
              @click="retryDocument(doc.job_id)"
              :disabled="retrying === doc.job_id"
            >
              <i class="icon-retry"></i>
              重试
            </button>
            <button
              class="btn-delete"
              @click="deleteDocument(doc.job_id)"
              :disabled="deleting === doc.job_id"
            >
              <i class="icon-delete"></i>
              删除
            </button>
          </div>
        </div>

        <div v-if="filteredDocuments.length === 0" class="no-documents">
          <i class="icon-empty"></i>
          <h3>暂无文档</h3>
          <p>{{ searchQuery ? '没有找到匹配的文档' : '上传文档开始使用RAG功能' }}</p>
          <button class="btn-upload-large" @click="$refs.fileInput.click()">
            <i class="icon-upload"></i>
            上传文档
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ragAPI } from '@/services/api.js'

// Props
const props = defineProps({
  conversationId: {
    type: String,
    default: null
  }
})

// Emits
const emit = defineEmits(['document-selected', 'search-in-document'])

// Reactive data
const documents = ref([])
const uploadQueue = ref([])
const loading = ref(false)
const retrying = ref(null)
const deleting = ref(null)
const searchQuery = ref('')
const activeStatusFilter = ref('all')

// Computed
const filteredDocuments = computed(() => {
  let filtered = documents.value

  // 状态过滤
  if (activeStatusFilter.value !== 'all') {
    filtered = filtered.filter(doc => doc.status === activeStatusFilter.value)
  }

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(doc =>
      doc.filename.toLowerCase().includes(query)
    )
  }

  return filtered
})

const statusFilters = [
  { value: 'all', label: '全部' },
  { value: 'pending', label: '待处理' },
  { value: 'processing', label: '处理中' },
  { value: 'completed', label: '已完成' },
  { value: 'failed', label: '失败' }
]

// Methods
const getStatusCount = (status) => {
  if (status === 'all') return documents.value.length
  return documents.value.filter(doc => doc.status === status).length
}

const setStatusFilter = (status) => {
  activeStatusFilter.value = status
}

const filterDocuments = () => {
  // 搜索过滤由computed处理
}

const getFileIcon = (filename) => {
  const ext = filename.split('.').pop().toLowerCase()
  const icons = {
    pdf: 'icon-pdf',
    docx: 'icon-word',
    doc: 'icon-word',
    txt: 'icon-text',
    md: 'icon-markdown'
  }
  return icons[ext] || 'icon-file'
}

const getStatusIcon = (status) => {
  const icons = {
    pending: 'icon-clock',
    processing: 'icon-spinner',
    completed: 'icon-check',
    failed: 'icon-error'
  }
  return icons[status] || 'icon-question'
}

const getStatusText = (status) => {
  const texts = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '处理失败'
  }
  return texts[status] || status
}

const getUploadStatusText = (status) => {
  const texts = {
    uploading: '上传中',
    processing: '处理中',
    completed: '完成',
    failed: '失败'
  }
  return texts[status] || status
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', {
    hour12: false
  })
}

const handleFileSelect = async (event) => {
  const files = Array.from(event.target.files)
  if (files.length === 0) return

  // 验证文件类型和大小
  const allowedTypes = ['.pdf', '.docx', '.doc', '.txt', '.md']
  const maxSize = 50 * 1024 * 1024 // 50MB

  for (const file of files) {
    const fileExt = '.' + file.name.split('.').pop().toLowerCase()

    if (!allowedTypes.includes(fileExt)) {
      alert(`不支持的文件类型: ${file.name}`)
      continue
    }

    if (file.size > maxSize) {
      alert(`文件过大: ${file.name} (${formatFileSize(file.size)})`)
      continue
    }

    // 添加到上传队列
    const uploadId = Date.now() + Math.random()
    uploadQueue.value.push({
      id: uploadId,
      file: file,
      status: 'uploading',
      progress: 0,
      jobId: null
    })

    // 开始上传
    uploadFile(uploadId, file)
  }

  // 清空文件输入
  event.target.value = ''
}

const uploadFile = async (uploadId, file) => {
  try {
    // 更新状态
    const upload = uploadQueue.value.find(u => u.id === uploadId)
    if (!upload) return

    upload.status = 'uploading'
    upload.progress = 0

    // 上传文件
    const result = await ragAPI.uploadDocument(file)

    // 更新状态
    upload.status = 'processing'
    upload.jobId = result.job_id

    // 开始监控处理进度
    monitorUploadProgress(uploadId, result.job_id)

  } catch (error) {
    console.error('文件上传失败:', error)
    const upload = uploadQueue.value.find(u => u.id === uploadId)
    if (upload) {
      upload.status = 'failed'
      upload.error = error.message
    }
  }
}

const monitorUploadProgress = async (uploadId, jobId) => {
  const checkStatus = async () => {
    try {
      const status = await ragAPI.getDocumentStatus(jobId)
      const upload = uploadQueue.value.find(u => u.id === uploadId)

      if (upload) {
        upload.status = status.status
        upload.progress = status.result?.progress || 0

        if (status.status === 'completed' || status.status === 'failed') {
          // 处理完成，从队列移除
          setTimeout(() => {
            const index = uploadQueue.value.findIndex(u => u.id === uploadId)
            if (index > -1) {
              uploadQueue.value.splice(index, 1)
            }
            // 重新加载文档列表
            loadDocuments()
          }, 2000)
          return
        }

        // 继续监控
        setTimeout(checkStatus, 2000)
      }
    } catch (error) {
      console.error('检查上传状态失败:', error)
    }
  }

  checkStatus()
}

const loadDocuments = async () => {
  loading.value = true
  try {
    const result = await ragAPI.getDocuments(1, 50)
    documents.value = result.documents || []
  } catch (error) {
    console.error('加载文档列表失败:', error)
    documents.value = []
  } finally {
    loading.value = false
  }
}

const viewDocument = (jobId) => {
  // 这里可以跳转到文档详情页面或在侧边栏显示
  emit('document-selected', jobId)
}

const searchInDocument = (jobId) => {
  emit('search-in-document', jobId)
}

const retryDocument = async (jobId) => {
  retrying.value = jobId
  try {
    await ragAPI.retryDocument(jobId)
    // 重新加载文档列表
    await loadDocuments()
  } catch (error) {
    console.error('重试文档处理失败:', error)
    alert('重试失败，请稍后再试')
  } finally {
    retrying.value = null
  }
}

const deleteDocument = async (jobId) => {
  if (!confirm('确定要删除这个文档吗？')) return

  deleting.value = jobId
  try {
    await ragAPI.deleteDocument(jobId)
    // 从列表中移除
    documents.value = documents.value.filter(doc => doc.job_id !== jobId)
  } catch (error) {
    console.error('删除文档失败:', error)
    alert('删除失败，请稍后再试')
  } finally {
    deleting.value = null
  }
}

// Lifecycle
onMounted(() => {
  loadDocuments()
})
</script>

<style scoped>
.document-manager {
  background: var(--primary-bg);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.manager-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  background: var(--secondary-bg);
}

.manager-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.manager-actions {
  display: flex;
  gap: 8px;
}

.btn-upload, .btn-refresh, .btn-upload-large {
  padding: 8px 16px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--accent-color);
  color: white;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-upload:hover, .btn-refresh:hover, .btn-upload-large:hover {
  background: var(--accent-hover);
  transform: translateY(-1px);
}

.btn-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.upload-progress {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  background: var(--secondary-bg);
}

.upload-progress h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: var(--text-primary);
}

.upload-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color);
}

.upload-item:last-child {
  border-bottom: none;
}

.upload-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.upload-filename {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.upload-size {
  font-size: 12px;
  color: var(--text-secondary);
}

.upload-status {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-bar {
  width: 100px;
  height: 4px;
  background: var(--border-color);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--accent-color);
  transition: width 0.3s;
}

.status-text {
  font-size: 12px;
  color: var(--text-secondary);
  min-width: 60px;
}

.btn-view {
  padding: 4px 8px;
  border: 1px solid var(--accent-color);
  border-radius: 3px;
  background: var(--accent-color);
  color: white;
  font-size: 12px;
  cursor: pointer;
}

.btn-view:hover {
  background: var(--accent-hover);
}

.documents-list {
  padding: 20px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  gap: 20px;
}

.search-box {
  position: relative;
  flex: 1;
  max-width: 300px;
}

.search-box input {
  width: 100%;
  padding: 8px 12px 8px 32px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--primary-bg);
  color: var(--text-primary);
  font-size: 14px;
}

.search-box .icon-search {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-secondary);
}

.filter-tabs {
  display: flex;
  gap: 4px;
}

.tab-btn {
  padding: 6px 12px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--primary-bg);
  color: var(--text-primary);
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: var(--hover-bg);
}

.tab-btn.active {
  background: var(--accent-color);
  color: white;
  border-color: var(--accent-color);
}

.documents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.document-card {
  background: var(--secondary-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.2s;
}

.document-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.document-card.completed {
  border-left: 3px solid var(--success-color);
}

.document-card.failed {
  border-left: 3px solid var(--error-color);
}

.card-header {
  display: flex;
  gap: 12px;
  padding: 16px;
}

.document-icon {
  width: 40px;
  height: 40px;
  border-radius: 6px;
  background: var(--accent-color);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
}

.document-info {
  flex: 1;
}

.document-title {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  word-break: break-word;
}

.document-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--text-secondary);
}

.card-body {
  padding: 0 16px 16px;
}

.processing-status {
  margin-bottom: 12px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 8px;
}

.status-indicator.pending {
  color: var(--warning-color);
}

.status-indicator.processing {
  color: var(--accent-color);
}

.status-indicator.completed {
  color: var(--success-color);
}

.status-indicator.failed {
  color: var(--error-color);
}

.progress-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-bar {
  flex: 1;
  height: 4px;
  background: var(--border-color);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--accent-color);
  transition: width 0.3s;
}

.progress-text {
  font-size: 11px;
  color: var(--text-secondary);
  min-width: 32px;
}

.error-message {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 8px 12px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 4px;
  font-size: 12px;
  color: var(--error-color);
  margin-bottom: 12px;
}

.processing-result {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}

.result-item {
  display: flex;
  justify-content: space-between;
}

.result-label {
  font-weight: 500;
}

.result-value {
  color: var(--text-primary);
}

.card-actions {
  display: flex;
  gap: 6px;
  padding: 12px 16px;
  border-top: 1px solid var(--border-color);
  background: var(--primary-bg);
}

.btn-search, .btn-retry, .btn-delete {
  flex: 1;
  padding: 6px 12px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--primary-bg);
  color: var(--text-primary);
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  transition: all 0.2s;
}

.btn-search:hover {
  background: var(--accent-color);
  color: white;
}

.btn-retry:hover {
  background: var(--warning-color);
  color: white;
}

.btn-delete:hover {
  background: var(--error-color);
  color: white;
}

.btn-search:disabled, .btn-retry:disabled, .btn-delete:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.no-documents {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}

.no-documents i {
  font-size: 64px;
  margin-bottom: 20px;
  opacity: 0.5;
}

.no-documents h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: var(--text-primary);
}

.no-documents p {
  margin: 0 0 20px 0;
  font-size: 14px;
}

.btn-upload-large {
  margin: 0 auto;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
