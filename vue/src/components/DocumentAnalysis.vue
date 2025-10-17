<template>
  <div class="document-analysis">
    <div class="analysis-header">
      <h2>文档分析</h2>
      <div class="header-actions">
        <button @click="showUploadModal = true" class="btn btn-primary">
          📄 上传文档
        </button>
        <button @click="batchAnalysis" class="btn btn-outline" :disabled="!selectedDocuments.length">
          🔍 批量分析
        </button>
        <button @click="refreshDocuments" class="btn btn-outline" :disabled="loading">
          🔄 刷新
        </button>
      </div>
    </div>

    <div class="analysis-content">
      <div class="analysis-sidebar">
        <div class="upload-section">
          <div class="upload-area" :class="{ 'drag-over': isDragOver }" @dragover.prevent @dragleave.prevent @drop.prevent="handleDrop">
            <input
              type="file"
              ref="fileInput"
              multiple
              accept=".pdf,.doc,.docx,.txt,.md,.ppt,.pptx,.xls,.xlsx,.png,.jpg,.jpeg"
              @change="handleFileSelect"
              style="display: none"
            />
            <div class="upload-content">
              <div class="upload-icon">📁</div>
              <h3>拖拽文件到此处</h3>
              <p>或点击选择文件</p>
              <button @click="$refs.fileInput.click()" class="btn btn-outline">
                选择文件
              </button>
            </div>
          </div>
        </div>

        <div class="filter-section">
          <h3>筛选条件</h3>
          <div class="filter-group">
            <label>分析状态</label>
            <select v-model="statusFilter" class="filter-select">
              <option value="">全部</option>
              <option value="pending">待分析</option>
              <option value="analyzing">分析中</option>
              <option value="completed">已完成</option>
              <option value="failed">失败</option>
            </select>
          </div>

          <div class="filter-group">
            <label>文档类型</label>
            <select v-model="typeFilter" class="filter-select">
              <option value="">全部</option>
              <option value="pdf">PDF</option>
              <option value="doc">Word文档</option>
              <option value="txt">文本文件</option>
              <option value="ppt">演示文稿</option>
              <option value="excel">电子表格</option>
              <option value="image">图片</option>
            </select>
          </div>

          <div class="filter-group">
            <label>分析类型</label>
            <div class="checkbox-group">
              <label v-for="type in analysisTypes" :key="type.value" class="checkbox-label">
                <input
                  type="checkbox"
                  :value="type.value"
                  v-model="selectedAnalysisTypes"
                />
                <span>{{ type.label }}</span>
              </label>
            </div>
          </div>
        </div>

        <div class="stats-section">
          <h3>分析统计</h3>
          <div class="stat-item">
            <span class="stat-label">总文档数:</span>
            <span class="stat-value">{{ documents.length }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">已分析:</span>
            <span class="stat-value">{{ completedAnalysis }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">分析中:</span>
            <span class="stat-value">{{ analyzingCount }}</span>
          </div>
        </div>
      </div>

      <div class="analysis-main">
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner">⟳</div>
          <p>加载文档列表...</p>
        </div>

        <div v-else-if="filteredDocuments.length === 0" class="empty-state">
          <div class="empty-icon">📄</div>
          <h3>暂无文档</h3>
          <p>上传文档开始分析</p>
          <button @click="showUploadModal = true" class="btn btn-primary">
            上传文档
          </button>
        </div>

        <div v-else class="document-list">
          <div class="list-header">
            <div class="list-actions">
              <input
                type="checkbox"
                v-model="selectAll"
                @change="toggleSelectAll"
                class="select-all"
              />
              <span>全选</span>
            </div>
            <div class="list-sort">
              <select v-model="sortBy" class="sort-select">
                <option value="updated_at">按更新时间</option>
                <option value="name">按名称</option>
                <option value="size">按大小</option>
                <option value="status">按状态</option>
              </select>
            </div>
          </div>

          <div
            v-for="doc in sortedDocuments"
            :key="doc.id"
            class="document-item"
            :class="{ selected: selectedDocuments.includes(doc.id) }"
          >
            <div class="document-checkbox">
              <input
                type="checkbox"
                :value="doc.id"
                v-model="selectedDocuments"
              />
            </div>

            <div class="document-preview" @click="viewDocument(doc)">
              <div class="preview-icon">
                <span :class="getFileIcon(doc.type)">{{ getFileEmoji(doc.type) }}</span>
              </div>
              <div v-if="doc.thumbnail" class="preview-image">
                <img :src="doc.thumbnail" :alt="doc.name" />
              </div>
            </div>

            <div class="document-info" @click="viewDocument(doc)">
              <h4 class="document-name">{{ doc.name }}</h4>
              <div class="document-meta">
                <span class="meta-item">
                  <span class="meta-icon">📄</span>
                  {{ doc.type.toUpperCase() }}
                </span>
                <span class="meta-item">
                  <span class="meta-icon">📏</span>
                  {{ formatFileSize(doc.size) }}
                </span>
                <span class="meta-item">
                  <span class="meta-icon">📅</span>
                  {{ formatDate(doc.updated_at) }}
                </span>
              </div>
              <div v-if="doc.tags.length > 0" class="document-tags">
                <span v-for="tag in doc.tags.slice(0, 3)" :key="tag" class="tag">
                  {{ tag }}
                </span>
                <span v-if="doc.tags.length > 3" class="tag-more">
                  +{{ doc.tags.length - 3 }}
                </span>
              </div>
            </div>

            <div class="document-status">
              <span class="status-badge" :class="doc.analysis_status">
                {{ getStatusText(doc.analysis_status) }}
              </span>
              <div v-if="doc.analysis_progress" class="progress-bar">
                <div
                  class="progress-fill"
                  :style="{ width: `${doc.analysis_progress}%` }"
                ></div>
              </div>
            </div>

            <div class="document-actions">
              <button @click="analyzeDocument(doc)" class="action-btn" title="分析">
                🔍
              </button>
              <button @click="downloadDocument(doc)" class="action-btn" title="下载">
                📥
              </button>
              <button @click="shareDocument(doc)" class="action-btn" title="分享">
                🔗
              </button>
              <button @click="deleteDocument(doc)" class="action-btn danger" title="删除">
                🗑️
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 文档上传模态框 -->
    <div v-if="showUploadModal" class="modal-overlay" @click="closeUploadModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>上传文档</h3>
          <button @click="closeUploadModal" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div class="upload-options">
            <div class="upload-option" @click="$refs.fileInput.click()">
              <span class="upload-icon">📁</span>
              <div class="upload-content">
                <h4>从本地上传</h4>
                <p>选择本地文件上传</p>
              </div>
            </div>
            <div class="upload-option" @click="uploadFromUrl">
              <span class="upload-icon">🌐</span>
              <div class="upload-content">
                <h4>从URL上传</h4>
                <p>通过URL链接上传文档</p>
              </div>
            </div>
            <div class="upload-option" @click="uploadFromApi">
              <span class="upload-icon">🔌</span>
              <div class="upload-content">
                <h4>API导入</h4>
                <p>通过API接口导入文档</p>
              </div>
            </div>
          </div>

          <div v-if="uploadedFiles.length > 0" class="uploaded-files">
            <h4>待上传文件</h4>
            <div class="file-list">
              <div v-for="(file, index) in uploadedFiles" :key="index" class="file-item">
                <div class="file-info">
                  <span class="file-name">{{ file.name }}</span>
                  <span class="file-size">{{ formatFileSize(file.size) }}</span>
                </div>
                <div class="file-actions">
                  <button @click="removeUploadedFile(index)" class="remove-btn">×</button>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeUploadModal" class="btn btn-outline">取消</button>
          <button @click="confirmUpload" class="btn btn-primary" :disabled="!uploadedFiles.length">
            上传文档
          </button>
        </div>
      </div>
    </div>

    <!-- 文档分析结果模态框 -->
    <div v-if="showAnalysisModal" class="modal-overlay" @click="closeAnalysisModal">
      <div class="modal-content large" @click.stop>
        <div class="modal-header">
          <h3>文档分析结果 - {{ analysisResult?.document_name }}</h3>
          <button @click="closeAnalysisModal" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div v-if="analysisResult" class="analysis-result">
            <div class="result-tabs">
              <button
                v-for="tab in resultTabs"
                :key="tab.key"
                class="tab-btn"
                :class="{ active: activeTab === tab.key }"
                @click="activeTab = tab.key"
              >
                {{ tab.label }}
              </button>
            </div>

            <div class="tab-content">
              <!-- 摘要标签页 -->
              <div v-if="activeTab === 'summary'" class="tab-pane">
                <div class="summary-section">
                  <h4>文档摘要</h4>
                  <div class="summary-content">
                    <p>{{ analysisResult.summary }}</p>
                  </div>
                </div>

                <div class="key-points-section">
                  <h4>关键要点</h4>
                  <ul class="key-points-list">
                    <li v-for="point in analysisResult.key_points" :key="point">
                      {{ point }}
                    </li>
                  </ul>
                </div>

                <div class="topics-section">
                  <h4>主要话题</h4>
                  <div class="topics-list">
                    <span v-for="topic in analysisResult.topics" :key="topic" class="topic-tag">
                      {{ topic }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- 内容提取标签页 -->
              <div v-if="activeTab === 'extraction'" class="tab-pane">
                <div class="extraction-section">
                  <h4>文本内容</h4>
                  <div class="text-content">
                    <pre>{{ analysisResult.extracted_text }}</pre>
                  </div>
                </div>

                <div v-if="analysisResult.tables.length > 0" class="tables-section">
                  <h4>表格数据</h4>
                  <div class="tables-list">
                    <div v-for="(table, index) in analysisResult.tables" :key="index" class="table-item">
                      <h5>表格 {{ index + 1 }}</h5>
                      <div class="table-content">
                        <table class="extracted-table">
                          <thead>
                            <tr>
                              <th v-for="header in table.headers" :key="header">
                                {{ header }}
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr v-for="row in table.rows" :key="row.id">
                              <td v-for="cell in row.cells" :key="cell">
                                {{ cell }}
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                </div>

                <div v-if="analysisResult.images.length > 0" class="images-section">
                  <h4>图片内容</h4>
                  <div class="images-grid">
                    <div v-for="(image, index) in analysisResult.images" :key="index" class="image-item">
                      <img :src="image.url" :alt="image.description" />
                      <p class="image-description">{{ image.description }}</p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 语义分析标签页 -->
              <div v-if="activeTab === 'semantic'" class="tab-pane">
                <div class="sentiment-section">
                  <h4>情感分析</h4>
                  <div class="sentiment-result">
                    <div class="sentiment-score">
                      <div class="score-circle" :class="analysisResult.sentiment.label">
                        {{ analysisResult.sentiment.score }}
                      </div>
                      <span class="sentiment-label">{{ analysisResult.sentiment.label }}</span>
                    </div>
                  </div>
                </div>

                <div class="entities-section">
                  <h4>实体识别</h4>
                  <div class="entities-list">
                    <div v-for="entity in analysisResult.entities" :key="entity.text" class="entity-item">
                      <span class="entity-text">{{ entity.text }}</span>
                      <span class="entity-type">{{ entity.type }}</span>
                      <span class="entity-confidence">{{ entity.confidence }}%</span>
                    </div>
                  </div>
                </div>

                <div class="keywords-section">
                  <h4>关键词提取</h4>
                  <div class="keywords-cloud">
                    <span
                      v-for="keyword in analysisResult.keywords"
                      :key="keyword.word"
                      class="keyword"
                      :style="{ fontSize: `${keyword.size}px` }"
                    >
                      {{ keyword.word }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- 结构化数据标签页 -->
              <div v-if="activeTab === 'structure'" class="tab-pane">
                <div class="metadata-section">
                  <h4>文档元数据</h4>
                  <div class="metadata-grid">
                    <div class="metadata-item">
                      <span class="metadata-label">标题:</span>
                      <span class="metadata-value">{{ analysisResult.metadata.title }}</span>
                    </div>
                    <div class="metadata-item">
                      <span class="metadata-label">作者:</span>
                      <span class="metadata-value">{{ analysisResult.metadata.author }}</span>
                    </div>
                    <div class="metadata-item">
                      <span class="metadata-label">创建时间:</span>
                      <span class="metadata-value">{{ analysisResult.metadata.created_date }}</span>
                    </div>
                    <div class="metadata-item">
                      <span class="metadata-label">页数:</span>
                      <span class="metadata-value">{{ analysisResult.metadata.page_count }}</span>
                    </div>
                    <div class="metadata-item">
                      <span class="metadata-label">字数:</span>
                      <span class="metadata-value">{{ analysisResult.metadata.word_count }}</span>
                    </div>
                  </div>
                </div>

                <div class="outline-section">
                  <h4>文档大纲</h4>
                  <div class="outline-tree">
                    <div v-for="section in analysisResult.outline" :key="section.id" class="outline-item">
                      <span class="outline-level">{{ '  '.repeat(section.level - 1) }}</span>
                      <span class="outline-title">{{ section.title }}</span>
                      <span class="outline-page">p.{{ section.page }}</span>
                    </div>
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
import { ref, computed, onMounted } from 'vue'

// 响应式数据
const loading = ref(false)
const documents = ref([])
const selectedDocuments = ref([])
const statusFilter = ref('')
const typeFilter = ref('')
const selectedAnalysisTypes = ref([])
const sortBy = ref('updated_at')
const isDragOver = ref(false)

// 模态框状态
const showUploadModal = ref(false)
const showAnalysisModal = ref(false)
const uploadedFiles = ref([])
const analysisResult = ref(null)
const activeTab = ref('summary')

// 分析类型配置
const analysisTypes = [
  { value: 'summary', label: '摘要生成' },
  { value: 'extraction', label: '内容提取' },
  { value: 'semantic', label: '语义分析' },
  { value: 'structure', label: '结构分析' }
]

// 结果标签页配置
const resultTabs = [
  { key: 'summary', label: '摘要' },
  { key: 'extraction', label: '内容提取' },
  { key: 'semantic', label: '语义分析' },
  { key: 'structure', label: '结构数据' }
]

// 模拟文档数据
const mockDocuments = [
  {
    id: 'doc_001',
    name: '2024年技术趋势报告.pdf',
    type: 'pdf',
    size: 5242880,
    analysis_status: 'completed',
    analysis_progress: 100,
    tags: ['技术', '趋势', '2024'],
    updated_at: new Date('2024-03-20'),
    thumbnail: null,
    analysis_result: {
      summary: '本报告分析了2024年主要技术发展趋势，包括人工智能、云计算、物联网等领域的重要进展。',
      key_points: [
        '人工智能在各个行业的应用加速',
        '云计算向边缘计算演进',
        '物联网设备数量持续增长'
      ],
      topics: ['人工智能', '云计算', '物联网', '大数据'],
      extracted_text: '2024年技术趋势报告\n\n第一章：人工智能发展...',
      tables: [
        {
          headers: ['技术', '增长率', '市场份额'],
          rows: [
            { id: 1, cells: ['AI', '35%', '45%'] },
            { id: 2, cells: ['云计算', '28%', '32%'] }
          ]
        }
      ],
      images: [],
      sentiment: { label: 'positive', score: 0.8 },
      entities: [
        { text: '人工智能', type: 'TECHNOLOGY', confidence: 95 },
        { text: '云计算', type: 'TECHNOLOGY', confidence: 92 }
      ],
      keywords: [
        { word: '人工智能', size: 24 },
        { word: '云计算', size: 20 },
        { word: '物联网', size: 18 }
      ],
      metadata: {
        title: '2024年技术趋势报告',
        author: '技术研究院',
        created_date: '2024-01-15',
        page_count: 45,
        word_count: 12500
      },
      outline: [
        { id: 1, level: 1, title: '引言', page: 1 },
        { id: 2, level: 1, title: '人工智能发展', page: 5 }
      ]
    }
  },
  {
    id: 'doc_002',
    name: '产品设计规范.docx',
    type: 'doc',
    size: 2097152,
    analysis_status: 'analyzing',
    analysis_progress: 65,
    tags: ['设计', '规范'],
    updated_at: new Date('2024-03-19'),
    thumbnail: null
  },
  {
    id: 'doc_003',
    name: '市场分析数据.xlsx',
    type: 'excel',
    size: 1048576,
    analysis_status: 'pending',
    analysis_progress: 0,
    tags: ['市场', '分析'],
    updated_at: new Date('2024-03-18'),
    thumbnail: null
  }
]

// 计算属性
const filteredDocuments = computed(() => {
  let filtered = documents.value

  // 状态筛选
  if (statusFilter.value) {
    filtered = filtered.filter(doc => doc.analysis_status === statusFilter.value)
  }

  // 类型筛选
  if (typeFilter.value) {
    filtered = filtered.filter(doc => doc.type === typeFilter.value)
  }

  return filtered
})

const sortedDocuments = computed(() => {
  const sorted = [...filteredDocuments.value]
  sorted.sort((a, b) => {
    switch (sortBy.value) {
      case 'name':
        return a.name.localeCompare(b.name)
      case 'size':
        return b.size - a.size
      case 'status':
        return a.analysis_status.localeCompare(b.analysis_status)
      default:
        return b.updated_at - a.updated_at
    }
  })
  return sorted
})

const selectAll = computed({
  get: () => selectedDocuments.value.length === filteredDocuments.value.length,
  set: (value) => {
    if (value) {
      selectedDocuments.value = filteredDocuments.value.map(doc => doc.id)
    } else {
      selectedDocuments.value = []
    }
  }
})

const completedAnalysis = computed(() => {
  return documents.value.filter(doc => doc.analysis_status === 'completed').length
})

const analyzingCount = computed(() => {
  return documents.value.filter(doc => doc.analysis_status === 'analyzing').length
})

// 方法
const loadDocuments = async () => {
  loading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 500))
    documents.value = mockDocuments
  } catch (error) {
    console.error('加载文档失败:', error)
  } finally {
    loading.value = false
  }
}

const refreshDocuments = () => {
  loadDocuments()
}

const toggleSelectAll = () => {
  // 由 v-model 的 computed 处理
}

const getFileIcon = (type) => {
  return `file-icon-${type}`
}

const getFileEmoji = (type) => {
  const icons = {
    pdf: '📄',
    doc: '📝',
    txt: '📃',
    ppt: '📊',
    excel: '📈',
    image: '🖼️'
  }
  return icons[type] || '📄'
}

const getStatusText = (status) => {
  const statusMap = {
    pending: '待分析',
    analyzing: '分析中',
    completed: '已完成',
    failed: '失败'
  }
  return statusMap[status] || status
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (date) => {
  return date.toLocaleDateString('zh-CN')
}

const viewDocument = (doc) => {
  if (doc.analysis_result) {
    analysisResult.value = doc.analysis_result
    analysisResult.value.document_name = doc.name
    showAnalysisModal.value = true
  }
}

const analyzeDocument = async (doc) => {
  try {
    doc.analysis_status = 'analyzing'
    doc.analysis_progress = 0

    // 模拟分析进度
    const progressInterval = setInterval(() => {
      if (doc.analysis_progress < 90) {
        doc.analysis_progress += 10
      }
    }, 500)

    // 模拟分析完成
    setTimeout(() => {
      clearInterval(progressInterval)
      doc.analysis_status = 'completed'
      doc.analysis_progress = 100
      doc.analysis_result = mockDocuments[0].analysis_result
    }, 5000)
  } catch (error) {
    console.error('分析文档失败:', error)
    doc.analysis_status = 'failed'
  }
}

const batchAnalysis = async () => {
  const docsToAnalyze = documents.value.filter(doc =>
    selectedDocuments.value.includes(doc.id) &&
    doc.analysis_status !== 'completed'
  )

  for (const doc of docsToAnalyze) {
    await analyzeDocument(doc)
  }
}

const downloadDocument = (doc) => {
  console.log('下载文档:', doc)
}

const shareDocument = (doc) => {
  console.log('分享文档:', doc)
}

const deleteDocument = (doc) => {
  if (confirm(`确定要删除文档 "${doc.name}" 吗？`)) {
    const index = documents.value.findIndex(item => item.id === doc.id)
    if (index > -1) {
      documents.value.splice(index, 1)
    }
  }
}

// 拖拽上传相关方法
const handleDrop = (event) => {
  isDragOver.value = false
  const files = Array.from(event.dataTransfer.files)
  uploadedFiles.value.push(...files)
}

const handleFileSelect = (event) => {
  const files = Array.from(event.target.files)
  uploadedFiles.value.push(...files)
}

// 上传模态框相关方法
const closeUploadModal = () => {
  showUploadModal.value = false
  uploadedFiles.value = []
}

const removeUploadedFile = (index) => {
  uploadedFiles.value.splice(index, 1)
}

const confirmUpload = async () => {
  try {
    for (const file of uploadedFiles.value) {
      const newDoc = {
        id: `doc_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        name: file.name,
        type: file.name.split('.').pop().toLowerCase(),
        size: file.size,
        analysis_status: 'pending',
        analysis_progress: 0,
        tags: [],
        updated_at: new Date(),
        thumbnail: null
      }
      documents.value.unshift(newDoc)
    }

    closeUploadModal()
  } catch (error) {
    console.error('上传文档失败:', error)
  }
}

const uploadFromUrl = () => {
  console.log('从URL上传')
  closeUploadModal()
}

const uploadFromApi = () => {
  console.log('从API上传')
  closeUploadModal()
}

// 分析结果模态框相关方法
const closeAnalysisModal = () => {
  showAnalysisModal.value = false
  analysisResult.value = null
  activeTab.value = 'summary'
}

// 生命周期
onMounted(() => {
  loadDocuments()
})
</script>

<style scoped>
.document-analysis {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  background: white;
  border-bottom: 1px solid #e1e8ed;
}

.analysis-header h2 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.5rem;
}

.header-actions {
  display: flex;
  gap: 1rem;
}

.analysis-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.analysis-sidebar {
  width: 320px;
  background: white;
  border-right: 1px solid #e1e8ed;
  padding: 1.5rem;
  overflow-y: auto;
}

.upload-section {
  margin-bottom: 2rem;
}

.upload-area {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.upload-area:hover,
.upload-area.drag-over {
  border-color: #667eea;
  background: #f8f9ff;
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.upload-content h3 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.upload-content p {
  margin: 0 0 1rem 0;
  color: #5a6c7d;
}

.filter-section h3 {
  margin: 0 0 1rem 0;
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

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.stats-section h3 {
  margin: 0 0 1rem 0;
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

.analysis-main {
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

.document-list {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: #f8f9fa;
  border-bottom: 1px solid #e1e8ed;
}

.list-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.select-all {
  margin-right: 0.5rem;
}

.sort-select {
  padding: 0.25rem 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.8rem;
}

.document-item {
  display: flex;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e1e8ed;
  transition: background-color 0.3s ease;
}

.document-item:hover {
  background: #f8f9fa;
}

.document-item.selected {
  background: #e3f2fd;
}

.document-checkbox {
  margin-right: 1rem;
}

.document-preview {
  width: 60px;
  height: 60px;
  margin-right: 1rem;
  border-radius: 6px;
  background: #f8f9fa;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  overflow: hidden;
}

.preview-icon {
  font-size: 1.5rem;
}

.preview-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.document-info {
  flex: 1;
  cursor: pointer;
}

.document-name {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
  font-size: 1rem;
}

.document-meta {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.5rem;
  font-size: 0.8rem;
  color: #5a6c7d;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.meta-icon {
  font-size: 0.7rem;
}

.document-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.tag {
  padding: 0.125rem 0.5rem;
  background: #e3f2fd;
  color: #1976d2;
  border-radius: 12px;
  font-size: 0.7rem;
}

.tag-more {
  padding: 0.125rem 0.5rem;
  background: #f5f5f5;
  color: #666;
  border-radius: 12px;
  font-size: 0.7rem;
}

.document-status {
  margin-right: 1rem;
  min-width: 100px;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
  text-align: center;
}

.status-badge.pending {
  background: #f8f9fa;
  color: #6c757d;
}

.status-badge.analyzing {
  background: #fff3cd;
  color: #856404;
}

.status-badge.completed {
  background: #d4edda;
  color: #155724;
}

.status-badge.failed {
  background: #f8d7da;
  color: #721c24;
}

.progress-bar {
  width: 100%;
  height: 4px;
  background: #e9ecef;
  border-radius: 2px;
  margin-top: 0.5rem;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #667eea;
  transition: width 0.3s ease;
}

.document-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.3s ease;
  background: #f8f9fa;
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
  max-width: 1000px;
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

/* 上传选项样式 */
.upload-options {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
}

.upload-option {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border: 1px solid #e1e8ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.upload-option:hover {
  background: #e3f2fd;
  border-color: #667eea;
}

.upload-icon {
  font-size: 2rem;
}

.upload-content h4 {
  margin: 0 0 0.25rem 0;
  color: #2c3e50;
}

.upload-content p {
  margin: 0;
  color: #5a6c7d;
  font-size: 0.9rem;
}

.uploaded-files h4 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.file-name {
  font-weight: 600;
  color: #2c3e50;
}

.file-size {
  font-size: 0.8rem;
  color: #5a6c7d;
}

.remove-btn {
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  font-size: 0.8rem;
}

/* 分析结果样式 */
.analysis-result {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.result-tabs {
  display: flex;
  border-bottom: 1px solid #e1e8ed;
}

.tab-btn {
  padding: 1rem 1.5rem;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  font-size: 0.9rem;
  color: #5a6c7d;
  transition: all 0.3s ease;
}

.tab-btn.active {
  color: #667eea;
  border-bottom-color: #667eea;
}

.tab-content {
  padding: 1rem 0;
}

.summary-section,
.key-points-section,
.topics-section,
.extraction-section,
.tables-section,
.images-section,
.sentiment-section,
.entities-section,
.keywords-section,
.metadata-section,
.outline-section {
  margin-bottom: 2rem;
}

.summary-section h4,
.key-points-section h4,
.topics-section h4,
.extraction-section h4,
.tables-section h4,
.images-section h4,
.sentiment-section h4,
.entities-section h4,
.keywords-section h4,
.metadata-section h4,
.outline-section h4 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.summary-content {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 6px;
  line-height: 1.6;
}

.key-points-list {
  margin: 0;
  padding-left: 1.5rem;
}

.key-points-list li {
  margin-bottom: 0.5rem;
  line-height: 1.5;
}

.topics-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.topic-tag {
  padding: 0.25rem 0.75rem;
  background: #e3f2fd;
  color: #1976d2;
  border-radius: 16px;
  font-size: 0.8rem;
}

.text-content {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 6px;
  max-height: 300px;
  overflow-y: auto;
}

.text-content pre {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.5;
  font-family: 'Consolas', 'Monaco', monospace;
}

.tables-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.table-item {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 6px;
}

.table-item h5 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.extracted-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.extracted-table th,
.extracted-table td {
  padding: 0.5rem;
  text-align: left;
  border: 1px solid #e1e8ed;
}

.extracted-table th {
  background: #e9ecef;
  font-weight: 600;
}

.images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.image-item {
  text-align: center;
}

.image-item img {
  width: 100%;
  max-height: 200px;
  object-fit: cover;
  border-radius: 6px;
}

.image-description {
  margin-top: 0.5rem;
  font-size: 0.8rem;
  color: #5a6c7d;
}

.sentiment-result {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.sentiment-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.score-circle {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: bold;
  color: white;
}

.score-circle.positive {
  background: #28a745;
}

.score-circle.negative {
  background: #dc3545;
}

.score-circle.neutral {
  background: #6c757d;
}

.sentiment-label {
  font-weight: 600;
  color: #2c3e50;
}

.entities-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.entity-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
}

.entity-text {
  font-weight: 600;
  color: #2c3e50;
}

.entity-type {
  padding: 0.25rem 0.5rem;
  background: #e3f2fd;
  color: #1976d2;
  border-radius: 4px;
  font-size: 0.8rem;
}

.entity-confidence {
  font-size: 0.8rem;
  color: #5a6c7d;
}

.keywords-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: #f8f9fa;
  border-radius: 6px;
}

.keyword {
  color: #667eea;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.keyword:hover {
  color: #5a6fd8;
  transform: scale(1.1);
}

.metadata-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.metadata-item {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
}

.metadata-label {
  font-weight: 600;
  color: #5a6c7d;
}

.metadata-value {
  color: #2c3e50;
}

.outline-tree {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 6px;
}

.outline-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0;
  font-family: 'Consolas', 'Monaco', monospace;
}

.outline-title {
  color: #2c3e50;
}

.outline-page {
  color: #5a6c7d;
  font-size: 0.8rem;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .analysis-content {
    flex-direction: column;
  }

  .analysis-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #e1e8ed;
  }
}

@media (max-width: 768px) {
  .analysis-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .header-actions {
    justify-content: center;
  }

  .analysis-main {
    padding: 1rem;
  }

  .document-item {
    flex-wrap: wrap;
    padding: 1rem;
  }

  .document-preview {
    width: 50px;
    height: 50px;
  }

  .document-info {
    flex: 1;
    min-width: 200px;
  }

  .document-status {
    margin-right: 0.5rem;
  }

  .modal-content {
    width: 95%;
    margin: 1rem;
  }
}

@media (max-width: 480px) {
  .analysis-sidebar {
    padding: 1rem;
  }

  .analysis-main {
    padding: 0.5rem;
  }

  .list-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .document-meta {
    flex-direction: column;
    gap: 0.25rem;
  }

  .document-actions {
    width: 100%;
    justify-content: center;
    margin-top: 0.5rem;
  }

  .result-tabs {
    overflow-x: auto;
  }

  .keywords-cloud {
    padding: 1rem;
  }
}
</style>