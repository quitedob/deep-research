<template>
  <div class="content-moderation">
    <div class="moderation-header">
      <h2>内容审核</h2>
      <div class="header-actions">
        <button @click="showBatchModerationModal = true" class="btn btn-primary">
          🔍 批量审核
        </button>
        <button @click="refreshData" class="btn btn-outline" :disabled="loading">
          🔄 刷新
        </button>
      </div>
    </div>

    <div class="moderation-content">
      <div class="moderation-sidebar">
        <div class="upload-section">
          <h3>内容审核</h3>
          <div class="upload-tabs">
            <button
              class="tab-btn"
              :class="{ active: activeTab === 'text' }"
              @click="activeTab = 'text'"
            >
              文本审核
            </button>
            <button
              class="tab-btn"
              :class="{ active: activeTab === 'image' }"
              @click="activeTab = 'image'"
            >
              图片审核
            </button>
          </div>

          <!-- 文本审核 -->
          <div v-if="activeTab === 'text'" class="text-moderation">
            <div class="text-input-section">
              <textarea
                v-model="textInput"
                placeholder="输入需要审核的文本内容..."
                class="text-input"
                rows="8"
              ></textarea>
              <div class="input-actions">
                <button @click="clearText" class="btn btn-sm btn-outline">
                  清空
                </button>
                <button @click="moderateText" class="btn btn-primary" :disabled="!textInput.trim()">
                  开始审核
                </button>
              </div>
            </div>
          </div>

          <!-- 图片审核 -->
          <div v-if="activeTab === 'image'" class="image-moderation">
            <div class="image-upload-area" :class="{ 'drag-over': isDragOver }" @dragover.prevent @dragleave.prevent @drop.prevent="handleImageDrop">
              <input
                type="file"
                ref="imageInput"
                accept="image/*"
                @change="handleImageSelect"
                style="display: none"
              />
              <div v-if="!selectedImage" class="upload-placeholder">
                <div class="upload-icon">🖼️</div>
                <h4>拖拽图片到此处</h4>
                <p>或点击选择图片</p>
                <button @click="$refs.imageInput.click()" class="btn btn-outline">
                  选择图片
                </button>
              </div>
              <div v-else class="image-preview">
                <img :src="imagePreviewUrl" :alt="selectedImage.name" />
                <div class="image-info">
                  <span class="image-name">{{ selectedImage.name }}</span>
                  <span class="image-size">{{ formatFileSize(selectedImage.size) }}</span>
                </div>
                <div class="image-actions">
                  <button @click="clearImage" class="btn btn-sm btn-outline">
                    重新选择
                  </button>
                  <button @click="moderateImage" class="btn btn-primary">
                    开始审核
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="rules-section">
          <h3>审核规则</h3>
          <div class="rules-list">
            <div v-for="rule in moderationRules" :key="rule.id" class="rule-item">
              <div class="rule-header">
                <span class="rule-name">{{ rule.name }}</span>
                <div class="rule-toggle">
                  <input
                    type="checkbox"
                    :id="`rule-${rule.id}`"
                    v-model="rule.enabled"
                  />
                  <label :for="`rule-${rule.id}`"></label>
                </div>
              </div>
              <div class="rule-description">{{ rule.description }}</div>
              <div class="rule-severity">
                <span class="severity-label">严重程度:</span>
                <span class="severity-badge" :class="rule.severity">
                  {{ getSeverityText(rule.severity) }}
                </span>
              </div>
            </div>
          </div>
          <button @click="showManageRulesModal = true" class="btn btn-outline">
            管理规则
          </button>
        </div>

        <div class="stats-section">
          <h3>审核统计</h3>
          <div class="stats-grid">
            <div class="stat-item">
              <span class="stat-value">{{ stats.total }}</span>
              <span class="stat-label">总审核数</span>
            </div>
            <div class="stat-item">
              <span class="stat-value approved">{{ stats.approved }}</span>
              <span class="stat-label">通过</span>
            </div>
            <div class="stat-item">
              <span class="stat-value rejected">{{ stats.rejected }}</span>
              <span class="stat-label">拒绝</span>
            </div>
            <div class="stat-item">
              <span class="stat-value pending">{{ stats.pending }}</span>
              <span class="stat-label">待处理</span>
            </div>
          </div>
        </div>
      </div>

      <div class="moderation-main">
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner">⟳</div>
          <p>审核中...</p>
        </div>

        <div v-else-if="!moderationHistory.length" class="empty-state">
          <div class="empty-icon">🔍</div>
          <h3>暂无审核记录</h3>
          <p>开始审核内容后，记录将显示在这里</p>
        </div>

        <div v-else class="moderation-history">
          <div class="history-header">
            <h3>审核历史</h3>
            <div class="history-filters">
              <select v-model="statusFilter" class="filter-select">
                <option value="">全部状态</option>
                <option value="approved">通过</option>
                <option value="rejected">拒绝</option>
                <option value="pending">待处理</option>
                <option value="review">需要人工审核</option>
              </select>
              <select v-model="typeFilter" class="filter-select">
                <option value="">全部类型</option>
                <option value="text">文本</option>
                <option value="image">图片</option>
              </select>
            </div>
          </div>

          <div class="history-list">
            <div
              v-for="item in filteredHistory"
              :key="item.id"
              class="moderation-item"
              :class="item.status"
            >
              <div class="item-header">
                <div class="item-info">
                  <span class="item-type" :class="item.type">
                    {{ getTypeIcon(item.type) }} {{ getTypeText(item.type) }}
                  </span>
                  <span class="item-time">{{ formatTime(item.timestamp) }}</span>
                </div>
                <div class="item-status">
                  <span class="status-badge" :class="item.status">
                    {{ getStatusText(item.status) }}
                  </span>
                  <span v-if="item.confidence" class="confidence-score">
                    {{ Math.round(item.confidence * 100) }}%
                  </span>
                </div>
              </div>

              <div class="item-content">
                <div v-if="item.type === 'text'" class="text-preview">
                  <p>{{ item.content.substring(0, 200) }}{{ item.content.length > 200 ? '...' : '' }}</p>
                </div>
                <div v-if="item.type === 'image'" class="image-preview-small">
                  <img :src="item.thumbnail_url" :alt="item.original_filename" />
                </div>
              </div>

              <div v-if="item.violations && item.violations.length > 0" class="violations-section">
                <h4>违规项:</h4>
                <div class="violations-list">
                  <span
                    v-for="violation in item.violations"
                    :key="violation.type"
                    class="violation-tag"
                    :class="violation.severity"
                  >
                    {{ violation.type }} ({{ violation.severity }})
                  </span>
                </div>
              </div>

              <div class="item-actions">
                <button @click="viewDetails(item)" class="btn btn-sm btn-outline">
                  查看详情
                </button>
                <button v-if="item.status === 'pending'" @click="approveItem(item)" class="btn btn-sm btn-success">
                  通过
                </button>
                <button v-if="item.status === 'pending'" @click="rejectItem(item)" class="btn btn-sm btn-danger">
                  拒绝
                </button>
                <button @click="deleteItem(item)" class="btn btn-sm btn-outline">
                  删除记录
                </button>
              </div>
            </div>
          </div>

          <!-- 分页 -->
          <div class="pagination">
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
    </div>

    <!-- 审核结果模态框 -->
    <div v-if="showResultModal" class="modal-overlay" @click="closeResultModal">
      <div class="modal-content large" @click.stop>
        <div class="modal-header">
          <h3>审核结果</h3>
          <button @click="closeResultModal" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div v-if="currentResult" class="result-details">
            <div class="result-summary">
              <div class="summary-item">
                <span class="summary-label">审核结果:</span>
                <span class="summary-value" :class="currentResult.status">
                  {{ getStatusText(currentResult.status) }}
                </span>
              </div>
              <div class="summary-item">
                <span class="summary-label">置信度:</span>
                <span class="summary-value">
                  {{ Math.round(currentResult.confidence * 100) }}%
                </span>
              </div>
              <div class="summary-item">
                <span class="summary-label">处理时间:</span>
                <span class="summary-value">{{ currentResult.processing_time }}ms</span>
              </div>
            </div>

            <div v-if="currentResult.type === 'text'" class="text-analysis">
              <h4>文本分析结果</h4>
              <div class="content-preview">
                <p>{{ currentResult.content }}</p>
              </div>
            </div>

            <div v-if="currentResult.type === 'image'" class="image-analysis">
              <h4>图片分析结果</h4>
              <div class="image-display">
                <img :src="currentResult.image_url" :alt="currentResult.original_filename" />
              </div>
            </div>

            <div v-if="currentResult.violations && currentResult.violations.length > 0" class="violations-detail">
              <h4>违规详情</h4>
              <div class="violations-list-detailed">
                <div
                  v-for="violation in currentResult.violations"
                  :key="violation.type"
                  class="violation-detail-item"
                >
                  <div class="violation-header">
                    <span class="violation-type">{{ violation.type }}</span>
                    <span class="violation-severity" :class="violation.severity">
                      {{ getSeverityText(violation.severity) }}
                    </span>
                  </div>
                  <div class="violation-description">{{ violation.description }}</div>
                  <div v-if="violation.details" class="violation-additional">
                    <p>{{ violation.details }}</p>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="currentResult.suggestions && currentResult.suggestions.length > 0" class="suggestions-section">
              <h4>建议操作</h4>
              <ul class="suggestions-list">
                <li v-for="suggestion in currentResult.suggestions" :key="suggestion">
                  {{ suggestion }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 批量审核模态框 -->
    <div v-if="showBatchModerationModal" class="modal-overlay" @click="closeBatchModerationModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>批量审核</h3>
          <button @click="closeBatchModerationModal" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div class="batch-upload">
            <div class="upload-area-large" :class="{ 'drag-over': isBatchDragOver }" @dragover.prevent @dragleave.prevent @drop.prevent="handleBatchDrop">
              <input
                type="file"
                ref="batchInput"
                multiple
                accept="text/*,image/*"
                @change="handleBatchSelect"
                style="display: none"
              />
              <div class="batch-placeholder">
                <div class="upload-icon">📁</div>
                <h4>拖拽多个文件到此处</h4>
                <p>支持文本文件和图片文件</p>
                <button @click="$refs.batchInput.click()" class="btn btn-primary">
                  选择文件
                </button>
              </div>
            </div>

            <div v-if="batchFiles.length > 0" class="batch-files-list">
              <h4>待审核文件</h4>
              <div class="files-list">
                <div v-for="(file, index) in batchFiles" :key="index" class="batch-file-item">
                  <span class="file-type">{{ getFileTypeIcon(file.type) }}</span>
                  <span class="file-name">{{ file.name }}</span>
                  <span class="file-size">{{ formatFileSize(file.size) }}</span>
                  <button @click="removeBatchFile(index)" class="remove-file">×</button>
                </div>
              </div>
              <div class="batch-actions">
                <button @click="clearBatch" class="btn btn-outline">
                  清空列表
                </button>
                <button @click="startBatchModeration" class="btn btn-primary" :disabled="!batchFiles.length">
                  开始批量审核
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 管理规则模态框 -->
    <div v-if="showManageRulesModal" class="modal-overlay" @click="closeManageRulesModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>管理审核规则</h3>
          <button @click="closeManageRulesModal" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div class="rules-management">
            <div class="rules-header">
              <button @click="showAddRuleModal = true" class="btn btn-primary">
                添加新规则
              </button>
            </div>
            <div class="rules-table">
              <table>
                <thead>
                  <tr>
                    <th>规则名称</th>
                    <th>类型</th>
                    <th>严重程度</th>
                    <th>状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="rule in moderationRules" :key="rule.id">
                    <td>{{ rule.name }}</td>
                    <td>{{ rule.type }}</td>
                    <td>
                      <span class="severity-badge" :class="rule.severity">
                        {{ getSeverityText(rule.severity) }}
                      </span>
                    </td>
                    <td>
                      <span class="status-badge" :class="rule.enabled ? 'enabled' : 'disabled'">
                        {{ rule.enabled ? '启用' : '禁用' }}
                      </span>
                    </td>
                    <td>
                      <div class="rule-actions">
                        <button @click="editRule(rule)" class="btn btn-xs btn-outline">
                          编辑
                        </button>
                        <button @click="deleteRule(rule.id)" class="btn btn-xs btn-danger">
                          删除
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
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
const activeTab = ref('text')
const textInput = ref('')
const selectedImage = ref(null)
const imagePreviewUrl = ref('')
const isDragOver = ref(false)
const isBatchDragOver = ref(false)
const statusFilter = ref('')
const typeFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(10)

// 模态框状态
const showResultModal = ref(false)
const showBatchModerationModal = ref(false)
const showManageRulesModal = ref(false)
const showAddRuleModal = ref(false)

// 当前审核结果
const currentResult = ref(null)

// 批量审核文件
const batchFiles = ref([])

// 审核规则
const moderationRules = ref([
  {
    id: 1,
    name: '敏感词检测',
    type: 'text',
    severity: 'high',
    enabled: true,
    description: '检测文本中的敏感词汇和不当内容'
  },
  {
    id: 2,
    name: '垃圾信息识别',
    type: 'text',
    severity: 'medium',
    enabled: true,
    description: '识别广告、诈骗等垃圾信息'
  },
  {
    id: 3,
    name: '暴力内容检测',
    type: 'image',
    severity: 'high',
    enabled: true,
    description: '检测图片中的暴力、血腥内容'
  },
  {
    id: 4,
    name: '成人内容检测',
    type: 'image',
    severity: 'high',
    enabled: true,
    description: '检测图片中的成人内容'
  },
  {
    id: 5,
    name: '政治敏感内容',
    type: 'text',
    severity: 'high',
    enabled: false,
    description: '检测政治敏感相关内容'
  }
])

// 审核统计数据
const stats = ref({
  total: 1250,
  approved: 980,
  rejected: 180,
  pending: 90
})

// 审核历史数据
const moderationHistory = ref([
  {
    id: 1,
    type: 'text',
    content: '这是一段测试文本，包含正常内容。',
    status: 'approved',
    confidence: 0.95,
    timestamp: new Date(Date.now() - 1000 * 60 * 5),
    processing_time: 120,
    violations: []
  },
  {
    id: 2,
    type: 'image',
    original_filename: 'test_image.jpg',
    thumbnail_url: 'https://via.placeholder.com/100x100',
    status: 'rejected',
    confidence: 0.88,
    timestamp: new Date(Date.now() - 1000 * 60 * 15),
    processing_time: 450,
    violations: [
      {
        type: '成人内容',
        severity: 'high',
        description: '检测到成人相关内容',
        details: '图片中包含不适合公共场合的内容'
      }
    ]
  },
  {
    id: 3,
    type: 'text',
    content: '这个产品非常好，强烈推荐大家购买！限时优惠，快来选购吧！',
    status: 'rejected',
    confidence: 0.92,
    timestamp: new Date(Date.now() - 1000 * 60 * 30),
    processing_time: 95,
    violations: [
      {
        type: '垃圾信息',
        severity: 'medium',
        description: '检测到广告内容',
        details: '文本包含营销推广信息'
      }
    ]
  },
  {
    id: 4,
    type: 'text',
    content: '边界情况内容，需要人工审核判断。',
    status: 'review',
    confidence: 0.65,
    timestamp: new Date(Date.now() - 1000 * 60 * 45),
    processing_time: 180,
    violations: [
      {
        type: '可能违规',
        severity: 'low',
        description: '内容可能存在违规，建议人工审核'
      }
    ]
  }
])

// 计算属性
const filteredHistory = computed(() => {
  let filtered = moderationHistory.value

  if (statusFilter.value) {
    filtered = filtered.filter(item => item.status === statusFilter.value)
  }

  if (typeFilter.value) {
    filtered = filtered.filter(item => item.type === typeFilter.value)
  }

  return filtered
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
const moderateText = async () => {
  if (!textInput.value.trim()) return

  loading.value = true
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 2000))

    const result = {
      id: Date.now(),
      type: 'text',
      content: textInput.value,
      status: Math.random() > 0.3 ? 'approved' : 'rejected',
      confidence: Math.random() * 0.3 + 0.7,
      timestamp: new Date(),
      processing_time: Math.floor(Math.random() * 300) + 50,
      violations: Math.random() > 0.7 ? [
        {
          type: '敏感词',
          severity: 'medium',
          description: '检测到敏感词汇'
        }
      ] : []
    }

    moderationHistory.value.unshift(result)
    currentResult.value = result
    showResultModal.value = true

    // 更新统计
    stats.value.total++
    if (result.status === 'approved') {
      stats.value.approved++
    } else if (result.status === 'rejected') {
      stats.value.rejected++
    }

    textInput.value = ''
  } catch (error) {
    console.error('文本审核失败:', error)
  } finally {
    loading.value = false
  }
}

