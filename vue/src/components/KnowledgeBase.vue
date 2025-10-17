<template>
  <div class="knowledge-base">
    <div class="kb-header">
      <h2>知识库管理</h2>
      <div class="header-actions">
        <button @click="showCreateModal = true" class="btn btn-primary">
          ➕ 新建知识库
        </button>
        <button @click="showImportModal = true" class="btn btn-outline">
          📥 导入知识库
        </button>
        <button @click="refreshKnowledgeBases" class="btn btn-outline" :disabled="loading">
          🔄 刷新
        </button>
      </div>
    </div>

    <div class="kb-content">
      <div class="kb-sidebar">
        <div class="search-section">
          <div class="search-box">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索知识库..."
              class="search-input"
            />
            <button @click="searchKnowledgeBases" class="search-btn">🔍</button>
          </div>
        </div>

        <div class="filter-section">
          <h3>筛选条件</h3>
          <div class="filter-group">
            <label>类型</label>
            <select v-model="typeFilter" class="filter-select">
              <option value="">全部</option>
              <option value="document">文档知识库</option>
              <option value="web">网页知识库</option>
              <option value="qa">问答知识库</option>
              <option value="mixed">混合知识库</option>
            </select>
          </div>

          <div class="filter-group">
            <label>状态</label>
            <select v-model="statusFilter" class="filter-select">
              <option value="">全部</option>
              <option value="active">活跃</option>
              <option value="training">训练中</option>
              <option value="inactive">未激活</option>
            </select>
          </div>

          <div class="filter-group">
            <label>标签</label>
            <div class="tag-filter">
              <span
                v-for="tag in availableTags"
                :key="tag"
                class="tag-chip"
                :class="{ active: selectedTags.includes(tag) }"
                @click="toggleTag(tag)"
              >
                {{ tag }}
              </span>
            </div>
          </div>
        </div>

        <div class="stats-section">
          <h3>统计信息</h3>
          <div class="stat-item">
            <span class="stat-label">知识库总数:</span>
            <span class="stat-value">{{ knowledgeBases.length }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">文档总数:</span>
            <span class="stat-value">{{ totalDocuments }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">存储空间:</span>
            <span class="stat-value">{{ totalStorage }}</span>
          </div>
        </div>
      </div>

      <div class="kb-main">
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner">⟳</div>
          <p>加载知识库...</p>
        </div>

        <div v-else-if="filteredKnowledgeBases.length === 0" class="empty-state">
          <div class="empty-icon">📚</div>
          <h3>暂无知识库</h3>
          <p>创建您的第一个知识库来开始管理文档和知识</p>
          <button @click="showCreateModal = true" class="btn btn-primary">
            创建知识库
          </button>
        </div>

        <div v-else class="kb-grid">
          <div
            v-for="kb in filteredKnowledgeBases"
            :key="kb.id"
            class="kb-card"
            :class="{ active: selectedKbId === kb.id }"
            @click="selectKnowledgeBase(kb.id)"
          >
            <div class="kb-card-header">
              <div class="kb-icon">
                <span :class="getKbIcon(kb.type)">{{ getKbIconEmoji(kb.type) }}</span>
              </div>
              <div class="kb-status">
                <span class="status-badge" :class="kb.status">{{ getStatusText(kb.status) }}</span>
              </div>
            </div>

            <div class="kb-card-body">
              <h3 class="kb-title">{{ kb.name }}</h3>
              <p class="kb-description">{{ kb.description }}</p>

              <div class="kb-meta">
                <div class="meta-item">
                  <span class="meta-icon">📄</span>
                  <span>{{ kb.document_count }} 文档</span>
                </div>
                <div class="meta-item">
                  <span class="meta-icon">🏷️</span>
                  <span>{{ kb.tags.length }} 标签</span>
                </div>
                <div class="meta-item">
                  <span class="meta-icon">📅</span>
                  <span>{{ formatDate(kb.updated_at) }}</span>
                </div>
              </div>

              <div v-if="kb.tags.length > 0" class="kb-tags">
                <span v-for="tag in kb.tags.slice(0, 3)" :key="tag" class="tag">
                  {{ tag }}
                </span>
                <span v-if="kb.tags.length > 3" class="tag-more">
                  +{{ kb.tags.length - 3 }}
                </span>
              </div>
            </div>

            <div class="kb-card-footer">
              <div class="kb-actions">
                <button @click.stop="searchInKb(kb)" class="action-btn" title="搜索">
                  🔍
                </button>
                <button @click.stop="editKb(kb)" class="action-btn" title="编辑">
                  ✏️
                </button>
                <button @click.stop="exportKb(kb)" class="action-btn" title="导出">
                  📤
                </button>
                <button @click.stop="deleteKb(kb)" class="action-btn danger" title="删除">
                  🗑️
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建知识库模态框 -->
    <div v-if="showCreateModal" class="modal-overlay" @click="closeCreateModal">
      <div class="modal-content large" @click.stop>
        <div class="modal-header">
          <h3>创建知识库</h3>
          <button @click="closeCreateModal" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>知识库名称 *</label>
            <input
              v-model="newKb.name"
              type="text"
              placeholder="输入知识库名称"
              class="form-input"
              required
            />
          </div>

          <div class="form-group">
            <label>描述</label>
            <textarea
              v-model="newKb.description"
              placeholder="描述知识库的用途和内容"
              class="form-textarea"
              rows="3"
            ></textarea>
          </div>

          <div class="form-group">
            <label>类型 *</label>
            <select v-model="newKb.type" class="form-select">
              <option value="">请选择类型</option>
              <option value="document">文档知识库</option>
              <option value="web">网页知识库</option>
              <option value="qa">问答知识库</option>
              <option value="mixed">混合知识库</option>
            </select>
          </div>

          <div class="form-group">
            <label>标签</label>
            <div class="tag-input">
              <input
                v-model="newTag"
                type="text"
                placeholder="添加标签后按回车"
                class="tag-input-field"
                @keyup.enter="addTag"
              />
              <button @click="addTag" class="btn btn-sm">添加</button>
            </div>
            <div class="tag-list">
              <span
                v-for="(tag, index) in newKb.tags"
                :key="index"
                class="tag removable"
                @click="removeTag(index)"
              >
                {{ tag }} ×
              </span>
            </div>
          </div>

          <div class="form-group">
            <label>初始文档</label>
            <div class="document-upload">
              <input
                type="file"
                ref="fileInput"
                multiple
                accept=".pdf,.doc,.docx,.txt,.md"
                @change="handleFileUpload"
                style="display: none"
              />
              <button @click="$refs.fileInput.click()" class="btn btn-outline">
                📁 选择文件
              </button>
              <span class="upload-hint">支持PDF、Word、文本等格式</span>
            </div>
            <div v-if="newKb.documents.length > 0" class="uploaded-files">
              <div v-for="(file, index) in newKb.documents" :key="index" class="file-item">
                <span class="file-name">{{ file.name }}</span>
                <button @click="removeFile(index)" class="remove-file">×</button>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeCreateModal" class="btn btn-outline">取消</button>
          <button @click="createKnowledgeBase" class="btn btn-primary" :disabled="!canCreateKb">
            创建知识库
          </button>
        </div>
      </div>
    </div>

    <!-- 导入知识库模态框 -->
    <div v-if="showImportModal" class="modal-overlay" @click="closeImportModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>导入知识库</h3>
          <button @click="closeImportModal" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div class="import-methods">
            <button @click="importFromFile" class="import-option">
              <span class="import-icon">📁</span>
              <div class="import-content">
                <h4>从文件导入</h4>
                <p>导入JSON、CSV等格式的知识库文件</p>
              </div>
            </button>
            <button @click="importFromUrl" class="import-option">
              <span class="import-icon">🌐</span>
              <div class="import-content">
                <h4>从URL导入</h4>
                <p>从在线URL导入知识库数据</p>
              </div>
            </button>
            <button @click="importFromApi" class="import-option">
              <span class="import-icon">🔌</span>
              <div class="import-content">
                <h4>从API导入</h4>
                <p>通过API接口导入外部知识库</p>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 知识库详情模态框 -->
    <div v-if="showDetailModal" class="modal-overlay" @click="closeDetailModal">
      <div class="modal-content large" @click.stop>
        <div class="modal-header">
          <h3>{{ selectedKb?.name }}</h3>
          <button @click="closeDetailModal" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div v-if="selectedKb" class="kb-detail">
            <div class="detail-section">
              <h4>基本信息</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <span class="detail-label">类型:</span>
                  <span class="detail-value">{{ getTypeText(selectedKb.type) }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">状态:</span>
                  <span class="detail-value">
                    <span class="status-badge" :class="selectedKb.status">
                      {{ getStatusText(selectedKb.status) }}
                    </span>
                  </span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">创建时间:</span>
                  <span class="detail-value">{{ formatDate(selectedKb.created_at) }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">更新时间:</span>
                  <span class="detail-value">{{ formatDate(selectedKb.updated_at) }}</span>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <h4>描述</h4>
              <p class="kb-description-full">{{ selectedKb.description }}</p>
            </div>

            <div class="detail-section">
              <h4>标签</h4>
              <div class="kb-tags-full">
                <span v-for="tag in selectedKb.tags" :key="tag" class="tag">
                  {{ tag }}
                </span>
              </div>
            </div>

            <div class="detail-section">
              <h4>文档列表</h4>
              <div class="document-list">
                <div v-for="doc in selectedKb.documents" :key="doc.id" class="document-item">
                  <div class="document-info">
                    <span class="document-name">{{ doc.name }}</span>
                    <span class="document-size">{{ formatFileSize(doc.size) }}</span>
                    <span class="document-date">{{ formatDate(doc.uploaded_at) }}</span>
                  </div>
                  <div class="document-actions">
                    <button @click="previewDocument(doc)" class="btn btn-xs btn-outline">
                      预览
                    </button>
                    <button @click="downloadDocument(doc)" class="btn btn-xs btn-outline">
                      下载
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const knowledgeBases = ref([])
const selectedKbId = ref('')
const selectedKb = ref(null)
const searchQuery = ref('')
const typeFilter = ref('')
const statusFilter = ref('')
const selectedTags = ref([])

// 模态框状态
const showCreateModal = ref(false)
const showImportModal = ref(false)
const showDetailModal = ref(false)

// 新知识库数据
const newKb = ref({
  name: '',
  description: '',
  type: '',
  tags: [],
  documents: []
})
const newTag = ref('')

// 模拟数据
const mockKnowledgeBases = [
  {
    id: 'kb_001',
    name: '机器学习研究库',
    description: '收集机器学习相关论文、算法和实现代码',
    type: 'document',
    status: 'active',
    document_count: 156,
    tags: ['机器学习', 'AI', '算法'],
    created_at: new Date('2024-01-15'),
    updated_at: new Date('2024-03-20'),
    documents: [
      { id: 'doc_001', name: '深度学习基础.pdf', size: 2048576, uploaded_at: new Date('2024-03-01') },
      { id: 'doc_002', name: '神经网络架构.docx', size: 1048576, uploaded_at: new Date('2024-03-05') }
    ]
  },
  {
    id: 'kb_002',
    name: '产品文档库',
    description: '公司产品相关文档和用户手册',
    type: 'document',
    status: 'active',
    document_count: 89,
    tags: ['产品', '文档', '手册'],
    created_at: new Date('2024-02-01'),
    updated_at: new Date('2024-03-18'),
    documents: [
      { id: 'doc_003', name: '产品使用指南.pdf', size: 5242880, uploaded_at: new Date('2024-02-15') }
    ]
  },
  {
    id: 'kb_003',
    name: '技术问答库',
    description: '常见技术问题和解答集合',
    type: 'qa',
    status: 'training',
    document_count: 234,
    tags: ['问答', '技术', 'FAQ'],
    created_at: new Date('2024-01-20'),
    updated_at: new Date('2024-03-19'),
    documents: []
  }
]

// 计算属性
const availableTags = computed(() => {
  const allTags = new Set()
  knowledgeBases.value.forEach(kb => {
    kb.tags.forEach(tag => allTags.add(tag))
  })
  return Array.from(allTags)
})

const filteredKnowledgeBases = computed(() => {
  let filtered = knowledgeBases.value

  // 搜索筛选
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(kb =>
      kb.name.toLowerCase().includes(query) ||
      kb.description.toLowerCase().includes(query)
    )
  }

  // 类型筛选
  if (typeFilter.value) {
    filtered = filtered.filter(kb => kb.type === typeFilter.value)
  }

  // 状态筛选
  if (statusFilter.value) {
    filtered = filtered.filter(kb => kb.status === statusFilter.value)
  }

  // 标签筛选
  if (selectedTags.value.length > 0) {
    filtered = filtered.filter(kb =>
      selectedTags.value.some(tag => kb.tags.includes(tag))
    )
  }

  return filtered
})

const totalDocuments = computed(() => {
  return knowledgeBases.value.reduce((sum, kb) => sum + kb.document_count, 0)
})

const totalStorage = computed(() => {
  // 模拟存储空间计算
  const totalBytes = totalDocuments.value * 1024 * 1024 // 假设每个文档1MB
  return formatFileSize(totalBytes)
})

const canCreateKb = computed(() => {
  return newKb.value.name.trim() && newKb.value.type
})

// 方法
const loadKnowledgeBases = async () => {
  loading.value = true
  try {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 500))
    knowledgeBases.value = mockKnowledgeBases
  } catch (error) {
    console.error('加载知识库失败:', error)
  } finally {
    loading.value = false
  }
}

const refreshKnowledgeBases = () => {
  loadKnowledgeBases()
}

const selectKnowledgeBase = (kbId) => {
  selectedKbId.value = kbId
  selectedKb.value = knowledgeBases.value.find(kb => kb.id === kbId)
  showDetailModal.value = true
}

const searchKnowledgeBases = () => {
  // 搜索逻辑已在计算属性中实现
}

const toggleTag = (tag) => {
  const index = selectedTags.value.indexOf(tag)
  if (index > -1) {
    selectedTags.value.splice(index, 1)
  } else {
    selectedTags.value.push(tag)
  }
}

const getKbIcon = (type) => {
  return `kb-icon-${type}`
}

const getKbIconEmoji = (type) => {
  const icons = {
    document: '📄',
    web: '🌐',
    qa: '❓',
    mixed: '🔄'
  }
  return icons[type] || '📚'
}

const getStatusText = (status) => {
  const statusMap = {
    active: '活跃',
    training: '训练中',
    inactive: '未激活'
  }
  return statusMap[status] || status
}

const getTypeText = (type) => {
  const typeMap = {
    document: '文档知识库',
    web: '网页知识库',
    qa: '问答知识库',
    mixed: '混合知识库'
  }
  return typeMap[type] || type
}

const formatDate = (date) => {
  return date.toLocaleDateString('zh-CN')
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const searchInKb = (kb) => {
  // 跳转到搜索页面并预选知识库
  router.push({
    name: 'search',
    query: { kb: kb.id }
  })
}

const editKb = (kb) => {
  // 编辑知识库功能
  console.log('编辑知识库:', kb)
}

const exportKb = (kb) => {
  // 导出知识库功能
  console.log('导出知识库:', kb)
}

const deleteKb = (kb) => {
  if (confirm(`确定要删除知识库 "${kb.name}" 吗？此操作不可恢复。`)) {
    const index = knowledgeBases.value.findIndex(item => item.id === kb.id)
    if (index > -1) {
      knowledgeBases.value.splice(index, 1)
    }
  }
}

// 创建知识库相关方法
const addTag = () => {
  if (newTag.value.trim() && !newKb.value.tags.includes(newTag.value.trim())) {
    newKb.value.tags.push(newTag.value.trim())
    newTag.value = ''
  }
}

const removeTag = (index) => {
  newKb.value.tags.splice(index, 1)
}

const handleFileUpload = (event) => {
  const files = Array.from(event.target.files)
  newKb.value.documents.push(...files)
}

const removeFile = (index) => {
  newKb.value.documents.splice(index, 1)
}

const createKnowledgeBase = async () => {
  try {
    const newKbData = {
      ...newKb.value,
      id: `kb_${Date.now()}`,
      status: 'training',
      document_count: newKb.value.documents.length,
      created_at: new Date(),
      updated_at: new Date()
    }

    knowledgeBases.value.push(newKbData)
    closeCreateModal()

    // 重置表单
    newKb.value = {
      name: '',
      description: '',
      type: '',
      tags: [],
      documents: []
    }
  } catch (error) {
    console.error('创建知识库失败:', error)
  }
}

// 导入相关方法
const importFromFile = () => {
  console.log('从文件导入')
  closeImportModal()
}

const importFromUrl = () => {
  console.log('从URL导入')
  closeImportModal()
}

const importFromApi = () => {
  console.log('从API导入')
  closeImportModal()
}

// 文档操作方法
const previewDocument = (doc) => {
  console.log('预览文档:', doc)
}

const downloadDocument = (doc) => {
  console.log('下载文档:', doc)
}

// 模态框控制方法
const closeCreateModal = () => {
  showCreateModal.value = false
}

const closeImportModal = () => {
  showImportModal.value = false
}

const closeDetailModal = () => {
  showDetailModal.value = false
  selectedKb.value = null
}

// 监听筛选条件变化
watch([searchQuery, typeFilter, statusFilter, selectedTags], () => {
  // 筛选逻辑已在计算属性中实现
})

// 生命周期
onMounted(() => {
  loadKnowledgeBases()
})
</script>

<style scoped>
.knowledge-base {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}

.kb-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  background: white;
  border-bottom: 1px solid #e1e8ed;
}

.kb-header h2 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.5rem;
}

