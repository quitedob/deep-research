<template>
  <div class="admin-dashboard">
    <div class="header">
      <h1>管理员控制台</h1>
      <p class="subtitle">系统管理和用户监控</p>
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
        <div class="stat-icon">💎</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.subscribed_users }}</div>
          <div class="stat-label">订阅用户</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">🆓</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.free_users }}</div>
          <div class="stat-label">免费用户</div>
        </div>
      </div>
    </div>

    <!-- 标签页 -->
    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="['tab', { active: currentTab === tab.id }]"
        @click="currentTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 用户管理 -->
    <div v-if="currentTab === 'users'" class="tab-content">
      <div class="section-header">
        <h2>用户管理</h2>
        <div class="filters">
          <select v-model="userFilters.role" @change="loadUsers">
            <option value="">所有角色</option>
            <option value="free">免费用户</option>
            <option value="subscribed">订阅用户</option>
            <option value="admin">管理员</option>
          </select>
          <select v-model="userFilters.is_active" @change="loadUsers">
            <option value="">所有状态</option>
            <option value="true">活跃</option>
            <option value="false">已封禁</option>
          </select>
        </div>
      </div>

      <div class="table-container">
        <table class="data-table">
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
                <span :class="['badge', `badge-${user.role}`]">
                  {{ getRoleLabel(user.role) }}
                </span>
              </td>
              <td>
                <span :class="['status', user.is_active ? 'active' : 'inactive']">
                  {{ user.is_active ? '活跃' : '已封禁' }}
                </span>
              </td>
              <td>{{ formatDate(user.created_at) }}</td>
              <td>
                <button @click="viewUserDetail(user.id)" class="btn-action">
                  查看
                </button>
                <button
                  @click="toggleUserActive(user.id)"
                  :class="['btn-action', user.is_active ? 'btn-danger' : 'btn-success']"
                >
                  {{ user.is_active ? '封禁' : '解封' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pagination">
        <button @click="prevPage" :disabled="currentPage === 1">上一页</button>
        <span>第 {{ currentPage }} 页</span>
        <button @click="nextPage" :disabled="users.length < pageSize">下一页</button>
      </div>
    </div>

    <!-- 对话记录 -->
    <div v-if="currentTab === 'conversations'" class="tab-content">
      <div class="section-header">
        <h2>对话记录</h2>
        <input
          v-model="searchUserId"
          placeholder="输入用户ID搜索"
          @keyup.enter="searchConversations"
          class="search-input"
        />
      </div>

      <div v-if="conversations.length > 0" class="conversations-list">
        <div v-for="conv in conversations" :key="conv.id" class="conversation-item">
          <div class="conv-header">
            <h3>{{ conv.title || '未命名对话' }}</h3>
            <span class="conv-meta">{{ conv.message_count }} 条消息</span>
          </div>
          <div class="conv-info">
            <span>用户: {{ conv.user_id }}</span>
            <span>更新: {{ formatDate(conv.updated_at) }}</span>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">
        <p>暂无对话记录</p>
      </div>
    </div>

    <!-- 研究报告 -->
    <div v-if="currentTab === 'reports'" class="tab-content">
      <div class="section-header">
        <h2>研究报告</h2>
      </div>

      <div v-if="reports.length > 0" class="reports-list">
        <div v-for="report in reports" :key="report.document_id" class="report-item">
          <div class="report-header">
            <h3>文档 ID: {{ report.document_id }}</h3>
            <span class="report-meta">{{ report.total_chunks }} 个块</span>
          </div>
          <div class="report-preview">
            {{ report.chunks[0]?.content || '无内容' }}
          </div>
          <div class="report-footer">
            <span>创建时间: {{ formatDate(report.created_at) }}</span>
            <button @click="viewReportDetail(report.document_id)" class="btn-action">
              查看详情
            </button>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">
        <p>暂无研究报告</p>
      </div>
    </div>

    <!-- 订阅管理 -->
    <div v-if="currentTab === 'subscriptions'" class="tab-content">
      <div class="section-header">
        <h2>订阅管理</h2>
        <select v-model="subscriptionFilter" @change="loadSubscriptions">
          <option value="">所有状态</option>
          <option value="active">活跃</option>
          <option value="canceled">已取消</option>
          <option value="past_due">逾期</option>
        </select>
      </div>

      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>用户名</th>
              <th>订阅ID</th>
              <th>状态</th>
              <th>开始时间</th>
              <th>结束时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="sub in subscriptions" :key="sub.id">
              <td>{{ sub.username }}</td>
              <td>{{ sub.stripe_subscription_id }}</td>
              <td>
                <span :class="['badge', `badge-${sub.status}`]">
                  {{ sub.status }}
                </span>
              </td>
              <td>{{ formatDate(sub.current_period_start) }}</td>
              <td>{{ formatDate(sub.current_period_end) }}</td>
              <td>
                <button @click="updateSubscription(sub.id)" class="btn-action">
                  管理
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 系统健康 -->
    <div v-if="currentTab === 'health'" class="tab-content">
      <div class="section-header">
        <h2>系统健康状态</h2>
        <button @click="checkHealth" class="btn-refresh">刷新</button>
      </div>

      <div v-if="health" class="health-grid">
        <div class="health-card">
          <h3>数据库</h3>
          <div :class="['health-status', health.components.database.healthy ? 'healthy' : 'unhealthy']">
            {{ health.components.database.healthy ? '✅ 健康' : '❌ 异常' }}
          </div>
          <p>{{ health.components.database.message }}</p>
        </div>

        <div class="health-card">
          <h3>LLM 服务</h3>
          <div :class="['health-status', !health.components.llm.error ? 'healthy' : 'unhealthy']">
            {{ !health.components.llm.error ? '✅ 健康' : '❌ 异常' }}
          </div>
          <p v-if="health.components.llm.error">{{ health.components.llm.error }}</p>
        </div>

        <div class="health-card">
          <h3>OCR 服务</h3>
          <div :class="['health-status', health.components.ocr.available ? 'healthy' : 'unhealthy']">
            {{ health.components.ocr.available ? '✅ 可用' : '❌ 不可用' }}
          </div>
          <p>提供商: {{ health.components.ocr.provider || 'N/A' }}</p>
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
  name: 'AdminDashboard',
  data() {
    return {
      currentTab: 'users',
      tabs: [
        { id: 'users', label: '用户管理' },
        { id: 'conversations', label: '对话记录' },
        { id: 'reports', label: '研究报告' },
        { id: 'subscriptions', label: '订阅管理' },
        { id: 'health', label: '系统健康' }
      ],
      stats: {
        total_users: 0,
        active_users: 0,
        subscribed_users: 0,
        free_users: 0
      },
      users: [],
      conversations: [],
      reports: [],
      subscriptions: [],
      health: null,
      userFilters: {
        role: '',
        is_active: ''
      },
      subscriptionFilter: '',
      searchUserId: '',
      currentPage: 1,
      pageSize: 50,
      notification: null
    };
  },
  async mounted() {
    await this.loadStats();
    await this.loadUsers();
  },
  methods: {
    async loadStats() {
      try {
        const response = await axios.get('/api/admin/stats/users');
        this.stats = response.data;
      } catch (error) {
        this.showNotification('加载统计数据失败', 'error');
      }
    },
    
    async loadUsers() {
      try {
        const params = {
          skip: (this.currentPage - 1) * this.pageSize,
          limit: this.pageSize
        };
        
        if (this.userFilters.role) params.role = this.userFilters.role;
        if (this.userFilters.is_active) params.is_active = this.userFilters.is_active === 'true';
        
        const response = await axios.get('/api/admin/users', { params });
        this.users = response.data;
      } catch (error) {
        this.showNotification('加载用户列表失败', 'error');
      }
    },
    
    async toggleUserActive(userId) {
      if (!confirm('确定要切换用户状态吗？')) return;
      
      try {
        await axios.post(`/api/admin/users/${userId}/toggle-active`);
        this.showNotification('用户状态已更新', 'success');
        await this.loadUsers();
      } catch (error) {
        this.showNotification('操作失败: ' + error.message, 'error');
      }
    },
    
    async searchConversations() {
      if (!this.searchUserId) {
        this.showNotification('请输入用户ID', 'error');
        return;
      }
      
      try {
        const response = await axios.get(`/api/admin/users/${this.searchUserId}/conversations`);
        this.conversations = response.data.sessions;
      } catch (error) {
        this.showNotification('加载对话记录失败', 'error');
      }
    },
    
    async loadReports() {
      try {
        const response = await axios.get('/api/admin/research-reports');
        this.reports = response.data.documents;
      } catch (error) {
        this.showNotification('加载研究报告失败', 'error');
      }
    },
    
    async loadSubscriptions() {
      try {
        const params = {};
        if (this.subscriptionFilter) params.status = this.subscriptionFilter;
        
        const response = await axios.get('/api/admin/subscriptions', { params });
        this.subscriptions = response.data.subscriptions;
      } catch (error) {
        this.showNotification('加载订阅记录失败', 'error');
      }
    },
    
    async checkHealth() {
      try {
        const response = await axios.get('/api/admin/health');
        this.health = response.data;
      } catch (error) {
        this.showNotification('健康检查失败', 'error');
      }
    },
    
    viewUserDetail(userId) {
      // TODO: 实现用户详情查看
      console.log('View user:', userId);
    },
    
    viewReportDetail(documentId) {
      // TODO: 实现报告详情查看
      console.log('View report:', documentId);
    },
    
    updateSubscription(subscriptionId) {
      // TODO: 实现订阅管理
      console.log('Update subscription:', subscriptionId);
    },
    
    getRoleLabel(role) {
      const labels = {
        free: '免费',
        subscribed: '订阅',
        admin: '管理员'
      };
      return labels[role] || role;
    },
    
    formatDate(date) {
      if (!date) return '-';
      return new Date(date).toLocaleString('zh-CN');
    },
    
    prevPage() {
      if (this.currentPage > 1) {
        this.currentPage--;
        this.loadUsers();
      }
    },
    
    nextPage() {
      this.currentPage++;
      this.loadUsers();
    },
    
    showNotification(message, type = 'info') {
      this.notification = { message, type };
      setTimeout(() => {
        this.notification = null;
      }, 3000);
    }
  },
  watch: {
    currentTab(newTab) {
      if (newTab === 'conversations' && this.conversations.length === 0) {
        // 不自动加载，等待用户搜索
      } else if (newTab === 'reports' && this.reports.length === 0) {
        this.loadReports();
      } else if (newTab === 'subscriptions' && this.subscriptions.length === 0) {
        this.loadSubscriptions();
      } else if (newTab === 'health' && !this.health) {
        this.checkHealth();
      }
    }
  }
};
</script>

<style scoped>
.admin-dashboard {
  padding: 20px;
  max-width: 1400px;
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

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  font-size: 36px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  color: #666;
  font-size: 14px;
}

/* 标签页 */
.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  border-bottom: 2px solid #eee;
}