const moderateImage = async () => {
  if (!selectedImage.value) return

  loading.value = true
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 3000))

    const result = {
      id: Date.now(),
      type: 'image',
      original_filename: selectedImage.value.name,
      thumbnail_url: imagePreviewUrl.value,
      image_url: imagePreviewUrl.value,
      status: Math.random() > 0.4 ? 'approved' : 'rejected',
      confidence: Math.random() * 0.25 + 0.75,
      timestamp: new Date(),
      processing_time: Math.floor(Math.random() * 500) + 100,
      violations: Math.random() > 0.6 ? [
        {
          type: '不当内容',
          severity: 'high',
          description: '检测到不当内容'
        }
      ] : []
    }

    moderationHistory.value.unshift(result)
    currentResult.value = result
    showResultModal.value = true

    // 更新统计
    stats.value.total++
    if (result.status === 'approved') {
      stats.value.approved++
    } else if (result.status === 'rejected') {
      stats.value.rejected++
    }

    clearImage()
  } catch (error) {
    console.error('图片审核失败:', error)
  } finally {
    loading.value = false
  }
}

const clearText = () => {
  textInput.value = ''
}

const clearImage = () => {
  selectedImage.value = null
  imagePreviewUrl.value = ''
}

const handleImageSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    selectedImage.value = file
    imagePreviewUrl.value = URL.createObjectURL(file)
  }
}

