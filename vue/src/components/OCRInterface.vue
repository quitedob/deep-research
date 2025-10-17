<template>
  <div class="ocr-interface">
    <div class="ocr-header">
      <h2>OCR文字识别</h2>
      <div class="header-actions">
        <button @click="showBatchModal = true" class="btn btn-primary">
          📁 批量识别
        </button>
        <button @click="refreshData" class="btn btn-outline" :disabled="loading">
          🔄 刷新
        </button>
      </div>
    </div>

    <div class="ocr-content">
      <div class="ocr-sidebar">
        <div class="upload-section">
          <h3>文件上传</h3>
          <div class="upload-tabs">
            <button
              class="tab-btn"
              :class="{ active: activeTab === 'image' }"
              @click="activeTab = 'image'"
            >
              图片识别
            </button>
            <button
              class="tab-btn"
              :class="{ active: activeTab === 'pdf' }"
              @click="activeTab = 'pdf'"
            >
              PDF识别
            </button>
          </div>

          <!-- 图片识别 -->
          <div v-if="activeTab === 'image'" class="image-upload">
            <div class="upload-area" :class="{ 'drag-over': isDragOver }" @dragover.prevent @dragleave.prevent @drop.prevent="handleImageDrop">
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
                <p>支持 JPG、PNG、BMP、GIF 等格式</p>
                <button @click="$refs.imageInput.click()" class="btn btn-primary">
                  选择图片
                </button>
              </div>
              <div v-else class="image-preview">
                <img :src="imagePreviewUrl" :alt="selectedImage.name" />
                <div class="image-info">
                  <span class="image-name">{{ selectedImage.name }}</span>
                  <span class="image-size">{{ formatFileSize(selectedImage.size) }}</span>
                  <span class="image-dimensions">{{ imageDimensions.width }} × {{ imageDimensions.height }}</span>
                </div>
                <div class="image-actions">
                  <button @click="clearImage" class="btn btn-sm btn-outline">
                    重新选择
                  </button>
                  <button @click="recognizeImage" class="btn btn-primary" :disabled="processing">
                    {{ processing ? '识别中...' : '开始识别' }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- PDF识别 -->
          <div v-if="activeTab === 'pdf'" class="pdf-upload">
            <div class="upload-area" :class="{ 'drag-over': isDragOver }" @dragover.prevent @dragleave.prevent @drop.prevent="handlePDFDrop">
              <input
                type="file"
                ref="pdfInput"
                accept=".pdf"
                @change="handlePDFSelect"
                style="display: none"
              />
              <div v-if="!selectedPDF" class="upload-placeholder">
                <div class="upload-icon">📄</div>
                <h4>拖拽PDF到此处</h4>
                <p>支持PDF文档文字识别</p>
                <button @click="$refs.pdfInput.click()" class="btn btn-primary">
                  选择PDF
                </button>
              </div>
              <div v-else class="pdf-preview">
                <div class="pdf-icon">📄</div>
                <div class="pdf-info">
                  <span class="pdf-name">{{ selectedPDF.name }}</span>
                  <span class="pdf-size">{{ formatFileSize(selectedPDF.size) }}</span>
                  <div class="pdf-options">
                    <label class="checkbox-label">
                      <input type="checkbox" v-model="pdfOptions.scanAllPages" />
                      扫描所有页面
                    </label>
                    <label v-if="!pdfOptions.scanAllPages" class="page-range">
                      页面范围:
                      <input
                        type="text"
                        v-model="pdfOptions.pageRange"
                        placeholder="如: 1-5,8,10-12"
                        class="page-input"
                      />
                    </label>
                  </div>
                </div>
                <div class="pdf-actions">
                  <button @click="clearPDF" class="btn btn-sm btn-outline">
                    重新选择
                  </button>
                  <button @click="recognizePDF" class="btn btn-primary" :disabled="processing">
                    {{ processing ? '识别中...' : '开始识别' }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- 识别选项 -->
          <div class="recognition-options">
            <h4>识别选项</h4>
            <div class="options-list">
              <div class="option-group">
                <label>识别语言</label>
                <select v-model="recognitionOptions.language" class="option-select">
                  <option value="auto">自动检测</option>
                  <option value="zh-cn">中文简体</option>
                  <option value="zh-tw">中文繁体</option>
                  <option value="en">英文</option>
                  <option value="ja">日文</option>
                  <option value="ko">韩文</option>
                </select>
              </div>

              <div class="option-group">
                <label>输出格式</label>
                <select v-model="recognitionOptions.outputFormat" class="option-select">
                  <option value="text">纯文本</option>
                  <option value="json">JSON格式</option>
                  <option value="markdown">Markdown</option>
                  <option value="html">HTML格式</option>
                </select>
              </div>

              <div class="option-group">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="recognitionOptions.preserveLayout" />
                  保持原始布局
                </label>
              </div>

              <div class="option-group">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="recognitionOptions.detectTables" />
                  检测表格
                </label>
              </div>

              <div class="option-group">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="recognitionOptions.enhanceImage" />
                  图像增强
                </label>
              </div>
            </div>
          </div>
        </div>

        <div class="stats-section">
          <h3>识别统计</h3>
          <div class="stats-grid">
            <div class="stat-item">
              <span class="stat-value">{{ stats.total }}</span>
              <span class="stat-label">总识别数</span>
            </div>
            <div class="stat-item">
              <span class="stat-value success">{{ stats.success }}</span>
              <span class="stat-label">成功</span>
            </div>
            <div class="stat-item">
              <span class="stat-value failed">{{ stats.failed }}</span>
              <span class="stat-label">失败</span>
            </div>
            <div class="stat-item">
              <span class="stat-value processing">{{ stats.processing }}</span>
              <span class="stat-label">处理中</span>
            </div>
          </div>
        </div>
      </div>

      <div class="ocr-main">
        <div v-if="processing" class="processing-state">
          <div class="processing-spinner">⟳</div>
          <h3>正在识别中...</h3>
          <div class="progress-info">
            <div class="progress-bar">
              <div
                class="progress-fill"
                :style="{ width: `${processingProgress}%` }"
              ></div>
            </div>
            <span class="progress-text">{{ processingProgress }}%</span>
          </div>
          <p class="processing-message">{{ processingMessage }}</p>
        </div>

        <div v-else-if="!recognitionHistory.length" class="empty-state">
          <div class="empty-icon">📷</div>
          <h3>暂无识别记录</h3>
          <p>上传图片或PDF开始文字识别</p>
        </div>

        <div v-else class="recognition-history">
          <div class="history-header">
            <h3>识别历史</h3>
            <div class="history-filters">
              <select v-model="statusFilter" class="filter-select">
                <option value="">全部状态</option>
                <option value="completed">已完成</option>
                <option value="processing">处理中</option>
                <option value="failed">失败</option>
              </select>
              <select v-model="typeFilter" class="filter-select">
                <option value="">全部类型</option>
                <option value="image">图片</option>
                <option value="pdf">PDF</option>
              </select>
            </div>
          </div>

          <div class="history-list">
            <div
              v-for="item in filteredHistory"
              :key="item.id"
              class="recognition-item"
              :class="item.status"
            >
              <div class="item-header">
                <div class="item-info">
                  <span class="item-type" :class="item.type">
                    {{ getTypeIcon(item.type) }} {{ getTypeText(item.type) }}
                  </span>
                  <span class="item-name">{{ item.filename }}</span>
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
                <div v-if="item.type === 'image'" class="image-thumbnail">
                  <img :src="item.thumbnail_url" :alt="item.filename" />
                </div>

                <div v-if="item.text_result" class="text-preview">
                  <p>{{ item.text_result.substring(0, 200) }}{{ item.text_result.length > 200 ? '...' : '' }}</p>
                </div>

                <div v-if="item.error_message" class="error-message">
                  <p>{{ item.error_message }}</p>
                </div>
              </div>

              <div class="item-meta">
                <div class="meta-item">
                  <span class="meta-label">文件大小:</span>
                  <span class="meta-value">{{ formatFileSize(item.file_size) }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-label">处理时间:</span>
                  <span class="meta-value">{{ item.processing_time }}ms</span>
                </div>
                <div v-if="item.page_count" class="meta-item">
                  <span class="meta-label">页面数:</span>
                  <span class="meta-value">{{ item.page_count }}</span>
                </div>
                <div v-if="item.word_count" class="meta-item">
                  <span class="meta-label">字数:</span>
                  <span class="meta-value">{{ item.word_count }}</span>
                </div>
              </div>

              <div class="item-actions">
                <button
                  v-if="item.status === 'completed'"
                  @click="viewResult(item)"
                  class="btn btn-sm btn-primary"
                >
                  查看结果
                </button>
                <button
                  v-if="item.status === 'completed'"
                  @click="downloadResult(item)"
                  class="btn btn-sm btn-outline"
                >
                  下载结果
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

    <!-- 识别结果模态框 -->
    <div v-if="showResultModal" class="modal-overlay" @click="closeResultModal">
      <div class="modal-content large" @click.stop>
        <div class="modal-header">
          <h3>识别结果 - {{ currentResult?.filename }}</h3>
          <button @click="closeResultModal" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div v-if="currentResult" class="result-content">
            <div class="result-summary">
              <div class="summary-item">
                <span class="summary-label">识别状态:</span>
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
                <span class="summary-label">识别字数:</span>
                <span class="summary-value">{{ currentResult.word_count }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">处理时间:</span>
                <span class="summary-value">{{ currentResult.processing_time }}ms</span>
              </div>
            </div>

            <div class="result-actions-modal">
              <select v-model="downloadFormat" class="format-select">
                <option value="txt">TXT格式</option>
                <option value="json">JSON格式</option>
                <option value="markdown">Markdown格式</option>
                <option value="html">HTML格式</option>
              </select>
              <button @click="downloadCurrentResult" class="btn btn-primary">
                📥 下载结果
              </button>
              <button @click="copyToClipboard" class="btn btn-outline">
                📋 复制文本
              </button>
            </div>

            <div class="text-result">
              <h4>识别文本</h4>
              <div class="text-content">
                <pre>{{ currentResult.text_result }}</pre>
              </div>
            </div>

            <div v-if="currentResult.type === 'image'" class="original-image">
              <h4>原始图片</h4>
              <div class="image-display">
                <img :src="currentResult.original_url" :alt="currentResult.filename" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 批量识别模态框 -->
    <div v-if="showBatchModal" class="modal-overlay" @click="closeBatchModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>批量OCR识别</h3>
          <button @click="closeBatchModal" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div class="batch-upload">
            <div class="upload-area-large" :class="{ 'drag-over': isBatchDragOver }" @dragover.prevent @dragleave.prevent @drop.prevent="handleBatchDrop">
              <input
                type="file"
                ref="batchInput"
                multiple
                accept="image/*,.pdf"
                @change="handleBatchSelect"
                style="display: none"
              />
              <div class="batch-placeholder">
                <div class="upload-icon">📁</div>
                <h4>拖拽多个文件到此处</h4>
                <p>支持图片和PDF文件</p>
                <button @click="$refs.batchInput.click()" class="btn btn-primary">
                  选择文件
                </button>
              </div>
            </div>

            <div v-if="batchFiles.length > 0" class="batch-files-list">
              <h4>待识别文件</h4>
              <div class="files-list">
                <div v-for="(file, index) in batchFiles" :key="index" class="batch-file-item">
                  <span class="file-type">{{ getFileTypeIcon(file.type) }}</span>
                  <span class="file-name">{{ file.name }}</span>
                  <span class="file-size">{{ formatFileSize(file.size) }}</span>
                  <button @click="removeBatchFile(index)" class="remove-file">×</button>
                </div>
              </div>
              <div class="batch-options">
                <div class="batch-option-group">
                  <label>识别语言:</label>
                  <select v-model="batchOptions.language" class="option-select">
                    <option value="auto">自动检测</option>
                    <option value="zh-cn">中文简体</option>
                    <option value="en">英文</option>
                  </select>
                </div>
                <div class="batch-option-group">
                  <label>输出格式:</label>
                  <select v-model="batchOptions.outputFormat" class="option-select">
                    <option value="text">纯文本</option>
                    <option value="json">JSON格式</option>
                  </select>
                </div>
              </div>
              <div class="batch-actions">
                <button @click="clearBatch" class="btn btn-outline">
                  清空列表
                </button>
                <button @click="startBatchRecognition" class="btn btn-primary" :disabled="!batchFiles.length">
                  开始批量识别
                </button>
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
const processing = ref(false)
const processingProgress = ref(0)
const processingMessage = ref('')
const activeTab = ref('image')
const selectedImage = ref(null)
const imagePreviewUrl = ref('')
const imageDimensions = ref({ width: 0, height: 0 })
const selectedPDF = ref(null)
const isDragOver = ref(false)
const isBatchDragOver = ref(false)
const statusFilter = ref('')
const typeFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(10)

// 模态框状态
const showResultModal = ref(false)
const showBatchModal = ref(false)
const currentResult = ref(null)
const downloadFormat = ref('txt')

// 识别选项
const recognitionOptions = ref({
  language: 'auto',
  outputFormat: 'text',
  preserveLayout: false,
  detectTables: false,
  enhanceImage: false
})

// PDF选项
const pdfOptions = ref({
  scanAllPages: true,
  pageRange: ''
})

// 批量处理选项
const batchOptions = ref({
  language: 'auto',
  outputFormat: 'text'
})

// 批量文件
const batchFiles = ref([])

// 统计数据
const stats = ref({
  total: 45,
  success: 38,
  failed: 3,
  processing: 4
})

// 识别历史
const recognitionHistory = ref([
  {
    id: 1,
    type: 'image',
    filename: 'document_scan.jpg',
    status: 'completed',
    confidence: 0.92,
    timestamp: new Date(Date.now() - 1000 * 60 * 5),
    processing_time: 1250,
    file_size: 2048576,
    text_result: '这是一个文档扫描件的识别结果示例。系统成功识别了图片中的文字内容。',
    word_count: 28,
    thumbnail_url: 'https://via.placeholder.com/150x100',
    original_url: 'https://via.placeholder.com/400x300'
  },
  {
    id: 2,
    type: 'pdf',
    filename: 'contract.pdf',
    status: 'completed',
    confidence: 0.88,
    timestamp: new Date(Date.now() - 1000 * 60 * 30),
    processing_time: 3200,
    file_size: 5242880,
    page_count: 5,
    text_result: '合同协议\n甲方：XXX公司\n乙方：XXX个人\n\n第一条 合作内容',
    word_count: 156,
    thumbnail_url: null
  },
  {
    id: 3,
    type: 'image',
    filename: 'receipt.jpg',
    status: 'failed',
    confidence: 0,
    timestamp: new Date(Date.now() - 1000 * 60 * 60),
    processing_time: 800,
    file_size: 1024000,
    error_message: '图像质量过低，无法识别文字内容',
    word_count: 0,
    thumbnail_url: 'https://via.placeholder.com/150x100'
  },
  {
    id: 4,
    type: 'pdf',
    filename: 'presentation.pdf',
    status: 'processing',
    confidence: 0,
    timestamp: new Date(Date.now() - 1000 * 60 * 2),
    processing_time: 0,
    file_size: 3145728,
    page_count: 12,
    text_result: '',
    word_count: 0,
    thumbnail_url: null
  }
])

// 计算属性
const filteredHistory = computed(() => {
  let filtered = recognitionHistory.value

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

// 方法
const handleImageSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    selectedImage.value = file
    imagePreviewUrl.value = URL.createObjectURL(file)

    // 获取图片尺寸
    const img = new Image()
    img.onload = () => {
      imageDimensions.value = {
        width: img.width,
        height: img.height
      }
    }
    img.src = imagePreviewUrl.value
  }
}

const handleImageDrop = (event) => {
  isDragOver.value = false
  const file = event.dataTransfer.files[0]
  if (file && file.type.startsWith('image/')) {
    selectedImage.value = file
    imagePreviewUrl.value = URL.createObjectURL(file)

    const img = new Image()
    img.onload = () => {
      imageDimensions.value = {
        width: img.width,
        height: img.height
      }
    }
    img.src = imagePreviewUrl.value
  }
}

const handlePDFSelect = (event) => {
  const file = event.target.files[0]
  if (file && file.type === 'application/pdf') {
    selectedPDF.value = file
  }
}

const handlePDFDrop = (event) => {
  isDragOver.value = false
  const file = event.dataTransfer.files[0]
  if (file && file.type === 'application/pdf') {
    selectedPDF.value = file
  }
}

const clearImage = () => {
  selectedImage.value = null
  imagePreviewUrl.value = ''
  imageDimensions.value = { width: 0, height: 0 }
}

const clearPDF = () => {
  selectedPDF.value = null
}

const recognizeImage = async () => {
  if (!selectedImage.value) return

  processing.value = true
  processingProgress.value = 0
  processingMessage.value = '准备识别...'

  try {
    // 模拟处理进度
    const progressInterval = setInterval(() => {
      if (processingProgress.value < 90) {
        processingProgress.value += 10
        processingMessage.value = `正在分析图像... ${processingProgress.value}%`
      }
    }, 200)

    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 3000))

    clearInterval(progressInterval)
    processingProgress.value = 100
    processingMessage.value = '识别完成！'

    // 创建识别结果
    const result = {
      id: Date.now(),
      type: 'image',
      filename: selectedImage.value.name,
      status: 'completed',
      confidence: Math.random() * 0.2 + 0.8,
      timestamp: new Date(),
      processing_time: Math.floor(Math.random() * 2000) + 500,
      file_size: selectedImage.value.size,
      text_result: '这是图片识别的结果文本。系统成功从图片中提取了文字内容，识别准确度较高。' +
                   '图像处理包括预处理、文字检测、文字识别和后处理等步骤。',
      word_count: Math.floor(Math.random() * 200) + 50,
      thumbnail_url: imagePreviewUrl.value,
      original_url: imagePreviewUrl.value
    }

    recognitionHistory.value.unshift(result)
    stats.value.total++
    stats.value.success++

    setTimeout(() => {
      processing.value = false
      processingProgress.value = 0
      clearImage()
    }, 1000)

  } catch (error) {
    console.error('图片识别失败:', error)
    processing.value = false

    // 添加失败记录
    const failedResult = {
      id: Date.now(),
      type: 'image',
      filename: selectedImage.value.name,
      status: 'failed',
      confidence: 0,
      timestamp: new Date(),
      processing_time: 0,
      file_size: selectedImage.value.size,
      error_message: '识别失败：' + error.message,
      word_count: 0,
      thumbnail_url: imagePreviewUrl.value
    }

    recognitionHistory.value.unshift(failedResult)
    stats.value.total++
    stats.value.failed++
  }
}

const recognizePDF = async () => {
  if (!selectedPDF.value) return

  processing.value = true
  processingProgress.value = 0
  processingMessage.value = '准备识别PDF...'

  try {
    // 模拟处理进度
    const progressInterval = setInterval(() => {
      if (processingProgress.value < 90) {
        processingProgress.value += 5
        processingMessage.value = `正在处理页面... ${processingProgress.value}%`
      }
    }, 300)

    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 5000))

    clearInterval(progressInterval)
    processingProgress.value = 100
    processingMessage.value = 'PDF识别完成！'

    // 创建识别结果
    const pageCount = pdfOptions.value.scanAllPages ?
      Math.floor(Math.random() * 10) + 1 :
      pdfOptions.value.pageRange.split(',').length

    const result = {
      id: Date.now(),
      type: 'pdf',
      filename: selectedPDF.value.name,
      status: 'completed',
      confidence: Math.random() * 0.15 + 0.85,
      timestamp: new Date(),
      processing_time: Math.floor(Math.random() * 4000) + 1000,
      file_size: selectedPDF.value.size,
      page_count: pageCount,
      text_result: 'PDF文档识别结果。\n\n第一章 引言\n这是PDF文档的第一章内容，包含了重要的背景信息。\n\n' +
                   '第二章 主要内容\n本章详细描述了核心概念和技术要点...\n\n' +
                   '第三章 结论\n总结全文的主要观点和发现。',
      word_count: Math.floor(Math.random() * 500) + 100,
      thumbnail_url: null
    }

    recognitionHistory.value.unshift(result)
    stats.value.total++
    stats.value.success++

    setTimeout(() => {
      processing.value = false
      processingProgress.value = 0
      clearPDF()
    }, 1000)

  } catch (error) {
    console.error('PDF识别失败:', error)
    processing.value = false
  }
}

