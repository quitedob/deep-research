<template>
  <div v-if="isAuthorized" class="admin-dashboard">
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

    <!-- 内容审核 -->
    <div v-if="currentTab === 'moderation'" class="tab-content">
      <div class="section-header">
        <h2>内容审核</h2>
        <div class="moderation-filters">
          <select v-model="moderationFilter" @change="loadModerationQueue">
            <option value="pending">待审核</option>
            <option value="approved">已批准</option>
            <option value="rejected">已拒绝</option>
            <option value="all">全部</option>
          </select>
          <button
            v-if="selectedModerationItems.length > 0"
            @click="showBatchModal = true"
            class="btn-primary"
          >
            批量审核 ({{ selectedModerationItems.length }})
          </button>
          <button @click="loadModerationQueue" :disabled="moderationLoading" class="btn-secondary">
            🔄 刷新
          </button>
        </div>
      </div>

      <!-- 审核统计卡片 -->
      <div class="moderation-stats">
        <div class="stat-card">
          <div class="stat-icon">⏳</div>
          <div class="stat-content">
            <div class="stat-value">{{ moderationStats.pending }}</div>
            <div class="stat-label">待审核</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">✅</div>
          <div class="stat-content">
            <div class="stat-value">{{ moderationStats.approved }}</div>
            <div class="stat-label">已批准</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">❌</div>
          <div class="stat-content">
            <div class="stat-value">{{ moderationStats.rejected }}</div>
            <div class="stat-label">已拒绝</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">📊</div>
          <div class="stat-content">
            <div class="stat-value">{{ moderationStats.total }}</div>
            <div class="stat-label">总计</div>
          </div>
        </div>
      </div>

      <!-- 审核队列列表 -->
      <div v-if="moderationQueue.length > 0" class="moderation-queue">
        <div class="queue-table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>
                  <input
                    type="checkbox"
                    @change="toggleSelectAll"
                    :checked="allSelected"
                  />
                </th>
                <th>内容类型</th>
                <th>用户</th>
                <th>内容预览</th>
                <th>风险等级</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in moderationQueue"
                :key="item.id"
                :class="{ 'selected': selectedModerationItems.includes(item.id) }"
              >
                <td>
                  <input
                    type="checkbox"
                    :value="item.id"
                    v-model="selectedModerationItems"
                  />
                </td>
                <td>
                  <span :class="['badge', `badge-${item.content_type}`]">
                    {{ getContentTypeLabel(item.content_type) }}
                  </span>
                </td>
                <td>{{ item.user_id }}</td>
                <td class="content-preview">
                  <div class="preview-text">{{ item.content_preview }}</div>
                </td>
                <td>
                  <span :class="['risk-badge', `risk-${item.risk_level}`]">
                    {{ getRiskLevelLabel(item.risk_level) }}
                  </span>
                </td>
                <td>{{ formatDate(item.created_at) }}</td>
                <td>
                  <div class="action-buttons">
                    <button
                      @click="moderateItem(item.id, 'approve')"
                      class="btn-approve"
                      :disabled="moderationLoading"
                    >
                      ✅ 批准
                    </button>
                    <button
                      @click="showRejectModal(item)"
                      class="btn-reject"
                      :disabled="moderationLoading"
                    >
                      ❌ 拒绝
                    </button>
                    <button
                      @click="viewItemDetail(item)"
                      class="btn-view"
                    >
                      👁 查看
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-else class="empty-state">
        <p>暂无审核内容</p>
      </div>

      <!-- 批量审核模态框 -->
      <div v-if="showBatchModal" class="modal-overlay" @click="showBatchModal = false">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3>批量审核</h3>
            <button @click="showBatchModal = false" class="btn-close">×</button>
          </div>
          <div class="modal-body">
            <div class="batch-info">
              <p>已选择 <strong>{{ selectedModerationItems.length }}</strong> 项内容进行批量审核</p>
            </div>
            <div class="form-group">
              <label>审核原因（可选）:</label>
              <textarea
                v-model="batchModerationReason"
                placeholder="请输入审核原因..."
                rows="3"
              ></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button @click="showBatchModal = false" class="btn-secondary">
              取消
            </button>
            <button
              @click="batchApprove"
              class="btn-primary"
              :disabled="moderationLoading"
            >
              {{ moderationLoading ? '审核中...' : '✅ 批准' }}
            </button>
            <button
              @click="batchReject"
              class="btn-danger"
              :disabled="moderationLoading"
            >
              {{ moderationLoading ? '审核中...' : '❌ 拒绝' }}
            </button>
          </div>
        </div>
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

  <!-- 未授权访问状态 -->
  <div v-else class="unauthorized-container">
    <div class="unauthorized-message">
      <h2>🚫 访问被拒绝</h2>
      <p>您没有权限访问管理控制台。</p>
      <p>此功能仅限管理员使用。</p>
      <button @click="goBack" class="btn-back">返回</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { moderationAPI } from '@/services/api.js';

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
        { id: 'moderation', label: '内容审核' },
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
      notification: null,
      // 内容审核相关数据
      moderationQueue: [],
      moderationStats: {
        pending: 0,
        approved: 0,
        rejected: 0,
        total: 0
      },
      moderationFilter: 'pending',
      selectedModerationItems: [],
      batchModerationReason: '',
      showBatchModal: false,
      moderationLoading: false
    };
  },
  computed: {
    isAuthorized() {
      try {
        const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');
        const user = userStr ? JSON.parse(userStr) : null;
        return user?.role === 'admin';
      } catch (error) {
        console.error('[AdminDashboard] 解析用户信息失败:', error);
        return false;
      }
    },

    allSelected() {
      return this.moderationQueue.length > 0 &&
             this.selectedModerationItems.length === this.moderationQueue.length;
    }
  },
  async mounted() {
    // 首先检查权限
    if (!this.isAuthorized) {
      console.warn('[AdminDashboard] 非管理员用户尝试访问管理控制台');
      return;
    }

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
    },

    // 内容审核相关方法
    async loadModerationQueue() {
      this.moderationLoading = true;
      try {
        const status = this.moderationFilter === 'all' ? null : this.moderationFilter;
        const response = await moderationAPI.getModerationQueue(status, 1, 50);
        this.moderationQueue = response.data || [];
      } catch (error) {
        console.error('加载审核队列失败:', error);
        this.showNotification('加载审核队列失败', 'error');
      } finally {
        this.moderationLoading = false;
      }
    },

    async loadModerationStats() {
      try {
        const response = await moderationAPI.getModerationStats();
        this.moderationStats = response.data || {
          pending: 0,
          approved: 0,
          rejected: 0,
          total: 0
        };
      } catch (error) {
        console.error('加载审核统计失败:', error);
      }
    },

    async moderateItem(queueId, action, reason = '') {
      this.moderationLoading = true;
      try {
        await moderationAPI.moderateContent(queueId, action, reason);
        this.showNotification(`内容已${action === 'approve' ? '批准' : '拒绝'}`, 'success');
        await this.loadModerationQueue();
        await this.loadModerationStats();
      } catch (error) {
        console.error('审核内容失败:', error);
        this.showNotification('审核操作失败', 'error');
      } finally {
        this.moderationLoading = false;
      }
    },

    async batchApprove() {
      this.moderationLoading = true;
      try {
        await moderationAPI.batchModerate(
          this.selectedModerationItems,
          'approve',
          this.batchModerationReason
        );
        this.showNotification('批量批准成功', 'success');
        this.showBatchModal = false;
        this.selectedModerationItems = [];
        this.batchModerationReason = '';
        await this.loadModerationQueue();
        await this.loadModerationStats();
      } catch (error) {
        console.error('批量审核失败:', error);
        this.showNotification('批量审核失败', 'error');
      } finally {
        this.moderationLoading = false;
      }
    },

    async batchReject() {
      this.moderationLoading = true;
      try {
        await moderationAPI.batchModerate(
          this.selectedModerationItems,
          'reject',
          this.batchModerationReason
        );
        this.showNotification('批量拒绝成功', 'success');
        this.showBatchModal = false;
        this.selectedModerationItems = [];
        this.batchModerationReason = '';
        await this.loadModerationQueue();
        await this.loadModerationStats();
      } catch (error) {
        console.error('批量审核失败:', error);
        this.showNotification('批量审核失败', 'error');
      } finally {
        this.moderationLoading = false;
      }
    },

    toggleSelectAll(event) {
      if (event.target.checked) {
        this.selectedModerationItems = this.moderationQueue.map(item => item.id);
      } else {
        this.selectedModerationItems = [];
      }
    },

    showRejectModal(item) {
      // TODO: 实现拒绝详情模态框
      const reason = prompt('请输入拒绝原因:');
      if (reason !== null) {
        this.moderateItem(item.id, 'reject', reason);
      }
    },

    viewItemDetail(item) {
      // TODO: 实现内容详情查看
      console.log('View item detail:', item);
    },

    // 内容类型和风险等级标签
    getContentTypeLabel(type) {
      const labels = {
        text: '文本',
        image: '图片',
        conversation: '对话',
        document: '文档'
      };
      return labels[type] || type;
    },

    getRiskLevelLabel(level) {
      const labels = {
        low: '低风险',
        medium: '中风险',
        high: '高风险',
        critical: '严重风险'
      };
      return labels[level] || level;
    },

    goBack() {
      this.$router.push('/home');
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
      } else if (newTab === 'moderation' && this.moderationQueue.length === 0) {
        this.loadModerationQueue();
        this.loadModerationStats();
      } else if (newTab === 'health' && !this.health) {
        this.checkHealth();
      }
    }
  }
};
</script>