const handleImageDrop = (event) => {
  isDragOver.value = false
  const file = event.dataTransfer.files[0]
  if (file && file.type.startsWith('image/')) {
    selectedImage.value = file
    imagePreviewUrl.value = URL.createObjectURL(file)
  }
}

const handleBatchSelect = (event) => {
  const files = Array.from(event.target.files)
  batchFiles.value.push(...files.map(file => ({
    ...file,
    type: file.type.startsWith('image/') ? 'image' : 'text'
  })))
}

const handleBatchDrop = (event) => {
  isBatchDragOver.value = false
  const files = Array.from(event.dataTransfer.files)
  batchFiles.value.push(...files.map(file => ({
    ...file,
    type: file.type.startsWith('image/') ? 'image' : 'text'
  })))
}

const removeBatchFile = (index) => {
  batchFiles.value.splice(index, 1)
}

const clearBatch = () => {
  batchFiles.value = []
}

const startBatchModeration = async () => {
  loading.value = true
  try {
    // 模拟批量审核
    for (const file of batchFiles.value) {
      await new Promise(resolve => setTimeout(resolve, 1000))

      const result = {
        id: Date.now() + Math.random(),
        type: file.type,
        content: file.type === 'text' ? '批量审核文本内容' : '',
        original_filename: file.name,
        thumbnail_url: file.type === 'image' ? URL.createObjectURL(file) : null,
        status: Math.random() > 0.3 ? 'approved' : 'rejected',
        confidence: Math.random() * 0.3 + 0.7,
        timestamp: new Date(),
        processing_time: Math.floor(Math.random() * 400) + 100,
        violations: Math.random() > 0.7 ? [
          {
            type: '违规内容',
            severity: 'medium',
            description: '检测到违规内容'
          }
        ] : []
      }

      moderationHistory.value.unshift(result)
      stats.value.total++
      if (result.status === 'approved') {
        stats.value.approved++
      } else if (result.status === 'rejected') {
        stats.value.rejected++
      }
    }

    clearBatch()
    closeBatchModerationModal()
  } catch (error) {
    console.error('批量审核失败:', error)
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  // 刷新数据
  console.log('刷新审核数据')
}

const viewDetails = (item) => {
  currentResult.value = item
  showResultModal.value = true
}

const approveItem = (item) => {
  item.status = 'approved'
  stats.value.approved++
  stats.value.pending--
}

const rejectItem = (item) => {
  item.status = 'rejected'
  stats.value.rejected++
  stats.value.pending--
}

const deleteItem = (item) => {
  const index = moderationHistory.value.findIndex(h => h.id === item.id)
  if (index > -1) {
    moderationHistory.value.splice(index, 1)
    stats.value.total--
    if (item.status === 'approved') {
      stats.value.approved--
    } else if (item.status === 'rejected') {
      stats.value.rejected--
    } else if (item.status === 'pending') {
      stats.value.pending--
    }
  }
}

const editRule = (rule) => {
  console.log('编辑规则:', rule)
}

const deleteRule = (ruleId) => {
  if (confirm('确定要删除这条规则吗？')) {
    const index = moderationRules.value.findIndex(r => r.id === ruleId)
    if (index > -1) {
      moderationRules.value.splice(index, 1)
    }
  }
}

// 分页方法
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

// 模态框控制方法
const closeResultModal = () => {
  showResultModal.value = false
  currentResult.value = null
}

const closeBatchModerationModal = () => {
  showBatchModerationModal.value = false
}

const closeManageRulesModal = () => {
  showManageRulesModal.value = false
}

// 工具方法
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatTime = (date) => {
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  return date.toLocaleDateString('zh-CN')
}

const getTypeIcon = (type) => {
  return type === 'text' ? '📝' : '🖼️'
}

const getTypeText = (type) => {
  return type === 'text' ? '文本' : '图片'
}

const getFileTypeIcon = (type) => {
  return type === 'text' ? '📄' : '🖼️'
}

const getStatusText = (status) => {
  const statusMap = {
    approved: '通过',
    rejected: '拒绝',
    pending: '待处理',
    review: '需要人工审核'
  }
  return statusMap[status] || status
}

const getSeverityText = (severity) => {
  const severityMap = {
    low: '低',
    medium: '中',
    high: '高'
  }
  return severityMap[severity] || severity
}

// 生命周期
onMounted(() => {
  // 初始化数据
})
</script>

<style scoped>
.content-moderation {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}

.moderation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  background: white;
  border-bottom: 1px solid #e1e8ed;
}