.tab {
  padding: 12px 24px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.2s;
}

.tab:hover {
  color: #333;
}

.tab.active {
  color: #007bff;
  border-bottom-color: #007bff;
  font-weight: 500;
}

/* 内容区域 */
.tab-content {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h2 {
  font-size: 20px;
  color: #333;
}

.filters {
  display: flex;
  gap: 10px;
}

.filters select,
.search-input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

/* 表格 */
.table-container {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  background: #f8f9fa;
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #555;
  font-size: 13px;
  border-bottom: 2px solid #dee2e6;
}

.data-table td {
  padding: 12px;
  border-bottom: 1px solid #eee;
  font-size: 14px;
}

.badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.badge-free {
  background: #e7f3ff;
  color: #0066cc;
}

.badge-subscribed {
  background: #d4edda;
  color: #155724;
}

.badge-admin {
  background: #fff3cd;
  color: #856404;
}

.status {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status.active {
  background: #d4edda;
  color: #155724;
}

.status.inactive {
  background: #f8d7da;
  color: #721c24;
}

.btn-action {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  background: #007bff;
  color: white;
  margin-right: 5px;
  transition: all 0.2s;
}

.btn-action:hover {
  background: #0056b3;
}

.btn-danger {
  background: #dc3545;
}

.btn-danger:hover {
  background: #c82333;
}

.btn-success {
  background: #28a745;
}

.btn-success:hover {
  background: #218838;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  margin-top: 20px;
}

.pagination button {
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 14px;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 健康状态 */
.health-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.health-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
}

.health-card h3 {
  font-size: 16px;
  margin-bottom: 10px;
  color: #333;
}

.health-status {
  font-size: 18px;
  font-weight: 500;
  margin-bottom: 10px;
}

.health-status.healthy {
  color: #28a745;
}

.health-status.unhealthy {
  color: #dc3545;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 40px;
  color: #666;
}

/* 通知 */
.notification {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 15px 20px;
  border-radius: 4px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  z-index: 1000;
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
