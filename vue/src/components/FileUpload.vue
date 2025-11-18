<template>
  <div class="file-upload-container">
    <!-- 文件选择区域 -->
    <div 
      class="drop-zone" 
      :class="{ 'dragging': isDragging, 'uploading': isUploading }"
      @dragover.prevent="handleDragOver"
      @dragenter.prevent="handleDragEnter"  
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
      @click="openFileSelector"
    >
      <input 
        ref="fileInput"
        type="file" 
        multiple 
        :accept="acceptedTypes"
        @change="handleFileSelect"
        style="display: none"
      />
      
      <div class="drop-zone-content">
        <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="17,8 12,3 7,8"/>
          <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
        
        <div class="upload-text">
          <span class="primary-text">点击选择文件或拖拽到此处</span>
          <span class="secondary-text">支持图片 (JPG, PNG, GIF) 和文本文件 (TXT, MD, JSON, Python等)</span>
          <span class="size-limit">单个文件最大: 图片10MB, 文本50MB</span>
        </div>
      </div>
    </div>

    <!-- 文件列表 -->
    <div v-if="files.length > 0" class="file-list">
      <div class="file-list-header">
        <span>已选择文件 ({{ files.length }})</span>
        <button @click="clearAllFiles" class="clear-all-btn">清空</button>
      </div>
      
      <div class="file-items">
        <div 
          v-for="(file, index) in files" 
          :key="file.id"
          class="file-item"
          :class="{ 'uploading': file.status === 'uploading', 'error': file.status === 'error', 'success': file.status === 'success' }"
        >
          <!-- 文件图标和信息 -->
          <div class="file-info">
            <div class="file-icon">
              {{ getFileIcon(file) }}
            </div>
            <div class="file-details">
              <div class="file-name" :title="file.name">{{ file.name }}</div>
              <div class="file-meta">
                {{ formatFileSize(file.size) }} • {{ getFileType(file) }}
              </div>
            </div>
          </div>

          <!-- 状态和操作 -->
          <div class="file-actions">
            <div v-if="file.status === 'uploading'" class="upload-progress">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: file.progress + '%' }"></div>
              </div>
              <span class="progress-text">{{ file.progress }}%</span>
            </div>
            
            <div v-else-if="file.status === 'success'" class="success-indicator">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20,6 9,17 4,12"></polyline>
              </svg>
            </div>
            
            <div v-else-if="file.status === 'error'" class="error-indicator">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="15" y1="9" x2="9" y2="15"></line>
                <line x1="9" y1="9" x2="15" y2="15"></line>
              </svg>
              <span class="error-message">{{ file.error }}</span>
            </div>
            
            <button 
              v-if="file.status !== 'uploading'"
              @click="removeFile(index)" 
              class="remove-btn"
              title="移除文件"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 上传控制 -->
    <div v-if="files.length > 0" class="upload-controls">
      <div class="upload-options">
        <label class="option-label">
          <input 
            v-model="uploadOptions.autoProcess" 
            type="checkbox"
          />
          自动处理文件内容
        </label>
      </div>
      
      <div class="upload-actions">
        <button 
          @click="startUpload" 
          :disabled="isUploading || files.every(f => f.status === 'success')"
          class="upload-btn primary"
        >
          <svg v-if="isUploading" class="spinner" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" opacity="0.25"/>
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" stroke-dasharray="63" stroke-dashoffset="63">
              <animate attributeName="stroke-dashoffset" dur="1s" values="63;0" repeatCount="indefinite"/>
            </circle>
          </svg>
          {{ isUploading ? '上传中...' : '开始上传' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { uploadSingleFile, uploadMultipleFiles } from '@/services/api.js'

// Props
const props = defineProps({
  maxFiles: {
    type: Number,
    default: 10
  },
  acceptTypes: {
    type: String,
    default: '.jpg,.jpeg,.png,.gif,.bmp,.webp,.txt,.md,.markdown,.py,.js,.json,.yaml,.yml'
  },
  autoUpload: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['upload-success', 'upload-error', 'files-changed'])

// Reactive data
const files = ref([])
const isDragging = ref(false)
const isUploading = ref(false)
const fileInput = ref(null)
const uploadOptions = ref({
  autoProcess: true
})

// Computed
const acceptedTypes = computed(() => props.acceptTypes)

// File handling methods
const openFileSelector = () => {
  if (!isUploading.value) {
    fileInput.value?.click()
  }
}

const handleFileSelect = (event) => {
  const selectedFiles = Array.from(event.target.files)
  addFiles(selectedFiles)
  // 清空 input，允许重复选择相同文件
  event.target.value = ''
}

const handleDragOver = (event) => {
  event.preventDefault()
}

const handleDragEnter = (event) => {
  event.preventDefault()
  isDragging.value = true
}

const handleDragLeave = (event) => {
  event.preventDefault()
  // 只有当离开整个拖拽区域时才取消拖拽状态
  if (!event.currentTarget.contains(event.relatedTarget)) {
    isDragging.value = false
  }
}

const handleDrop = (event) => {
  event.preventDefault()
  isDragging.value = false
  
  const droppedFiles = Array.from(event.dataTransfer.files)
  addFiles(droppedFiles)
}

const addFiles = (newFiles) => {
  // 检查文件数量限制
  if (files.value.length + newFiles.length > props.maxFiles) {
    alert(`最多只能选择 ${props.maxFiles} 个文件`)
    return
  }

  // 过滤和验证文件
  const validFiles = newFiles.filter(file => {
    // 检查文件类型
    const fileName = file.name.toLowerCase()
    const acceptedExtensions = props.acceptTypes.split(',').map(ext => ext.trim())
    const isValidType = acceptedExtensions.some(ext => fileName.endsWith(ext.replace('.', '')))
    
    if (!isValidType) {
      alert(`不支持的文件类型: ${file.name}`)
      return false
    }

    // 检查文件大小
    const isImage = /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(fileName)
    const maxSize = isImage ? 10 * 1024 * 1024 : 50 * 1024 * 1024 // 10MB for images, 50MB for text
    
    if (file.size > maxSize) {
      alert(`文件过大: ${file.name} (最大 ${isImage ? '10MB' : '50MB'})`)
      return false
    }

    return true
  })

  // 添加到文件列表
  validFiles.forEach(file => {
    const fileItem = {
      id: Date.now() + Math.random(),
      file: file,
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'pending', // pending, uploading, success, error
      progress: 0,
      error: null,
      result: null
    }
    files.value.push(fileItem)
  })

  emit('files-changed', files.value)

  // 自动上传
  if (props.autoUpload && validFiles.length > 0) {
    startUpload()
  }
}

const removeFile = (index) => {
  files.value.splice(index, 1)
  emit('files-changed', files.value)
}

const clearAllFiles = () => {
  files.value = []
  emit('files-changed', files.value)
}

// Upload methods
const startUpload = async () => {
  if (isUploading.value) return

  const pendingFiles = files.value.filter(f => f.status === 'pending' || f.status === 'error')
  if (pendingFiles.length === 0) return

  isUploading.value = true

  try {
    if (pendingFiles.length === 1) {
      await uploadSingleFileItem(pendingFiles[0])
    } else {
      await uploadMultipleFileItems(pendingFiles)
    }
    
    // 检查是否所有文件都成功上传
    const successfulFiles = files.value.filter(f => f.status === 'success')
    if (successfulFiles.length > 0) {
      emit('upload-success', {
        files: successfulFiles,
        results: successfulFiles.map(f => f.result)
      })
    }
    
  } catch (error) {
    console.error('文件上传失败:', error)
    emit('upload-error', error)
  } finally {
    isUploading.value = false
  }
}

const uploadSingleFileItem = async (fileItem) => {
  fileItem.status = 'uploading'
  fileItem.progress = 0
  
  try {
    // 模拟上传进度
    const progressInterval = setInterval(() => {
      if (fileItem.progress < 90) {
        fileItem.progress += Math.random() * 20
      }
    }, 200)

    const formData = new FormData()
    formData.append('file', fileItem.file)
    formData.append('question', '')
    formData.append('context', '')
    formData.append('model_name', 'default')

    const result = await uploadSingleFile(formData)
    
    clearInterval(progressInterval)
    fileItem.progress = 100
    
    if (result.success) {
      fileItem.status = 'success'
      fileItem.result = result.data
    } else {
      fileItem.status = 'error'
      fileItem.error = result.error || '上传失败'
    }
  } catch (error) {
    fileItem.status = 'error'
    fileItem.error = error.message || '上传异常'
  }
}

const uploadMultipleFileItems = async (fileItems) => {
  const formData = new FormData()
  
  fileItems.forEach((fileItem, index) => {
    fileItem.status = 'uploading'
    fileItem.progress = 0
    formData.append('files', fileItem.file)
  })
  
  formData.append('question', '')
  formData.append('context', '')
  formData.append('model_name', 'default')

  try {
    // 模拟进度更新
    const progressInterval = setInterval(() => {
      fileItems.forEach(fileItem => {
        if (fileItem.progress < 90) {
          fileItem.progress += Math.random() * 15
        }
      })
    }, 300)

    const result = await uploadMultipleFiles(formData)
    
    clearInterval(progressInterval)
    
    fileItems.forEach((fileItem, index) => {
      fileItem.progress = 100
      
      if (result.success) {
        const individualResult = result.data.individual_results?.[index]
        if (individualResult?.success) {
          fileItem.status = 'success'
          fileItem.result = individualResult
        } else {
          fileItem.status = 'error'
          fileItem.error = individualResult?.error || '处理失败'
        }
      } else {
        fileItem.status = 'error'
        fileItem.error = result.error || '批量上传失败'
      }
    })
    
  } catch (error) {
    fileItems.forEach(fileItem => {
      fileItem.status = 'error'
      fileItem.error = error.message || '上传异常'
    })
  }
}

// Utility methods
const getFileIcon = (file) => {
  const name = file.name.toLowerCase()
  if (/\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(name)) return '🖼️'
  if (/\.(txt|md|markdown)$/i.test(name)) return '📄'
  if (/\.(py|js|json|yaml|yml)$/i.test(name)) return '💻'
  return '📁'
}

const getFileType = (file) => {
  const name = file.name.toLowerCase()
  if (/\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(name)) return '图片'
  if (/\.(txt|md|markdown)$/i.test(name)) return '文本'
  if (/\.(py|js|json|yaml|yml)$/i.test(name)) return '代码'
  return '文件'
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

// Expose methods for parent component
defineExpose({
  startUpload,
  clearAllFiles,
  files: files
})
</script>

<style scoped>
.file-upload-container {
  width: 100%;
  max-width: 600px;
  margin: 0 auto;
}

.drop-zone {
  border: 2px dashed var(--border-color);
  border-radius: 12px;
  padding: 32px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: var(--secondary-bg);
}

.drop-zone:hover {
  border-color: var(--primary-color);
  background-color: var(--hover-bg);
}

.drop-zone.dragging {
  border-color: var(--primary-color);
  background-color: var(--primary-color-light);
  transform: scale(1.02);
}

.drop-zone.uploading {
  pointer-events: none;
  opacity: 0.7;
}

.drop-zone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.upload-icon {
  width: 48px;
  height: 48px;
  color: var(--text-secondary);
  transition: color 0.3s ease;
}

.drop-zone:hover .upload-icon {
  color: var(--primary-color);
}

.upload-text {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.primary-text {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
}

.secondary-text {
  font-size: 14px;
  color: var(--text-secondary);
}

.size-limit {
  font-size: 12px;
  color: var(--text-hint);
}

.file-list {
  margin-top: 24px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background-color: var(--primary-bg);
}

.file-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--secondary-bg);
  font-size: 14px;
  font-weight: 500;
}

.clear-all-btn {
  background: none;
  border: none;
  color: var(--danger-color);
  cursor: pointer;
  font-size: 14px;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.clear-all-btn:hover {
  background-color: var(--danger-color-light);
}

.file-items {
  max-height: 300px;
  overflow-y: auto;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  transition: background-color 0.2s;
}

.file-item:last-child {
  border-bottom: none;
}

.file-item:hover {
  background-color: var(--hover-bg);
}

.file-item.uploading {
  background-color: var(--info-bg);
}

.file-item.success {
  background-color: var(--success-bg);
}

.file-item.error {
  background-color: var(--danger-bg);
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.file-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.file-details {
  min-width: 0;
  flex: 1;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-meta {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.file-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.upload-progress {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-bar {
  width: 80px;
  height: 4px;
  background-color: var(--border-color);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: var(--primary-color);
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 12px;
  color: var(--text-secondary);
  min-width: 35px;
}

.success-indicator,
.error-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
}

.success-indicator svg {
  width: 16px;
  height: 16px;
  color: var(--success-color);
}

.error-indicator svg {
  width: 16px;
  height: 16px;
  color: var(--danger-color);
}

.error-message {
  font-size: 12px;
  color: var(--danger-color);
}

.remove-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  color: var(--text-secondary);
  transition: all 0.2s;
}

.remove-btn:hover {
  color: var(--danger-color);
  background-color: var(--danger-color-light);
}

.remove-btn svg {
  width: 16px;
  height: 16px;
}

.upload-controls {
  margin-top: 16px;
  padding: 16px;
  background-color: var(--secondary-bg);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.upload-options {
  margin-bottom: 12px;
}

.option-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text-primary);
  cursor: pointer;
}

.option-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
}

.upload-actions {
  display: flex;
  justify-content: flex-end;
}

.upload-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-btn.primary {
  background-color: var(--primary-color);
  color: white;
}

.upload-btn.primary:hover:not(:disabled) {
  background-color: var(--primary-color-dark);
}

.upload-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner {
  width: 16px;
  height: 16px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .file-upload-container {
    max-width: 100%;
  }
  
  .drop-zone {
    padding: 24px 16px;
  }
  
  .file-item {
    padding: 10px 12px;
  }
  
  .file-info {
    gap: 8px;
  }
  
  .upload-controls {
    padding: 12px;
  }
}
</style> 