const handleBatchSelect = (event) => {
  const files = Array.from(event.target.files)
  batchFiles.value.push(...files.map(file => ({
    ...file,
    type: file.type.startsWith('image/') ? 'image' : 'pdf'
  })))
}

const handleBatchDrop = (event) => {
  isBatchDragOver.value = false
  const files = Array.from(event.dataTransfer.files)
  batchFiles.value.push(...files.map(file => ({
    ...file,
    type: file.type.startsWith('image/') ? 'image' : 'pdf'
  })))
}

const removeBatchFile = (index) => {
  batchFiles.value.splice(index, 1)
}

const clearBatch = () => {
  batchFiles.value = []
}

const startBatchRecognition = async () => {
  if (!batchFiles.value.length) return

  for (const file of batchFiles.value) {
    // 模拟批量处理
    processing.value = true
    processingMessage.value = `正在处理: ${file.name}`

    await new Promise(resolve => setTimeout(resolve, 2000))

    const result = {
      id: Date.now() + Math.random(),
      type: file.type,
      filename: file.name,
      status: Math.random() > 0.2 ? 'completed' : 'failed',
      confidence: Math.random() * 0.3 + 0.7,
      timestamp: new Date(),
      processing_time: Math.floor(Math.random() * 3000) + 500,
      file_size: file.size,
      text_result: Math.random() > 0.2 ? `批量处理结果：${file.name} 的识别文本内容。` : '',
      word_count: Math.floor(Math.random() * 200) + 50,
      thumbnail_url: file.type === 'image' ? URL.createObjectURL(file) : null
    }

    recognitionHistory.value.unshift(result)
    stats.value.total++
    if (result.status === 'completed') {
      stats.value.success++
    } else {
      stats.value.failed++
    }
  }

  processing.value = false
  clearBatch()
  closeBatchModal()
}