.header-actions {
  display: flex;
  gap: 1rem;
}

.kb-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.kb-sidebar {
  width: 300px;
  background: white;
  border-right: 1px solid #e1e8ed;
  padding: 1.5rem;
  overflow-y: auto;
}

.search-section {
  margin-bottom: 2rem;
}

.search-box {
  display: flex;
  gap: 0.5rem;
}

.search-input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.9rem;
}

.search-btn {
  padding: 0.75rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.filter-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  color: #2c3e50;
}

.filter-group {
  margin-bottom: 1.5rem;
}

.filter-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #5a6c7d;
}

.filter-select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.tag-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag-chip {
  padding: 0.25rem 0.75rem;
  background: #f1f3f4;
  border: 1px solid #ddd;
  border-radius: 16px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tag-chip.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.stats-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  color: #2c3e50;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  font-size: 0.9rem;
}

.stat-label {
  color: #5a6c7d;
}

.stat-value {
  font-weight: 600;
  color: #2c3e50;
}

.kb-main {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #5a6c7d;
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
  height: 400px;
  text-align: center;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-state h3 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.empty-state p {
  margin: 0 0 2rem 0;
  color: #5a6c7d;
}

.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.kb-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
}

.kb-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.kb-card.active {
  border: 2px solid #667eea;
}

