<template>
  <div class="project-detail">
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="project" class="detail-container">
      <!-- 头部 -->
      <div class="detail-header">
        <button @click="$router.back()" class="btn-back">
          <i class="fas fa-arrow-left"></i> 返回
        </button>
        <div class="header-info">
          <h1>{{ project.project.title }}</h1>
          <span :class="['status-badge', project.project.status]">
            {{ getStatusText(project.project.status) }}
          </span>
        </div>
      </div>

      <!-- 项目信息卡片 -->
      <div class="info-cards">
        <div class="info-card">
          <i class="fas fa-search"></i>
          <div>
            <h3>研究问题</h3>
            <p>{{ project.project.query }}</p>
          </div>
        </div>
        <div class="info-card">
          <i class="fas fa-file-alt"></i>
          <div>
            <h3>文档数量</h3>
            <p>{{ project.documents_count }} 个</p>
          </div>
        </div>
        <div class="info-card">
          <i class="fas fa-tasks"></i>
          <div>
            <h3>任务数量</h3>
            <p>{{ project.tasks_count }} 个</p>
          </div>
        </div>
        <div class="info-card">
          <i class="fas fa-chart-line"></i>
          <div>
            <h3>进度</h3>
            <p>{{ project.project.progress }}%</p>
          </div>
        </div>
      </div>

      <!-- 描述 -->
      <div v-if="project.project.description" class="section">
        <h2>项目描述</h2>
        <p class="description">{{ project.project.description }}</p>
      </div>

      <!-- 标签页 -->
      <div class="tabs">
        <button 
          v-for="tab in tabs" 
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="['tab', { active: activeTab === tab.id }]"
        >
          <i :class="tab.icon"></i>
          {{ tab.label }}
        </button>
      </div>

      <!-- 标签页内容 -->
      <div class="tab-content">
        <!-- 报告 -->
        <div v-if="activeTab === 'report'" class="report-section">
          <div v-if="project.final_report" class="report-content">
            <div class="report-header">
              <h2>最终报告</h2>
              <button @click="downloadReport" class="btn-download">
                <i class="fas fa-download"></i> 下载报告
              </button>
            </div>
            <div class="markdown-content" v-html="renderMarkdown(project.final_report)"></div>
          </div>
          <div v-else-if="project.draft_report" class="report-content">
            <div class="report-header">
              <h2>草稿报告</h2>
              <p class="draft-notice">此报告仍在审查中</p>
            </div>
            <div class="markdown-content" v-html="renderMarkdown(project.draft_report)"></div>
          </div>
          <div v-else class="empty-state">
            <i class="fas fa-file-alt"></i>
            <p>报告尚未生成</p>
          </div>
        </div>

        <!-- 文档 -->
        <div v-if="activeTab === 'documents'" class="documents-section">
          <div v-if="documents.length > 0" class="documents-list">
            <div v-for="doc in documents" :key="doc.id" class="document-item">
              <div class="doc-header">
                <h3>{{ doc.title }}</h3>
                <span :class="['source-badge', doc.source_type]">
                  {{ doc.source_type }}
                </span>
              </div>
              <p class="doc-content">{{ doc.content.substring(0, 200) }}...</p>
              <div class="doc-meta">
                <span v-if="doc.url" class="doc-url">
                  <i class="fas fa-link"></i>
                  <a :href="doc.url" target="_blank">{{ doc.url }}</a>
                </span>
                <span class="doc-score">
                  相关度: {{ (doc.relevance_score * 100).toFixed(1) }}%
                </span>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <i class="fas fa-folder-open"></i>
            <p>暂无文档</p>
          </div>
        </div>

        <!-- 任务历史 -->
        <div v-if="activeTab === 'tasks'" class="tasks-section">
          <div v-if="tasks.length > 0" class="tasks-list">
            <div v-for="task in tasks" :key="task.id" class="task-item">
              <div class="task-header">
                <h3>{{ task.task_name }}</h3>
                <span :class="['task-status', task.status]">
                  {{ task.status }}
                </span>
              </div>
              <p v-if="task.description" class="task-description">
                {{ task.description }}
              </p>
              <div class="task-meta">
                <span><i class="fas fa-clock"></i> {{ formatDate(task.created_at) }}</span>
                <span v-if="task.duration_seconds">
                  <i class="fas fa-hourglass-half"></i> 
                  {{ formatDuration(task.duration_seconds) }}
                </span>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <i class="fas fa-tasks"></i>
            <p>暂无任务记录</p>
          </div>
        </div>

        <!-- 产物 -->
        <div v-if="activeTab === 'artifacts'" class="artifacts-section">
          <div v-if="artifacts.length > 0" class="artifacts-list">
            <div v-for="artifact in artifacts" :key="artifact.id" class="artifact-item">
              <i :class="getArtifactIcon(artifact.artifact_type)"></i>
              <div class="artifact-info">
                <h3>{{ artifact.name }}</h3>
                <p>{{ artifact.description || '无描述' }}</p>
                <span class="artifact-size">
                  {{ formatFileSize(artifact.file_size) }}
                </span>
              </div>
              <button @click="downloadArtifact(artifact)" class="btn-download-small">
                <i class="fas fa-download"></i>
              </button>
            </div>
          </div>
          <div v-else class="empty-state">
            <i class="fas fa-box-open"></i>
            <p>暂无产物</p>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="error-state">
      <i class="fas fa-exclamation-triangle"></i>
      <p>项目不存在或加载失败</p>
      <button @click="$router.back()" class="btn-secondary">返回</button>
    </div>
  </div>