<style scoped>
.admin-dashboard {
  padding: var(--spacing-xl);
  max-width: 1400px;
  margin: 0 auto;
  background-color: var(--primary-bg);
  min-height: 100vh;
  font-family: var(--font-family);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.header {
  margin-bottom: var(--spacing-xxl);
  text-align: center;
  padding: var(--spacing-xl);
  background: var(--card-bg);
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
  border-radius: var(--radius-xlarge);
  box-shadow: var(--shadow-elev);
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.header:hover {
  box-shadow: var(--shadow-elev-high);
}

.header h1 {
  font-size: 32px;
  font-weight: 700;
  background: var(--gradient-blue);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: var(--spacing-sm);
  letter-spacing: -0.032em;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 16px;
  font-weight: 500;
  letter-spacing: -0.016em;
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xxl);
}

.stat-card {
  background: var(--card-bg);
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
  border-radius: var(--radius-xlarge);
  padding: var(--spacing-xl);
  box-shadow: var(--shadow-elev);
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  transition: all 0.3s ease;
  border: 1px solid var(--border-color);
  cursor: pointer;
}

.stat-card:hover {
  box-shadow: var(--shadow-elev-high);
  transform: translateY(-2px);
}

.stat-icon {
  font-size: 42px;
  filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.15));
  transition: transform 0.3s ease;
}