.moderation-header h2 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.5rem;
}

.header-actions {
  display: flex;
  gap: 1rem;
}

.moderation-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.moderation-sidebar {
  width: 380px;
  background: white;
  border-right: 1px solid #e1e8ed;
  padding: 1.5rem;
  overflow-y: auto;
}

.upload-section h3,
.rules-section h3,
.stats-section h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  font-size: 1.1rem;
}

.upload-tabs {
  display: flex;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid #e1e8ed;
}

.tab-btn {
  flex: 1;
  padding: 0.75rem;
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

.text-input-section {
  margin-bottom: 1.5rem;
}

.text-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.9rem;
  resize: vertical;
  margin-bottom: 1rem;
}

.text-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

.input-actions {
  display: flex;
  justify-content: space-between;
}

.image-upload-area {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 1.5rem;
}

.image-upload-area:hover,
.image-upload-area.drag-over {
  border-color: #667eea;
  background: #f8f9ff;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.upload-placeholder h4 {
  margin: 0;
  color: #2c3e50;
}

.upload-placeholder p {
  margin: 0;
  color: #5a6c7d;
  font-size: 0.9rem;
}

.image-preview {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.image-preview img {
  max-width: 100%;
  max-height: 200px;
  border-radius: 6px;
}

.image-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  color: #5a6c7d;
}

