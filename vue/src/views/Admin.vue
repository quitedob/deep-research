<template>
  <div class="admin-dashboard">
    <div class="admin-header">
      <h1>管理员控制台</h1>
      <p class="subtitle">用户管理与系统监控</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">👥</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_users }}</div>
          <div class="stat-label">总用户数</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.active_users }}</div>
          <div class="stat-label">活跃用户</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">⭐</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.subscribed_users }}</div>
          <div class="stat-label">订阅用户</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">🔧</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.admin_users }}</div>
          <div class="stat-label">管理员</div>
        </div>
      </div>
    </div>

    <!-- 用户列表 -->
    <div class="users-section">
      <div class="section-header">
        <h2>用户列表</h2>
        <div class="filters">
          <select v-model="filters.role" @change="loadUsers" class="filter-select">
            <option value="">所有角色</option>
            <option value="free">免费用户</option>
            <option value="subscribed">订阅用户</option>
            <option value="admin">管理员</option>
          </select>
          
          <select v-model="filters.is_active" @change="loadUsers" class="filter-select">
            <option value="">所有状态</option>
            <option value="true">活跃</option>
            <option value="false">已封禁</option>
          </select>
          
          <button @click="loadUsers" class="btn-refresh">🔄 刷新</button>
        </div>
      </div>

      <div v-if="loading" class="loading">加载中...</div>
      
      <div v-else-if="error" class="error">{{ error }}</div>
      
      <div v-else class="users-table-container">
        <table class="users-table">
          <thead>
            <tr>
              <th>用户名</th>
              <th>邮箱</th>
              <th>角色</th>
              <th>状态</th>
              <th>注册时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td>{{ user.username }}</td>
              <td>{{ user.email || '-' }}</td>
              <td>
                <span :class="['role-badge', `role-${user.role}`]">
                  {{ getRoleLabel(user.role) }}
                </span>
              </td>
              <td>
                <span :class="['status-badge', user.is_active ? 'active' : 'inactive']">
                  {{ user.is_active ? '活跃' : '已封禁' }}
                </span>
              </td>
              <td>{{ formatDate(user.created_at) }}</td>
              <td class="actions">
                <button @click="viewUserDetail(user)" class="btn-action btn-view">
                  查看
                </button>
                <button 
                  @click="toggleUserActive(user)" 
                  :class="['btn-action', user.is_active ? 'btn-ban' : 'btn-unban']"
                >
                  {{ user.is_active ? '封禁' : '解封' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分页 -->
      <div class="pagination">
        <button 
          @click="prevPage" 
          :disabled="currentPage === 1"
          class="btn-page"
        >
          上一页
        </button>
        <span class="page-info">第 {{ currentPage }} 页</span>
        <button 
          @click="nextPage" 
          :disabled="users.length < pageSize"
          class="btn-page"
        >
          下一页
        </button>
      </div>
    </div>

    <!-- 用户详情模态框 -->
    <div v-if="selectedUser" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>用户详情</h3>
          <button @click="closeModal" class="btn-close">×</button>
        </div>
        
        <div class="modal-body">
          <div class="detail-section">
            <h4>基本信息</h4>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">用户名:</span>
                <span class="detail-value">{{ selectedUser.username }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">邮箱:</span>
                <span class="detail-value">{{ selectedUser.email || '-' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">角色:</span>
                <span class="detail-value">{{ getRoleLabel(selectedUser.role) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">状态:</span>
                <span class="detail-value">{{ selectedUser.is_active ? '活跃' : '已封禁' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">注册时间:</span>
                <span class="detail-value">{{ formatDate(selectedUser.created_at) }}</span>
              </div>
            </div>
          </div>

          <div class="detail-section">
            <h4>操作</h4>
            <div class="action-buttons">
              <button @click="viewUserConversations" class="btn-detail">
                查看对话记录
              </button>
              <button @click="viewUserApiUsage" class="btn-detail">
                查看 API 使用
              </button>
              <button @click="viewUserDocuments" class="btn-detail">
                查看文档任务
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import api from '@/services/api';

export default {
  name: 'AdminDashboard',
  
  setup() {
    // 状态
    const stats = ref({
      total_users: 0,
      active_users: 0,
      subscribed_users: 0,
      admin_users: 0,
      free_users: 0
    });
    
    const users = ref([]);
    const selectedUser = ref(null);
    const loading = ref(false);
    const error = ref(null);
    
    // 筛选和分页
    const filters = ref({
      role: '',
      is_active: ''
    });
    
    const currentPage = ref(1);
    const pageSize = ref(20);
    
    // 加载统计数据
    const loadStats = async () => {
      try {
        const response = await api.get('/admin/stats/users');
        stats.value = response.data;
      } catch (err) {
        console.error('加载统计数据失败:', err);
      }
    };
    
    // 加载用户列表
    const loadUsers = async () => {
      loading.value = true;
      error.value = null;
      
      try {
        const params = {
          skip: (currentPage.value - 1) * pageSize.value,
          limit: pageSize.value
        };
        
        if (filters.value.role) {
          params.role = filters.value.role;
        }
        
        if (filters.value.is_active !== '') {
          params.is_active = filters.value.is_active === 'true';
        }
        
        const response = await api.get('/admin/users', { params });
        users.value = response.data;
      } catch (err) {
        error.value = '加载用户列表失败: ' + (err.response?.data?.detail || err.message);
      } finally {
        loading.value = false;
      }
    };
    
    // 切换用户激活状态
    const toggleUserActive = async (user) => {
      const action = user.is_active ? '封禁' : '解封';
      
      if (!confirm(`确定要${action}用户 ${user.username} 吗？`)) {
        return;
      }
      
      try {
        await api.post(`/admin/users/${user.id}/toggle-active`);
        await loadUsers();
        await loadStats();
        alert(`用户已${action}`);
      } catch (err) {
        alert(`${action}失败: ` + (err.response?.data?.detail || err.message));
      }
    };
    
    // 查看用户详情
    const viewUserDetail = async (user) => {
      try {
        const response = await api.get(`/admin/users/${user.id}`);
        selectedUser.value = response.data;
      } catch (err) {
        alert('获取用户详情失败: ' + (err.response?.data?.detail || err.message));
      }
    };
    
    // 关闭模态框
    const closeModal = () => {
      selectedUser.value = null;
    };
    
    // 查看用户对话记录
    const viewUserConversations = () => {
      alert('对话记录功能开发中...');
      // TODO: 实现对话记录查看
    };
    
    // 查看用户 API 使用
    const viewUserApiUsage = () => {
      alert('API 使用记录功能开发中...');
      // TODO: 实现 API 使用记录查看
    };
    
    // 查看用户文档
    const viewUserDocuments = () => {
      alert('文档任务功能开发中...');
      // TODO: 实现文档任务查看
    };
    
    // 分页
    const prevPage = () => {
      if (currentPage.value > 1) {
        currentPage.value--;
        loadUsers();
      }
    };
    
    const nextPage = () => {
      currentPage.value++;
      loadUsers();
    };
    
    // 工具函数
    const getRoleLabel = (role) => {
      const labels = {
        free: '免费用户',
        subscribed: '订阅用户',
        admin: '管理员'
      };
      return labels[role] || role;
    };
    
    const formatDate = (dateString) => {
      const date = new Date(dateString);
      return date.toLocaleString('zh-CN');
    };
    
    // 初始化
    onMounted(() => {
      loadStats();
      loadUsers();
    });
    
    return {
      stats,
      users,
      selectedUser,
      loading,
      error,
      filters,
      currentPage,
      pageSize,
      loadUsers,
      toggleUserActive,
      viewUserDetail,
      closeModal,
      viewUserConversations,
      viewUserApiUsage,
      viewUserDocuments,
      prevPage,
      nextPage,
      getRoleLabel,
      formatDate
    };
  }
};
</script>

<style scoped>
.admin-dashboard {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.admin-header {
  margin-bottom: 2rem;
}

.admin-header h1 {
  font-size: 2rem;
  color: #333;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #666;
  font-size: 1rem;
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-icon {
  font-size: 2.5rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  color: #333;
}

.stat-label {
  color: #666;
  font-size: 0.9rem;
}

/* 用户列表 */
.users-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-header h2 {
  font-size: 1.5rem;
  color: #333;
}

.filters {
  display: flex;
  gap: 1rem;
}

.filter-select {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.btn-refresh {
  padding: 0.5rem 1rem;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

.btn-refresh:hover {
  background: #45a049;
}

/* 表格 */
.users-table-container {
  overflow-x: auto;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
}

.users-table th,
.users-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.users-table th {
  background: #f5f5f5;
  font-weight: 600;
  color: #333;
}

.role-badge,
.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 500;
}

.role-free {
  background: #e3f2fd;
  color: #1976d2;
}

.role-subscribed {
  background: #fff3e0;
  color: #f57c00;
}

.role-admin {
  background: #f3e5f5;
  color: #7b1fa2;
}

.status-badge.active {
  background: #e8f5e9;
  color: #2e7d32;
}

.status-badge.inactive {
  background: #ffebee;
  color: #c62828;
}

.actions {
  display: flex;
  gap: 0.5rem;
}

.btn-action {
  padding: 0.4rem 0.8rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: opacity 0.2s;
}

.btn-action:hover {
  opacity: 0.8;
}

.btn-view {
  background: #2196F3;
  color: white;
}

.btn-ban {
  background: #f44336;
  color: white;
}

.btn-unban {
  background: #4CAF50;
  color: white;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 1.5rem;
}

.btn-page {
  padding: 0.5rem 1rem;
  background: #2196F3;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-page:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.page-info {
  color: #666;
}

/* 模态框 */
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
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.5rem;
}

.btn-close {
  background: none;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  color: #999;
}

.btn-close:hover {
  color: #333;
}

.modal-body {
  padding: 1.5rem;
}

.detail-section {
  margin-bottom: 2rem;
}

.detail-section h4 {
  margin-bottom: 1rem;
  color: #333;
}

.detail-grid {
  display: grid;
  gap: 1rem;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem;
  background: #f5f5f5;
  border-radius: 4px;
}

.detail-label {
  font-weight: 600;
  color: #666;
}

.detail-value {
  color: #333;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.btn-detail {
  padding: 0.75rem 1rem;
  background: #2196F3;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  text-align: left;
}

.btn-detail:hover {
  background: #1976d2;
}

/* 加载和错误状态 */
.loading,
.error {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.error {
  color: #f44336;
}
</style>