.stat-card:hover .stat-icon {
  transform: scale(1.1);
}

.stat-value {
  font-size: 36px;
  font-weight: 800;
  background: var(--gradient-blue);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.032em;
}

.stat-label {
  color: var(--text-secondary);
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.016em;
}

/* 标签页 */
.tabs {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xl);
  border-bottom: 1px solid var(--border-color);
  padding: 0 var(--spacing-sm);
}

.tab {
  padding: var(--spacing-md) var(--spacing-lg);
  border: none;
  background: none;
  cursor: pointer;
  font-size: 15px;
  color: var(--text-secondary);
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: all 0.3s ease;
  border-radius: var(--radius-medium) var(--radius-medium) 0 0;
  font-weight: 500;
  letter-spacing: -0.016em;
}

.tab:hover {
  color: var(--text-primary);
  background: var(--hover-bg);
}

.tab.active {
  color: var(--accent-blue);
  border-bottom-color: var(--accent-blue);
  font-weight: 600;
  background: var(--active-bg);
}

/* 内容区域 */
.tab-content {
  background: var(--card-bg);
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
  border-radius: var(--radius-xlarge);
  padding: var(--spacing-xl);
  box-shadow: var(--shadow-elev);
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.tab-content:hover {
  box-shadow: var(--shadow-elev-high);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
}

.section-header h2 {
  font-size: 22px;
  font-weight: 700;
  background: var(--gradient-blue);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.022em;
}

.filters {
  display: flex;
  gap: var(--spacing-sm);
}

.filters select,
.search-input {
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--input-border);
  border-radius: var(--radius-medium);
  font-size: 14px;
  background: var(--input-bg);
  color: var(--text-primary);
  transition: all 0.2s ease;
  font-family: var(--font-family);
}