.image-actions {
  display: flex;
  gap: 0.5rem;
}

.rules-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.rule-item {
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #e9ecef;
}

.rule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.rule-name {
  font-weight: 600;
  color: #2c3e50;
}

.rule-toggle input[type="checkbox"] {
  display: none;
}

.rule-toggle label {
  display: block;
  width: 48px;
  height: 24px;
  background: #ccc;
  border-radius: 12px;
  position: relative;
  cursor: pointer;
  transition: background 0.3s ease;
}

.rule-toggle label::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  transition: transform 0.3s ease;
}

.rule-toggle input[type="checkbox"]:checked + label {
  background: #667eea;
}

.rule-toggle input[type="checkbox"]:checked + label::after {
  transform: translateX(24px);
}

.rule-description {
  font-size: 0.9rem;
  color: #5a6c7d;
  margin-bottom: 0.5rem;
}

.rule-severity {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.severity-label {
  font-size: 0.8rem;
  color: #5a6c7d;
}

.severity-badge {
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 600;
}

.severity-badge.low {
  background: #d4edda;
  color: #155724;
}

.severity-badge.medium {
  background: #fff3cd;
  color: #856404;
}

.severity-badge.high {
  background: #f8d7da;
  color: #721c24;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.stat-item {
  text-align: center;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 6px;
}

.stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: bold;
  color: #2c3e50;
  margin-bottom: 0.25rem;
}

