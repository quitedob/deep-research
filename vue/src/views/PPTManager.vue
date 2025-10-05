<template>
  <div class="ppt-manager">
    <div class="header">
      <h1>PPT 管理</h1>
      <p class="subtitle">创建、编辑和管理您的演示文稿</p>
    </div>

    <!-- 操作栏 -->
    <div class="actions-bar">
      <button @click="showCreateDialog = true" class="btn-primary">
        <i class="fas fa-plus"></i>
        创建新 PPT
      </button>
      <button @click="loadPresentations" class="btn-secondary">
        <i class="fas fa-refresh"></i>
        刷新
      </button>
    </div>

    <!-- PPT 列表 -->
    <div v-if="presentations.length > 0" class="ppt-grid">
      <div v-for="ppt in presentations" :key="ppt.presentation_id" class="ppt-card">
        <div class="ppt-header">
          <h3>{{ ppt.title }}</h3>
          <span :class="['status', `status-${ppt.status}`]">
            {{ getStatusText(ppt.status) }}
          </span>
        </div>
        
        <div class="ppt-info">
          <p>创建时间: {{ formatDate(ppt.created_at) }}</p>
          <p v-if="ppt.updated_at">更新时间: {{ formatDate(ppt.updated_at) }}</p>
        </div>
        
        <div class="ppt-actions">
          <button @click="previewPPT(ppt.presentation_id)" class="btn-action">
            <i class="fas fa-eye"></i>
            预览
          </button>
          <button @click="editPPT(ppt.presentation_id)" class="btn-action">
            <i class="fas fa-edit"></i>
            编辑
          </button>
          <button @click="deletePPT(ppt.presentation_id)" class="btn-danger">
            <i class="fas fa-trash"></i>
            删除
          </button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <div class="empty-icon">📊</div>
      <h3>还没有演示文稿</h3>
      <p>点击上方按钮创建您的第一个 PPT</p>
    </div>

    <!-- 创建 PPT 对话框 -->
    <div v-if="showCreateDialog" class="modal-overlay" @click="closeCreateDialog">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h2>创建新的演示文稿</h2>
          <button @click="closeCreateDialog" class="close-btn">×</button>
        </div>
        
        <div class="modal-body">
          <form @submit.prevent="createPPT">
            <div class="form-group">
              <label>标题 *</label>
              <input 
                v-model="createForm.title" 
                type="text" 
                required 
                placeholder="输入演示文稿标题"
              />
            </div>
            
            <div class="form-group">
              <label>主题</label>
              <input 
                v-model="createForm.topic" 
                type="text" 
                placeholder="输入主题（可选）"
              />
            </div>
            
            <div class="form-group">
              <label>大纲</label>
              <textarea 
                v-model="outlineText" 
                placeholder="输入大纲，每行一个要点（可选）"
                rows="5"
              ></textarea>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label>幻灯片数量</label>
                <input 
                  v-model.number="createForm.n_slides" 
                  type="number" 
                  min="3" 
                  max="50" 
                  required
                />
              </div>
              
              <div class="form-group">
                <label>语言</label>
                <select v-model="createForm.language">
                  <option value="Chinese">中文</option>
                  <option value="English">英文</option>
                </select>
              </div>
            </div>
            
            <div class="form-group">
              <label>语气</label>
              <select v-model="createForm.tone">
                <option value="professional">专业</option>
                <option value="casual">轻松</option>
                <option value="academic">学术</option>
                <option value="creative">创意</option>
              </select>
            </div>
            
            <div class="form-actions">
              <button type="button" @click="closeCreateDialog" class="btn-secondary">
                取消
              </button>
              <button type="submit" class="btn-primary" :disabled="creating">
                {{ creating ? '创建中...' : '创建 PPT' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- PPT 预览对话框 -->
    <div v-if="showPreviewDialog" class="modal-overlay" @click="closePreviewDialog">
      <div class="modal modal-large" @click.stop>
        <div class="modal-header">
          <h2>{{ previewData.title }}</h2>
          <button @click="closePreviewDialog" class="close-btn">×</button>
        </div>
        
        <div class="modal-body">
          <div v-if="previewData.slides && previewData.slides.length > 0" class="slides-preview">
            <div class="slides-nav">
              <button 
                v-for="(slide, index) in previewData.slides" 
                :key="index"
                @click="currentSlide = index"
                :class="['slide-nav-btn', { active: currentSlide === index }]"
              >
                {{ index + 1 }}
              </button>
            </div>
            
            <div class="slide-content">
              <div class="slide-header">
                <h3>第 {{ currentSlide + 1 }} 页</h3>
                <button @click="editSlide(currentSlide + 1)" class="btn-edit">
                  编辑
                </button>
              </div>
              
              <div class="slide-body">
                <h4 v-if="previewData.slides[currentSlide].title" class="slide-title">
                  {{ previewData.slides[currentSlide].title }}
                </h4>
                
                <div v-if="previewData.slides[currentSlide].content.length > 0" class="slide-content-list">
                  <div 
                    v-for="(content, index) in previewData.slides[currentSlide].content" 
                    :key="index"
                    class="content-item"
                  >
                    {{ content }}
                  </div>
                </div>
                
                <div v-if="previewData.slides[currentSlide].notes" class="slide-notes">
                  <h5>备注:</h5>
                  <p>{{ previewData.slides[currentSlide].notes }}</p>
                </div>
              </div>
            </div>
          </div>
          
          <div v-else class="no-slides">
            <p>无法加载幻灯片内容</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 通知 -->
    <div v-if="notification" :class="['notification', notification.type]">
      {{ notification.message }}
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'PPTManager',
  data() {
    return {
      presentations: [],
      showCreateDialog: false,
      showPreviewDialog: false,
      creating: false,
      createForm: {
        title: '',
        topic: '',
        n_slides: 10,
        language: 'Chinese',
        tone: 'professional'
      },
      outlineText: '',
      previewData: {},
      currentSlide: 0,
      notification: null
    };
  },
  async mounted() {
    await this.loadPresentations();
  },
  methods: {
    async loadPresentations() {
      try {
        const response = await axios.get('/api/ppt/list');
        this.presentations = response.data.presentations;
      } catch (error) {
        this.showNotification('加载演示文稿列表失败', 'error');
      }
    },
    
    async createPPT() {
      if (!this.createForm.title.trim()) {
        this.showNotification('请输入标题', 'error');
        return;
      }
      
      this.creating = true;
      
      try {
        const requestData = { ...this.createForm };
        
        if (this.outlineText.trim()) {
          requestData.outline = this.outlineText.split('\n').filter(line => line.trim());
        }
        
        const response = await axios.post('/api/ppt/create', requestData);
        
        this.showNotification('PPT 创建成功', 'success');
        this.closeCreateDialog();
        await this.loadPresentations();
      } catch (error) {
        this.showNotification('创建 PPT 失败: ' + (error.response?.data?.detail || error.message), 'error');
      } finally {
        this.creating = false;
      }
    },
    
    async previewPPT(presentationId) {
      try {
        const response = await axios.get(`/api/ppt/${presentationId}/preview`);
        this.previewData = response.data;
        this.currentSlide = 0;
        this.showPreviewDialog = true;
      } catch (error) {
        this.showNotification('加载预览失败', 'error');
      }
    },
    
    editPPT(presentationId) {
      this.showNotification('编辑功能开发中', 'info');
    },
    
    editSlide(slideNumber) {
      this.showNotification(`编辑第 ${slideNumber} 页功能开发中`, 'info');
    },
    
    async deletePPT(presentationId) {
      if (!confirm('确定要删除这个演示文稿吗？')) return;
      
      try {
        await axios.delete(`/api/ppt/${presentationId}`);
        this.showNotification('演示文稿已删除', 'success');
        await this.loadPresentations();
      } catch (error) {
        this.showNotification('删除失败', 'error');
      }
    },
    
    closeCreateDialog() {
      this.showCreateDialog = false;
      this.createForm = {
        title: '',
        topic: '',
        n_slides: 10,
        language: 'Chinese',
        tone: 'professional'
      };
      this.outlineText = '';
    },
    
    closePreviewDialog() {
      this.showPreviewDialog = false;
      this.previewData = {};
      this.currentSlide = 0;
    },
    
    getStatusText(status) {
      const statusMap = {
        pending: '处理中',
        processing: '生成中',
        completed: '已完成',
        failed: '失败',
        ready: '就绪'
      };
      return statusMap[status] || status;
    },
    
    formatDate(dateString) {
      if (!dateString) return '-';
      return new Date(dateString).toLocaleString('zh-CN');
    },
    
    showNotification(message, type = 'info') {
      this.notification = { message, type };
      setTimeout(() => {
        this.notification = null;
      }, 3000);
    }
  }
};
</script>

<style scoped>
.ppt-manager {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  margin-bottom: 30px;
}

.header h1 {
  font-size: 28px;
  color: #333;
  margin-bottom: 8px;
}

.subtitle {
  color: #666;
  font-size: 14px;
}

.actions-bar {
  display: flex;
  gap: 15px;
  margin-bottom: 30px;
}

.btn-primary, .btn-secondary, .btn-action, .btn-danger {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #545b62;
}

.btn-action {
  background: #28a745;
  color: white;
  padding: 6px 12px;
  font-size: 12px;
}

.btn-action:hover {
  background: #218838;
}

.btn-danger {
  background: #dc3545;
  color: white;
  padding: 6px 12px;
  font-size: 12px;
}

.btn-danger:hover {
  background: #c82333;
}

.ppt-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.ppt-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: transform 0.2s;
}