const refreshData = () => {
  console.log('刷新OCR数据')
}

const viewResult = (item) => {
  currentResult.value = item
  showResultModal.value = true
}

const downloadResult = (item) => {
  const content = item.text_result
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${item.filename}_ocr_result.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const deleteItem = (item) => {
  if (confirm('确定要删除这条识别记录吗？')) {
    const index = recognitionHistory.value.findIndex(h => h.id === item.id)
    if (index > -1) {
      recognitionHistory.value.splice(index, 1)
      stats.value.total--
      if (item.status === 'completed') {
        stats.value.success--
      } else if (item.status === 'failed') {
        stats.value.failed--
      }
    }
  }
}

const downloadCurrentResult = () => {
  if (!currentResult.value) return

  let content = currentResult.value.text_result
  let mimeType = 'text/plain'
  let extension = 'txt'

  switch (downloadFormat.value) {
    case 'json':
      content = JSON.stringify({
        filename: currentResult.value.filename,
        confidence: currentResult.value.confidence,
        word_count: currentResult.value.word_count,
        text: currentResult.value.text_result
      }, null, 2)
      mimeType = 'application/json'
      extension = 'json'
      break
    case 'markdown':
      mimeType = 'text/markdown'
      extension = 'md'
      break
    case 'html':
      content = `<html><body><pre>${content}</pre></body></html>`
      mimeType = 'text/html'
      extension = 'html'
      break
  }

  const blob = new Blob([content], { type: `${mimeType};charset=utf-8` })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${currentResult.value.filename}_ocr_result.${extension}`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const copyToClipboard = async () => {
  if (!currentResult.value?.text_result) return

  try {
    await navigator.clipboard.writeText(currentResult.value.text_result)
    console.log('文本已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
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

const closeBatchModal = () => {
  showBatchModal.value = false
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
  return type === 'image' ? '🖼️' : '📄'
}

const getTypeText = (type) => {
  return type === 'image' ? '图片' : 'PDF'
}

const getFileTypeIcon = (type) => {
  return type === 'image' ? '🖼️' : '📄'
}

const getStatusText = (status) => {
  const statusMap = {
    completed: '已完成',
    processing: '处理中',
    failed: '失败'
  }
  return statusMap[status] || status
}

// 生命周期
onMounted(() => {
  // 初始化
})
</script>

<style scoped>
.ocr-interface {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}

.ocr-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  background: white;
  border-bottom: 1px solid #e1e8ed;
}

.ocr-header h2 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.5rem;
}

.header-actions {
  display: flex;
  gap: 1rem;
}

.ocr-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.ocr-sidebar {
  width: 380px;
  background: white;
  border-right: 1px solid #e1e8ed;
  padding: 1.5rem;
  overflow-y: auto;
}

.upload-section h3,
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

.upload-area {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 1.5rem;
}

.upload-area:hover,
.upload-area.drag-over {
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

.image-preview,
.pdf-preview {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.image-preview img {
  max-width: 100%;
  max-height: 200px;
  border-radius: 6px;
}

.pdf-icon {
  font-size: 4rem;
  text-align: center;
  margin-bottom: 1rem;
}

.image-info,
.pdf-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #5a6c7d;
}

.image-name,
.pdf-name {
  font-weight: 600;
  color: #2c3e50;
}

.pdf-options {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.page-range {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.page-input {
  flex: 1;
  padding: 0.25rem 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.8rem;
}

.image-actions,
.pdf-actions {
  display: flex;
  gap: 0.5rem;
}

.recognition-options {
  margin-bottom: 1.5rem;
}

.recognition-options h4 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  font-size: 1rem;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.option-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.option-group label {
  font-size: 0.9rem;
  font-weight: 600;
  color: #2c3e50;
}

.option-select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.9rem;
  color: #2c3e50;
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

.stat-value.success {
  color: #28a745;
}

.stat-value.failed {
  color: #dc3545;
}

.stat-value.processing {
  color: #ffc107;
}

.stat-label {
  font-size: 0.8rem;
  color: #5a6c7d;
}

.ocr-main {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
}

.processing-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  text-align: center;
}

.processing-spinner {
  font-size: 3rem;
  margin-bottom: 1rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.processing-state h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.progress-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
  width: 300px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #667eea;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.9rem;
  color: #5a6c7d;
  min-width: 45px;
}

.processing-message {
  color: #5a6c7d;
  font-size: 0.9rem;
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

.recognition-history {
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

.recognition-item {
  padding: 1.5rem;
  border-bottom: 1px solid #e1e8ed;
  transition: background-color 0.3s ease;
}

.recognition-item:hover {
  background: #f8f9fa;
}

.recognition-item:last-child {
  border-bottom: none;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.item-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.item-type {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}

.item-type.image {
  background: #e3f2fd;
  color: #1976d2;
}

.item-type.pdf {
  background: #f3e5f5;
  color: #7b1fa2;
}

.item-name {
  font-weight: 600;
  color: #2c3e50;
}

.item-time {
  font-size: 0.8rem;
  color: #5a6c7d;
}

.item-status {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.5rem;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}

.status-badge.completed {
  background: #d4edda;
  color: #155724;
}

.status-badge.processing {
  background: #fff3cd;
  color: #856404;
}

.status-badge.failed {
  background: #f8d7da;
  color: #721c24;
}

.confidence-score {
  font-size: 0.8rem;
  color: #5a6c7d;
}

.item-content {
  margin-bottom: 1rem;
}

.image-thumbnail {
  margin-bottom: 1rem;
}

.image-thumbnail img {
  max-width: 150px;
  max-height: 100px;
  border-radius: 4px;
}

.text-preview {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 6px;
  border-left: 4px solid #667eea;
}

.text-preview p {
  margin: 0;
  color: #2c3e50;
  line-height: 1.5;
}

.error-message {
  background: #f8d7da;
  padding: 1rem;
  border-radius: 6px;
  border-left: 4px solid #dc3545;
}

.error-message p {
  margin: 0;
  color: #721c24;
}

.item-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1rem;
  font-size: 0.8rem;
}

.meta-item {
  display: flex;
  gap: 0.25rem;
}

.meta-label {
  color: #5a6c7d;
}

.meta-value {
  color: #2c3e50;
  font-weight: 600;
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
  max-width: 900px;
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

.result-content {
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

.summary-value.completed {
  color: #28a745;
}

.result-actions-modal {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.format-select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.text-result h4,
.original-image h4 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.text-content {
  background: #f8f9fa;
  padding: 1.5rem;
  border-radius: 6px;
  max-height: 400px;
  overflow-y: auto;
}

.text-content pre {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.6;
  font-family: 'Consolas', 'Monaco', monospace;
}

.image-display {
  text-align: center;
}

.image-display img {
  max-width: 100%;
  max-height: 500px;
  border-radius: 6px;
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

.batch-options {
  display: flex;
  gap: 2rem;
  margin-bottom: 1rem;
}

.batch-option-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.batch-option-group label {
  font-size: 0.9rem;
  font-weight: 600;
  color: #2c3e50;
}

.batch-actions {
  display: flex;
  justify-content: space-between;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .ocr-content {
    flex-direction: column;
  }

  .ocr-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #e1e8ed;
  }
}

@media (max-width: 768px) {
  .ocr-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .header-actions {
    justify-content: center;
  }

  .ocr-main {
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

  .item-status {
    align-items: flex-start;
  }

  .item-meta {
    flex-direction: column;
    gap: 0.5rem;
  }

  .result-summary {
    grid-template-columns: 1fr;
  }

  .result-actions-modal {
    flex-direction: column;
    align-items: stretch;
  }

  .batch-options {
    flex-direction: column;
    gap: 1rem;
  }

  .batch-actions {
    flex-direction: column;
    gap: 1rem;
  }

  .modal-content {
    width: 95%;
    margin: 1rem;
  }
}

@media (max-width: 480px) {
  .ocr-sidebar {
    padding: 1rem;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .upload-area {
    padding: 1.5rem;
  }

  .item-actions {
    flex-wrap: wrap;
    justify-content: center;
  }

  .pagination {
    flex-direction: column;
    gap: 1rem;
  }
}
</style>