.stat-value.approved {
  color: #28a745;
}

.stat-value.rejected {
  color: #dc3545;
}

.stat-value.pending {
  color: #ffc107;
}

.stat-label {
  font-size: 0.8rem;
  color: #5a6c7d;
}

.moderation-main {
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
  margin: 0;
  color: #5a6c7d;
}

.moderation-history {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  background: #f8f9fa;
  border-bottom: 1px solid #e1e8ed;
}

.history-header h3 {
  margin: 0;
  color: #2c3e50;
}

.history-filters {
  display: flex;
  gap: 1rem;
}

.filter-select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.history-list {
  display: flex;
  flex-direction: column;
}

.moderation-item {
  padding: 1.5rem;
  border-bottom: 1px solid #e1e8ed;
  transition: background-color 0.3s ease;
}

.moderation-item:hover {
  background: #f8f9fa;
}

.moderation-item:last-child {
  border-bottom: none;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.item-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.item-type {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}

.item-type.text {
  background: #e3f2fd;
  color: #1976d2;
}

.item-type.image {
  background: #f3e5f5;
  color: #7b1fa2;
}

.item-time {
  font-size: 0.8rem;
  color: #5a6c7d;
}

.item-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}

.status-badge.approved {
  background: #d4edda;
  color: #155724;
}