.ppt-card:hover {
  transform: translateY(-2px);
}

.ppt-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.ppt-header h3 {
  font-size: 16px;
  color: #333;
  margin: 0;
  flex: 1;
}

.status {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-completed, .status-ready {
  background: #d4edda;
  color: #155724;
}

.status-processing, .status-pending {
  background: #fff3cd;
  color: #856404;
}

.status-failed {
  background: #f8d7da;
  color: #721c24;
}

.ppt-info {
  margin-bottom: 15px;
}

.ppt-info p {
  margin: 5px 0;
  font-size: 13px;
  color: #666;
}

.ppt-actions {
  display: flex;
  gap: 8px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.empty-state h3 {
  font-size: 20px;
  margin-bottom: 10px;
  color: #333;
}

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

.modal {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-large {
  max-width: 900px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #333;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-group textarea {
  resize: vertical;
}

.form-actions {
  display: flex;
  gap: 15px;
  justify-content: flex-end;
  margin-top: 30px;
}

.slides-preview {
  display: flex;
  gap: 20px;
}

.slides-nav {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 60px;
}

.slide-nav-btn {
  padding: 8px;
  border: 1px solid #ddd;
  background: white;
  cursor: pointer;
  border-radius: 4px;
  font-size: 14px;
}

.slide-nav-btn.active {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.slide-content {
  flex: 1;
}

.slide-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.slide-header h3 {
  margin: 0;
  color: #333;
}

.btn-edit {
  padding: 6px 12px;
  background: #ffc107;
  color: #333;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.btn-edit:hover {
  background: #e0a800;
}

.slide-body {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 6px;
  min-height: 300px;
}

.slide-title {
  font-size: 18px;
  color: #333;
  margin-bottom: 15px;
  text-align: center;
}

.slide-content-list {
  margin-bottom: 20px;
}

.content-item {
  margin-bottom: 10px;
  padding: 10px;
  background: white;
  border-radius: 4px;
  border-left: 3px solid #007bff;
}

.slide-notes {
  margin-top: 20px;
  padding: 15px;
  background: #fff3cd;
  border-radius: 4px;
}

.slide-notes h5 {
  margin: 0 0 10px 0;
  color: #856404;
}

.slide-notes p {
  margin: 0;
  color: #856404;
}

.no-slides {
  text-align: center;
  padding: 40px;
  color: #666;
}

.notification {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 15px 20px;
  border-radius: 4px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  z-index: 1001;
  animation: slideIn 0.3s ease-out;
}

.notification.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.notification.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.notification.info {
  background: #d1ecf1;
  color: #0c5460;
  border: 1px solid #bee5eb;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
</style>