.filters select:focus,
.search-input:focus {
  outline: none;
  border-color: var(--input-focus-border);
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
}

/* 表格 */
.table-container {
  overflow-x: auto;
  border-radius: var(--radius-large);
  border: 1px solid var(--border-color);
  background: var(--secondary-bg);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.data-table th {
  background: var(--secondary-bg);
  padding: var(--spacing-md);
  text-align: left;
  font-weight: 600;
  color: var(--text-primary);
  font-size: 13px;
  border-bottom: 1px solid var(--border-color);
  letter-spacing: -0.016em;
}

.data-table td {
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
  font-size: 14px;
  color: var(--text-primary);
  transition: background-color 0.2s ease;
}

.data-table tr:hover td {
  background: var(--hover-bg);
}

.badge {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-large);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: -0.016em;
  border: 1px solid transparent;
}

.badge-free {
  background: var(--accent-blue-light);
  color: var(--accent-blue);
  border-color: var(--accent-blue-border);
}

.badge-subscribed {
  background: var(--accent-green-light);
  color: var(--accent-green);
  border-color: var(--accent-green-border);
}

.badge-admin {
  background: var(--accent-orange-light);
  color: var(--accent-orange);
  border-color: var(--accent-orange-border);
}

.status {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-large);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: -0.016em;
  border: 1px solid transparent;
}

.status.active {
  background: var(--accent-green-light);
  color: var(--accent-green);
  border-color: var(--accent-green-border);
}

.status.inactive {
  background: var(--accent-red-light);
  color: var(--accent-red);
  border-color: var(--accent-red-border);
}

.btn-action {
  padding: var(--spacing-xs) var(--spacing-sm);
  border: none;
  border-radius: var(--radius-medium);
  font-size: 13px;
  cursor: pointer;
  background: var(--accent-blue);
  color: var(--button-text);
  margin-right: var(--spacing-xs);
  transition: all 0.2s ease;
  font-weight: 600;
  letter-spacing: -0.016em;
}

.btn-action:hover {
  background: var(--accent-blue-dark);
  transform: translateY(-1px);
}

.btn-danger {
  background: var(--accent-red);
}

.btn-danger:hover {
  background: var(--accent-red-dark);
  transform: translateY(-1px);
}

.btn-success {
  background: var(--accent-green);
}

.btn-success:hover {
  background: var(--accent-green-dark);
  transform: translateY(-1px);
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--spacing-md);
  margin-top: var(--spacing-xl);
}

.pagination button {
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-medium);
  background: var(--input-bg);
  cursor: pointer;
  font-size: 14px;
  color: var(--text-primary);
  transition: all 0.2s ease;
  font-weight: 500;
}

.pagination button:hover:not(:disabled) {
  background: var(--hover-bg);
  border-color: var(--input-focus-border);
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--secondary-bg);
}

/* 健康状态 */
.health-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: var(--spacing-lg);
}

.health-card {
  background: var(--card-bg);
  border-radius: var(--radius-xlarge);
  padding: var(--spacing-xl);
  border: 1px solid var(--border-color);
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
  box-shadow: var(--shadow-elev);
  transition: all 0.3s ease;
}

.health-card:hover {
  box-shadow: var(--shadow-elev-high);
  transform: translateY(-2px);
}

.health-card h3 {
  font-size: 16px;
  margin-bottom: var(--spacing-sm);
  color: var(--text-primary);
  font-weight: 600;
  letter-spacing: -0.016em;
}

.health-status {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: var(--spacing-sm);
  letter-spacing: -0.016em;
}

.health-status.healthy {
  color: var(--accent-green);
}