.kb-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #f8f9fa;
}

.kb-icon {
  font-size: 1.5rem;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}

.status-badge.active {
  background: #d4edda;
  color: #155724;
}

.status-badge.training {
  background: #fff3cd;
  color: #856404;
}

.status-badge.inactive {
  background: #f8d7da;
  color: #721c24;
}

.kb-card-body {
  padding: 1.5rem;
}

.kb-title {
  margin: 0 0 0.75rem 0;
  font-size: 1.2rem;
  color: #2c3e50;
}

.kb-description {
  margin: 0 0 1rem 0;
  color: #5a6c7d;
  line-height: 1.5;
}

.kb-meta {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  font-size: 0.9rem;
  color: #5a6c7d;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.meta-icon {
  font-size: 0.8rem;
}

.kb-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag {
  padding: 0.25rem 0.5rem;
  background: #e3f2fd;
  color: #1976d2;
  border-radius: 4px;
  font-size: 0.8rem;
}

.tag-more {
  padding: 0.25rem 0.5rem;
  background: #f5f5f5;
  color: #666;
  border-radius: 4px;
  font-size: 0.8rem;
}

.kb-card-footer {
  padding: 1rem;
  background: #f8f9fa;
  border-top: 1px solid #e1e8ed;
}

.kb-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.action-btn {
  padding: 0.5rem;
  background: none;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.action-btn:hover {
  background: #e9ecef;
}

.action-btn.danger:hover {
  background: #f8d7da;
  color: #721c24;
}

/* 按钮样式 */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem 1.5rem;
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
  padding: 0.5rem 1rem;
  font-size: 0.8rem;
}

