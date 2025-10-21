<template>
  <div class="research-projects">
    <div class="page-header">
      <h1>研究项目</h1>
      <button @click="showCreateModal = true" class="btn-primary">
        <i class="fas fa-plus"></i> 创建新项目
      </button>
    </div>

    <!-- 筛选和搜索 -->
    <div class="filters">
      <div class="filter-group">
        <label>状态:</label>
        <select v-model="filterStatus" @change="loadProjects">
          <option value="">全部</option>
          <option value="pending">待执行</option>
          <option value="running">执行中</option>
          <option value="completed">已完成</option>
          <option value="failed">失败</option>
        </select>
      </div>
      <div class="search-box">
        <input 
          v-model="searchQuery" 
          @input="loadProjects"
          placeholder="搜索项目..."
          type="text"
        />
        <i class="fas fa-search"></i>
      </div>
    </div>

    <!-- 项目列表 -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="projects.length === 0" class="empty-state">
      <i class="fas fa-folder-open"></i>
      <p>还没有研究项目</p>
      <button @click="showCreateModal = true" class="btn-secondary">
        创建第一个项目
      </button>
    </div>

    <div v-else class="projects-grid">
      <div 
        v-for="project in projects" 
        :key="project.id"
        class="project-card"
        @click="viewProject(project.id)"
      >
        <div class="project-header">
          <h3>{{ project.title }}</h3>
          <span :class="['status-badge', project.status]">
            {{ getStatusText(project.status) }}
          </span>
        </div>
        
        <p class="project-description">{{ project.description || '暂无描述' }}</p>
        
        <div class="project-meta">
          <div class="meta-item">
            <i class="fas fa-search"></i>
            <span>{{ project.query }}</span>
          </div>
          <div class="meta-item">
            <i class="fas fa-calendar"></i>
            <span>{{ formatDate(project.created_at) }}</span>
          </div>
        </div>

        <div class="project-progress">
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: project.progress + '%' }"
            ></div>
          </div>
          <span class="progress-text">{{ project.progress }}%</span>
        </div>

        <div class="project-actions" @click.stop>
          <button 
            v-if="project.status === 'pending'"
            @click="executeProject(project.id)"
            class="btn-action btn-execute"
          >
            <i class="fas fa-play"></i> 执行
          </button>
          <button 
            @click="viewProject(project.id)"
            class="btn-action btn-view"
          >
            <i class="fas fa-eye"></i> 查看
          </button>
          <button 
            @click="deleteProject(project.id)"
            class="btn-action btn-delete"
          >
            <i class="fas fa-trash"></i> 删除
          </button>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="totalPages > 1" class="pagination">
      <button 
        @click="currentPage--" 
        :disabled="currentPage === 1"
        class="btn-page"
      >
        上一页
      </button>
      <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
      <button 
        @click="currentPage++" 
        :disabled="currentPage === totalPages"
        class="btn-page"
      >
        下一页
      </button>
    </div>

    <!-- 创建项目模态框 -->
    <div v-if="showCreateModal" class="modal-overlay" @click="showCreateModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>创建研究项目</h2>
          <button @click="showCreateModal = false" class="btn-close">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <form @submit.prevent="createProject" class="modal-body">
          <div class="form-group">
            <label>项目标题 *</label>
            <input 
              v-model="newProject.title" 
              type="text" 
              required
              placeholder="例如: AI在医疗中的应用研究"
            />
          </div>

          <div class="form-group">
            <label>研究问题 *</label>
            <input 
              v-model="newProject.query" 
              type="text" 
              required
              placeholder="例如: AI技术如何改进医疗诊断"
            />
          </div>

          <div class="form-group">
            <label>项目描述</label>
            <textarea 
              v-model="newProject.description" 
              rows="4"
              placeholder="详细描述研究目标和范围..."
            ></textarea>
          </div>

          <div class="form-actions">
            <button type="button" @click="showCreateModal = false" class="btn-secondary">
              取消
            </button>
            <button type="submit" class="btn-primary" :disabled="creating">
              {{ creating ? '创建中...' : '创建项目' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { researchAPI, documentAPI } from '../services/api'
import { useNotifications } from '@/composables/useNotifications.js'

export default {
  name: 'ResearchProjects',
  data() {
    return {
      projects: [],
      loading: false,
      creating: false,
      showCreateModal: false,
      filterStatus: '',
      searchQuery: '',
      currentPage: 1,
      pageSize: 12,
      totalPages: 1,
      newProject: {
        title: '',
        query: '',
        description: ''
      }
    }
  },
  setup() {
    const { showNotification } = useNotifications()
    return { showNotification }
  },
  mounted() {
    this.loadProjects()
  },
  methods: {
    async loadProjects() {
      this.loading = true
      try {
        // 由于后端暂时没有项目管理API，这里使用会话历史作为模拟
        // TODO: 后续需要实现真正的项目管理API

        // 创建模拟数据结构来展示功能
        const mockProjects = this.generateMockProjects()

        // 应用过滤
        let filteredProjects = mockProjects
        if (this.filterStatus) {
          filteredProjects = mockProjects.filter(p => p.status === this.filterStatus)
        }
        if (this.searchQuery) {
          filteredProjects = filteredProjects.filter(p =>
            p.title.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
            p.description.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
            p.query.toLowerCase().includes(this.searchQuery.toLowerCase())
          )
        }

        // 分页
        const startIndex = (this.currentPage - 1) * this.pageSize
        const endIndex = startIndex + this.pageSize
        this.projects = filteredProjects.slice(startIndex, endIndex)
        this.totalPages = Math.ceil(filteredProjects.length / this.pageSize)

      } catch (error) {
        console.error('加载项目失败:', error)
        this.showNotification('加载项目失败', 'error')
      } finally {
        this.loading = false
      }
    },

    // 生成模拟项目数据（用于演示）
    generateMockProjects() {
      return [
        {
          id: '1',
          title: '人工智能在医疗诊断中的应用研究',
          description: '深入分析AI技术在医疗诊断领域的应用现状和发展趋势',
          query: '人工智能医疗诊断应用现状与发展趋势',
          status: 'completed',
          progress: 100,
          created_at: '2024-01-15T10:30:00Z',
          session_id: 'session_1'
        },
        {
          id: '2',
          title: '区块链技术在供应链管理中的创新应用',
          description: '探讨区块链技术如何提升供应链管理的透明度和效率',
          query: '区块链供应链管理创新应用',
          status: 'running',
          progress: 65,
          created_at: '2024-01-16T14:20:00Z',
          session_id: 'session_2'
        },
        {
          id: '3',
          title: '可持续能源发展策略研究',
          description: '分析全球可持续能源发展现状及未来策略建议',
          query: '可持续能源发展现状与策略',
          status: 'pending',
          progress: 0,
          created_at: '2024-01-17T09:15:00Z',
          session_id: 'session_3'
        }
      ]
    },
    
    async createProject() {
      this.creating = true
      try {
        // 由于后端没有项目管理API，这里使用研究API作为替代
        const response = await researchAPI.startResearch(this.newProject.query)

        // 创建模拟项目对象
        const newProject = {
          id: response.session_id,
          title: this.newProject.title,
          description: this.newProject.description,
          query: this.newProject.query,
          status: 'running',
          progress: 25,
          created_at: new Date().toISOString(),
          session_id: response.session_id
        }

        this.projects.unshift(newProject)
        this.showNotification('研究项目创建成功', 'success')
        this.showCreateModal = false
        this.newProject = { title: '', query: '', description: '' }
      } catch (error) {
        console.error('创建项目失败:', error)
        this.showNotification('创建项目失败: ' + error.message, 'error')
      } finally {
        this.creating = false
      }
    },
    
    async executeProject(projectId) {
      try {
        // 找到对应项目并启动研究
        const project = this.projects.find(p => p.id === projectId)
        if (project) {
          await researchAPI.startResearch(project.query, project.session_id)
          this.showNotification('项目已开始执行', 'success')
          project.status = 'running'
          project.progress = 25
        }
      } catch (error) {
        console.error('执行项目失败:', error)
        this.showNotification('执行项目失败: ' + error.message, 'error')
      }
    },
    
    viewProject(projectId) {
      this.$router.push(`/research/projects/${projectId}`)
    },
    
    async deleteProject(projectId) {
      if (!confirm('确定要删除这个项目吗？')) return

      try {
        // 从本地数组中删除项目（因为没有后端API）
        const index = this.projects.findIndex(p => p.id === projectId)
        if (index !== -1) {
          this.projects.splice(index, 1)
          this.showNotification('项目已删除', 'success')
        }
      } catch (error) {
        console.error('删除项目失败:', error)
        this.showNotification('删除项目失败: ' + error.message, 'error')
      }
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
    
    formatDate(dateString) {
      const date = new Date(dateString)
      return date.toLocaleDateString('zh-CN')
    }
  }
}
</script>

<style scoped>
.research-projects {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 2rem;
  color: #2c3e50;
}

.filters {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  align-items: center;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-group label {
  font-weight: 500;
  color: #666;
}

.filter-group select {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.search-box {
  position: relative;
  flex: 1;
  max-width: 400px;
}

.search-box input {
  width: 100%;
  padding: 0.5rem 2.5rem 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.search-box i {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: #999;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.project-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  cursor: pointer;
  transition: all 0.3s;
}

.project-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
  transform: translateY(-2px);
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  margin-bottom: 1rem;
}

.project-header h3 {
  font-size: 1.2rem;
  color: #2c3e50;
  margin: 0;
  flex: 1;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-badge.pending {
  background: #fff3cd;
  color: #856404;
}

.status-badge.running {
  background: #cfe2ff;
  color: #084298;
}

.status-badge.completed {
  background: #d1e7dd;
  color: #0f5132;
}

.status-badge.failed {
  background: #f8d7da;
  color: #842029;
}

.project-description {
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 1rem;
  line-height: 1.5;
}

.project-meta {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: #666;
}

.meta-item i {
  color: #999;
  width: 16px;
}

.project-progress {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: #e9ecef;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4CAF50, #8BC34A);
  transition: width 0.3s;
}

.progress-text {
  font-size: 0.85rem;
  color: #666;
  min-width: 40px;
  text-align: right;
}

.project-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-action {
  flex: 1;
  padding: 0.5rem;
  border: none;
  border-radius: 4px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
}

.btn-execute {
  background: #4CAF50;
  color: white;
}

.btn-execute:hover {
  background: #45a049;
}

.btn-view {
  background: #2196F3;
  color: white;
}

.btn-view:hover {
  background: #0b7dda;
}

.btn-delete {
  background: #f44336;
  color: white;
}

.btn-delete:hover {
  background: #da190b;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: #999;
}

.empty-state i {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-state p {
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

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;
}

.btn-page {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-page:hover:not(:disabled) {
  background: #f5f5f5;
}

.btn-page:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: #666;
  font-size: 0.9rem;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #eee;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #2c3e50;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.btn-close:hover {
  background: #f5f5f5;
  color: #666;
}

.modal-body {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #333;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
  font-family: inherit;
}

.form-group textarea {
  resize: vertical;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 2rem;
}

.btn-primary,
.btn-secondary {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #4CAF50;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #45a049;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f5f5f5;
  color: #666;
}

.btn-secondary:hover {
  background: #e0e0e0;
}
</style>