.health-status.unhealthy {
  color: var(--accent-red);
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: var(--spacing-xxl);
  color: var(--text-secondary);
  font-size: 16px;
  letter-spacing: -0.016em;
}

/* 通知 */
.notification {
  position: fixed;
  top: var(--spacing-xl);
  right: var(--spacing-xl);
  padding: var(--spacing-md) var(--spacing-lg);
  border-radius: var(--radius-large);
  box-shadow: var(--shadow-elev-high);
  z-index: 1000;
  animation: slideIn 0.3s ease-out;
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
  border: 1px solid var(--border-color);
  font-weight: 500;
  letter-spacing: -0.016em;
}

.notification.success {
  background: var(--accent-green-light);
  color: var(--accent-green);
  border-color: var(--accent-green-border);
}

.notification.error {
  background: var(--accent-red-light);
  color: var(--accent-red);
  border-color: var(--accent-red-border);
}

/* 未授权状态 */
.unauthorized-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
  padding: var(--spacing-xl);
}

.unauthorized-message {
  text-align: center;
  background: var(--card-bg);
  padding: var(--spacing-xxl);
  border-radius: var(--radius-xlarge);
  box-shadow: var(--shadow-elev-high);
  max-width: 400px;
  border: 1px solid var(--border-color);
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
}

.unauthorized-message h2 {
  color: var(--accent-red);
  margin-bottom: var(--spacing-md);
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.024em;
}

.unauthorized-message p {
  color: var(--text-secondary);
  margin-bottom: var(--spacing-sm);
  line-height: 1.5;
  font-size: 16px;
  letter-spacing: -0.016em;
}

.btn-back {
  margin-top: var(--spacing-xl);
  padding: var(--spacing-md) var(--spacing-xl);
  background: var(--accent-blue);
  color: var(--button-text);
  border: none;
  border-radius: var(--radius-large);
  cursor: pointer;
  font-size: 15px;
  transition: all 0.2s ease;
  font-weight: 600;
  letter-spacing: -0.016em;
  box-shadow: 0 2px 8px rgba(0, 122, 255, 0.3);
}

.btn-back:hover {
  background: var(--accent-blue-dark);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 122, 255, 0.4);
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

/* 内容审核相关样式 */
.moderation-filters {
  display: flex;
  gap: 12px;
  align-items: center;
}

.moderation-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.moderation-queue {
  margin-top: 20px;
}

.queue-table-container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.content-preview {
  max-width: 300px;
}

.preview-text {
  font-size: 14px;
  color: #555;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 250px;
}

.risk-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.risk-low {
  background: #d4edda;
  color: #155724;
}

.risk-medium {
  background: #fff3cd;
  color: #856404;
}

.risk-high {
  background: #f8d7da;
  color: #721c24;
}

.risk-critical {
  background: #f5c6cb;
  color: #491217;
}

.action-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-approve,
.btn-reject,
.btn-view {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
  font-weight: 600;
}

.btn-approve {
  background: #28a745;
  color: white;
}

.btn-approve:hover:not(:disabled) {
  background: #218838;
  transform: translateY(-1px);
}

.btn-reject {
  background: #dc3545;
  color: white;
}

.btn-reject:hover:not(:disabled) {
  background: #c82333;
  transform: translateY(-1px);
}

.btn-view {
  background: #6c757d;
  color: white;
}

.btn-view:hover {
  background: #5a6268;
  transform: translateY(-1px);
}

.action-buttons button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.selected {
  background: rgba(102, 126, 234, 0.1);
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
  padding: 0;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
  padding: 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #333;
}

.btn-close {
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

.btn-close:hover {
  color: #666;
}

.modal-body {
  padding: 20px;
}

.batch-info {
  margin-bottom: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #007bff;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #333;
}

.form-group textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  line-height: 1.4;
  resize: vertical;
  font-family: inherit;
}

.modal-footer {
  padding: 20px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn-secondary {
  padding: 10px 20px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: background-color 0.2s;
}

.btn-secondary:hover {
  background: #5a6268;
}

.btn-primary {
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.btn-danger {
  padding: 10px 20px;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-danger:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(239, 68, 68, 0.4);
}

.modal-footer button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}
</style>