.btn-xs {
  padding: 0.25rem 0.75rem;
  font-size: 0.75rem;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #5a6fd8;
}

.btn-outline {
  background: transparent;
  color: #667eea;
  border: 1px solid #667eea;
}

.btn-outline:hover:not(:disabled) {
  background: #667eea;
  color: white;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-content.large {
  max-width: 800px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e1e8ed;
}

.modal-header h3 {
  margin: 0;
  color: #2c3e50;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #5a6c7d;
  padding: 0.25rem;
  border-radius: 4px;
}

.btn-close:hover {
  background: #f1f3f4;
}

.modal-body {
  padding: 1.5rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid #e1e8ed;
}

/* 表单样式 */
.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #2c3e50;
}

.form-input,
.form-textarea,
.form-select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.9rem;
}

.form-input:focus,
.form-textarea:focus,
.form-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

.tag-input {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.tag-input-field {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag.removable {
  padding: 0.25rem 0.75rem;
  background: #667eea;
  color: white;
  border-radius: 16px;
  font-size: 0.8rem;
  cursor: pointer;
}

.document-upload {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.upload-hint {
  font-size: 0.8rem;
  color: #5a6c7d;
}

.uploaded-files {
  margin-top: 1rem;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 4px;
  margin-bottom: 0.5rem;
}

.remove-file {
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  cursor: pointer;
  font-size: 0.8rem;
}

/* 导入选项 */
.import-methods {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.import-option {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  background: #f8f9fa;
  border: 1px solid #e1e8ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.import-option:hover {
  background: #e3f2fd;
  border-color: #667eea;
}

.import-icon {
  font-size: 2rem;
}

.import-content h4 {
  margin: 0 0 0.25rem 0;
  color: #2c3e50;
}

.import-content p {
  margin: 0;
  color: #5a6c7d;
  font-size: 0.9rem;
}

/* 知识库详情样式 */
.kb-detail {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.detail-section h4 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.detail-label {
  font-size: 0.9rem;
  color: #5a6c7d;
}

.detail-value {
  font-weight: 600;
  color: #2c3e50;
}

.kb-description-full {
  line-height: 1.6;
  color: #5a6c7d;
}

.kb-tags-full {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.document-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.document-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 6px;
}

.document-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.document-name {
  font-weight: 600;
  color: #2c3e50;
}

.document-size,
.document-date {
  font-size: 0.8rem;
  color: #5a6c7d;
}

.document-actions {
  display: flex;
  gap: 0.5rem;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .kb-content {
    flex-direction: column;
  }

  .kb-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #e1e8ed;
  }
}

@media (max-width: 768px) {
  .kb-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .header-actions {
    justify-content: center;
  }

  .kb-main {
    padding: 1rem;
  }

  .kb-grid {
    grid-template-columns: 1fr;
  }

  .modal-content {
    width: 95%;
    margin: 1rem;
  }
}

@media (max-width: 480px) {
  .kb-sidebar {
    padding: 1rem;
  }

  .kb-main {
    padding: 0.5rem;
  }

  .kb-meta {
    flex-direction: column;
    gap: 0.5rem;
  }

  .kb-actions {
    justify-content: center;
  }
}
</style>