.status-badge.rejected {
  background: #f8d7da;
  color: #721c24;
}

.status-badge.pending {
  background: #fff3cd;
  color: #856404;
}

.status-badge.review {
  background: #e2e3e5;
  color: #383d41;
}

.confidence-score {
  font-size: 0.8rem;
  color: #5a6c7d;
}

.item-content {
  margin-bottom: 1rem;
}

.text-preview p {
  margin: 0;
  color: #2c3e50;
  line-height: 1.5;
}

.image-preview-small img {
  max-width: 100px;
  max-height: 100px;
  border-radius: 4px;
}

.violations-section {
  margin-bottom: 1rem;
}

.violations-section h4 {
  margin: 0 0 0.5rem 0;
  font-size: 0.9rem;
  color: #2c3e50;
}

.violations-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.violation-tag {
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 600;
}

.violation-tag.low {
  background: #d4edda;
  color: #155724;
}

.violation-tag.medium {
  background: #fff3cd;
  color: #856404;
}

.violation-tag.high {
  background: #f8d7da;
  color: #721c24;
}

.item-actions {
  display: flex;
  gap: 0.5rem;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  background: #f8f9fa;
  border-top: 1px solid #e1e8ed;
}

.page-info {
  color: #5a6c7d;
  font-size: 0.9rem;
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
  font-size: 0.8rem;
}