</template>

<script>
import api from '../services/api'
import { marked } from 'marked'

export default {
  name: 'ProjectDetail',
  data() {
    return {
      project: null,
      documents: [],
      tasks: [],
      artifacts: [],
      loading: true,
      activeTab: 'report',
      tabs: [
        { id: 'report', label: '研究报告', icon: 'fas fa-file-alt' },
        { id: 'documents', label: '文档', icon: 'fas fa-folder' },
        { id: 'tasks', label: '任务历史', icon: 'fas fa-tasks' },
        { id: 'artifacts', label: '产物', icon: 'fas fa-box' }
      ]
    }
  },
  mounted() {
    this.loadProjectDetail()
  },
  methods: {
    async loadProjectDetail() {
      this.loading = true
      try {
        const projectId = this.$route.params.id
        const response = await api.get(`/research/projects/${projectId}`)
        this.project = response.data
        
        // 加载文档、任务等
        await this.loadDocuments(projectId)
        await this.loadTasks(projectId)
        await this.loadArtifacts(projectId)
      } catch (error) {
        console.error('加载项目详情失败:', error)
        this.$toast?.error('加载项目详情失败')
      } finally {
        this.loading = false
      }
    },
    
    async loadDocuments(projectId) {
      try {
        // 这里需要添加获取项目文档的API
        // const response = await api.get(`/research/projects/${projectId}/documents`)
        // this.documents = response.data
        this.documents = [] // 临时
      } catch (error) {
        console.error('加载文档失败:', error)
      }
    },
    
    async loadTasks(projectId) {
      try {
        // 这里需要添加获取项目任务的API
        // const response = await api.get(`/research/projects/${projectId}/tasks`)
        // this.tasks = response.data
        this.tasks = [] // 临时
      } catch (error) {
        console.error('加载任务失败:', error)
      }
    },
    
    async loadArtifacts(projectId) {
      try {
        // 这里需要添加获取项目产物的API
        // const response = await api.get(`/research/projects/${projectId}/artifacts`)
        // this.artifacts = response.data
        this.artifacts = [] // 临时
      } catch (error) {
        console.error('加载产物失败:', error)
      }
    },
    
    renderMarkdown(content) {
      return marked(content || '')
    },
    
    downloadReport() {
      const content = this.project.final_report || this.project.draft_report
      const blob = new Blob([content], { type: 'text/markdown' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${this.project.project.title}_report.md`
      a.click()
      URL.revokeObjectURL(url)
    },
    
    downloadArtifact(artifact) {
      // 实现下载产物的逻辑
      console.log('下载产物:', artifact)
    },
    
    getStatusText(status) {
      const statusMap = {
        pending: '待执行',
        running: '执行中',
        completed: '已完成',
        failed: '失败'
      }
      return statusMap[status] || status
    },
    
    getArtifactIcon(type) {
      const iconMap = {
        report: 'fas fa-file-alt',
        chart: 'fas fa-chart-bar',
        code: 'fas fa-code',
        ppt: 'fas fa-file-powerpoint',
        default: 'fas fa-file'
      }
      return iconMap[type] || iconMap.default
    },
    
    formatDate(dateString) {
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN')
    },
    
    formatDuration(seconds) {
      if (seconds < 60) return `${seconds.toFixed(0)}秒`
      if (seconds < 3600) return `${(seconds / 60).toFixed(1)}分钟`
      return `${(seconds / 3600).toFixed(1)}小时`
    },
    
    formatFileSize(bytes) {
      if (!bytes) return '未知'
      if (bytes < 1024) return `${bytes} B`
      if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
      return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    }
  }
}
</script>

<style scoped>
.project-detail {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.detail-header {
  margin-bottom: 2rem;
}

.btn-back {
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 0.9rem;
  padding: 0.5rem 0;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-back:hover {
  color: #333;
}

.header-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-info h1 {
  font-size: 2rem;
  color: #2c3e50;
  margin: 0;
}

.status-badge {
  padding: 0.5rem 1rem;
  border-radius: 16px;
  font-size: 0.85rem;
  font-weight: 500;
}

.status-badge.pending { background: #fff3cd; color: #856404; }
.status-badge.running { background: #cfe2ff; color: #084298; }
.status-badge.completed { background: #d1e7dd; color: #0f5132; }
.status-badge.failed { background: #f8d7da; color: #842029; }

.info-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.info-card {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  gap: 1rem;
}

.info-card i {
  font-size: 2rem;
  color: #4CAF50;
}

.info-card h3 {
  font-size: 0.85rem;
  color: #999;
  margin: 0 0 0.25rem 0;
}

.info-card p {
  font-size: 1.2rem;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.section {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin-bottom: 2rem;
}

.section h2 {
  font-size: 1.2rem;
  color: #2c3e50;
  margin: 0 0 1rem 0;
}

.description {
  color: #666;
  line-height: 1.6;
}

.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  border-bottom: 2px solid #eee;
}

.tab {
  padding: 1rem 1.5rem;
  border: none;
  background: none;
  cursor: pointer;
  color: #666;
  font-size: 0.9rem;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.tab:hover {
  color: #333;
}

.tab.active {
  color: #4CAF50;
  border-bottom-color: #4CAF50;
}

.tab-content {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  min-height: 400px;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #eee;
}

.report-header h2 {
  margin: 0;
  color: #2c3e50;
}

.draft-notice {
  color: #ff9800;
  font-size: 0.9rem;
  margin: 0.5rem 0 0 0;
}

.btn-download {
  padding: 0.5rem 1rem;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-download:hover {
  background: #45a049;
}

.markdown-content {
  line-height: 1.8;
  color: #333;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3 {
  color: #2c3e50;
  margin-top: 1.5rem;
  margin-bottom: 1rem;
}

.markdown-content p {
  margin-bottom: 1rem;
}

.markdown-content code {
  background: #f5f5f5;
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}

.documents-list,
.tasks-list,
.artifacts-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.document-item,
.task-item,
.artifact-item {
  padding: 1.5rem;
  border: 1px solid #eee;
  border-radius: 8px;
  transition: all 0.2s;
}

.document-item:hover,
.task-item:hover,
.artifact-item:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.doc-header,
.task-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  margin-bottom: 0.5rem;
}

.doc-header h3,
.task-header h3 {
  font-size: 1.1rem;
  color: #2c3e50;
  margin: 0;
  flex: 1;
}

.source-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
}

.source-badge.kimi { background: #e3f2fd; color: #1976d2; }
.source-badge.arxiv { background: #f3e5f5; color: #7b1fa2; }
.source-badge.wikipedia { background: #e8f5e9; color: #388e3c; }

.doc-content {
  color: #666;
  line-height: 1.6;
  margin-bottom: 0.5rem;
}

.doc-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
  color: #999;
}

.doc-url {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.doc-url a {
  color: #2196F3;
  text-decoration: none;
}

.doc-url a:hover {
  text-decoration: underline;
}

.task-status {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.task-status.pending { background: #fff3cd; color: #856404; }
.task-status.running { background: #cfe2ff; color: #084298; }
.task-status.completed { background: #d1e7dd; color: #0f5132; }
.task-status.failed { background: #f8d7da; color: #842029; }

.task-description {
  color: #666;
  margin: 0.5rem 0;
}

.task-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.85rem;
  color: #999;
}

.task-meta span {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.artifact-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.artifact-item i {
  font-size: 2rem;
  color: #4CAF50;
}

.artifact-info {
  flex: 1;
}

.artifact-info h3 {
  font-size: 1rem;
  color: #2c3e50;
  margin: 0 0 0.25rem 0;
}

.artifact-info p {
  color: #666;
  font-size: 0.85rem;
  margin: 0 0 0.25rem 0;
}

.artifact-size {
  font-size: 0.75rem;
  color: #999;
}

.btn-download-small {
  padding: 0.5rem 1rem;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-download-small:hover {
  background: #45a049;
}

.empty-state,
.error-state {
  text-align: center;
  padding: 4rem 2rem;
  color: #999;
}

.empty-state i,
.error-state i {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-state p,
.error-state p {
  font-size: 1.2rem;
  margin-bottom: 1.5rem;
}

.loading {
  text-align: center;
  padding: 4rem 2rem;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