.btn-xs {
  padding: 0.125rem 0.5rem;
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

.btn-success {
  background: #28a745;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #218838;
}

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #c82333;
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

.result-details {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.result-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.summary-label {
  font-size: 0.9rem;
  color: #5a6c7d;
}

.summary-value {
  font-weight: 600;
  color: #2c3e50;
}

.summary-value.approved {
  color: #28a745;
}

.summary-value.rejected {
  color: #dc3545;
}

.summary-value.review {
  color: #ffc107;
}

.text-analysis h4,
.image-analysis h4,
.violations-detail h4,
.suggestions-section h4 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.content-preview {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 6px;
  line-height: 1.5;
}

.image-display {
  text-align: center;
}

.image-display img {
  max-width: 100%;
  max-height: 400px;
  border-radius: 6px;
}

.violations-list-detailed {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.violation-detail-item {
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #e9ecef;
}

.violation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.violation-type {
  font-weight: 600;
  color: #2c3e50;
}

.violation-description {
  color: #5a6c7d;
  margin-bottom: 0.5rem;
}

.violation-additional {
  font-size: 0.9rem;
  color: #5a6c7d;
}

.suggestions-list {
  margin: 0;
  padding-left: 1.5rem;
}

.suggestions-list li {
  margin-bottom: 0.5rem;
  color: #2c3e50;
}

.batch-upload {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.upload-area-large {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 3rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.upload-area-large:hover,
.upload-area-large.drag-over {
  border-color: #667eea;
  background: #f8f9ff;
}

.batch-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.batch-files-list h4 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.files-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.batch-file-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
}

.file-type {
  font-size: 1.2rem;
}

.file-name {
  flex: 1;
  font-weight: 600;
  color: #2c3e50;
}

.file-size {
  font-size: 0.8rem;
  color: #5a6c7d;
}

.remove-file {
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  font-size: 0.8rem;
}

.batch-actions {
  display: flex;
  justify-content: space-between;
}

.rules-management {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.rules-header {
  display: flex;
  justify-content: flex-end;
}

.rules-table {
  overflow-x: auto;
}

.rules-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.rules-table th,
.rules-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e1e8ed;
}

.rules-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #2c3e50;
}

.rule-actions {
  display: flex;
  gap: 0.5rem;
}

.status-badge.enabled {
  background: #d4edda;
  color: #155724;
}

.status-badge.disabled {
  background: #f8d7da;
  color: #721c24;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .moderation-content {
    flex-direction: column;
  }

  .moderation-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #e1e8ed;
  }
}

@media (max-width: 768px) {
  .moderation-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .header-actions {
    justify-content: center;
  }

  .moderation-main {
    padding: 1rem;
  }

  .history-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .history-filters {
    flex-direction: column;
  }

  .item-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .item-info {
    justify-content: space-between;
  }

  .result-summary {
    grid-template-columns: 1fr;
  }

  .modal-content {
    width: 95%;
    margin: 1rem;
  }
}

@media (max-width: 480px) {
  .moderation-sidebar {
    padding: 1rem;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .input-actions {
    flex-direction: column;
    gap: 0.5rem;
  }

  .item-actions {
    flex-wrap: wrap;
    justify-content: center;
  }

  .batch-actions {
    flex-direction: column;
    gap: 1rem;
  }
}
</style>