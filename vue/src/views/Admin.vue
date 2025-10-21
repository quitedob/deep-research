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

    <!-- 标签页导航 -->
    <div class="tabs-navigation">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-button', { 'active': activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
        <span v-if="tab.badge" class="tab-badge">{{ tab.badge }}</span>
      </button>
    </div>

    <!-- 审计日志部分 -->
    <div v-if="activeTab === 'audit'" class="audit-section">
      <div class="section-header">
        <h2>审计日志</h2>
        <div class="audit-filters">
          <select v-model="auditFilters.action" @change="loadAuditLogs" class="filter-select">
            <option value="">所有操作</option>
            <option value="USER_BAN">用户封禁</option>
            <option value="USER_UNBAN">用户解封</option>
            <option value="USER_UPDATE">用户更新</option>
            <option value="USER_VIEW">查看用户</option>
            <option value="SYSTEM_HEALTH_CHECK">系统检查</option>
          </select>

          <select v-model="auditFilters.status" @change="loadAuditLogs" class="filter-select">
            <option value="">所有状态</option>
            <option value="success">成功</option>
            <option value="failed">失败</option>
          </select>

          <button @click="loadAuditLogs" class="btn-refresh">🔄 刷新</button>
        </div>
      </div>

      <div v-if="auditLoading" class="loading">加载中...</div>

      <div v-else-if="auditError" class="error">{{ auditError }}</div>

      <div v-else class="audit-table-container">
        <table class="audit-table">
          <thead>
            <tr>
              <th>时间</th>
              <th>管理员</th>
              <th>操作</th>
              <th>目标用户</th>
              <th>状态</th>
              <th>IP地址</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in auditLogs" :key="log.id">
              <td>{{ formatDate(log.timestamp) }}</td>
              <td>{{ log.admin_username || '-' }}</td>
              <td>
                <span :class="['action-badge', getActionClass(log.action)]">
                  {{ getActionLabel(log.action) }}
                </span>
              </td>
              <td>{{ log.target_username || '-' }}</td>
              <td>
                <span :class="['status-badge', log.status]">
                  {{ getStatusLabel(log.status) }}
                </span>
              </td>
              <td>{{ log.ip_address || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 审计日志分页 -->
      <div class="pagination">
        <button
          @click="prevAuditPage"
          :disabled="auditPage === 1"
          class="btn-page"
        >
          上一页
        </button>
        <span class="page-info">第 {{ auditPage }} 页</span>
        <button
          @click="nextAuditPage"
          :disabled="auditLogs.length < auditPageSize"
          class="btn-page"
        >
          下一页
        </button>
      </div>
    </div>

    <!-- 内容审核部分 -->
    <div v-if="activeTab === 'moderation'" class="moderation-section">
      <div class="section-header">
        <h2>内容审核</h2>
        <div class="moderation-filters">
          <select v-model="moderationFilters.status" @change="loadModerationQueue" class="filter-select">
            <option value="">所有状态</option>
            <option value="pending">待处理</option>
            <option value="reviewing">审核中</option>
            <option value="resolved">已处理</option>
            <option value="dismissed">已驳回</option>
          </select>

          <select v-model="moderationFilters.priority" @change="loadModerationQueue" class="filter-select">
            <option value="">所有优先级</option>
            <option value="urgent">紧急</option>
            <option value="high">高</option>
            <option value="medium">中</option>
            <option value="low">低</option>
          </select>

          <select v-model="moderationFilters.reason" @change="loadModerationQueue" class="filter-select">
            <option value="">所有原因</option>
            <option value="spam">垃圾信息</option>
            <option value="harassment">骚扰欺凌</option>
            <option value="violence">暴力威胁</option>
            <option value="inappropriate_content">不当内容</option>
            <option value="misinformation">虚假信息</option>
            <option value="other">其他</option>
          </select>

          <button @click="loadModerationQueue" class="btn-refresh">🔄 刷新</button>
        </div>
      </div>

      <!-- 审核统计 -->
      <div class="moderation-stats">
        <div class="stat-card small">
          <div class="stat-value">{{ moderationStats.total_reports }}</div>
          <div class="stat-label">总举报数</div>
        </div>
        <div class="stat-card small pending">
          <div class="stat-value">{{ moderationStats.pending_reports }}</div>
          <div class="stat-label">待处理</div>
        </div>
        <div class="stat-card small resolved">
          <div class="stat-value">{{ moderationStats.resolved_reports }}</div>
          <div class="stat-label">已处理</div>
        </div>
        <div class="stat-card small dismissed">
          <div class="stat-value">{{ moderationStats.dismissed_reports }}</div>
          <div class="stat-label">已驳回</div>
        </div>
      </div>

      <div v-if="moderationLoading" class="loading">加载中...</div>

      <div v-else-if="moderationError" class="error">{{ moderationError }}</div>

      <div v-else class="moderation-list">
        <div v-for="report in moderationReports" :key="report.id" class="report-item">
          <div class="report-header">
            <div class="report-meta">
              <span :class="['priority-badge', report.priority]">
                {{ getPriorityLabel(report.priority) }}
              </span>
              <span :class="['status-badge', report.status]">
                {{ getModerationStatusLabel(report.status) }}
              </span>
              <span class="report-reason">
                {{ getReasonLabel(report.report_reason) }}
              </span>
            </div>
            <div class="report-time">
              {{ formatDate(report.created_at) }}
            </div>
          </div>

          <div class="report-content">
            <div class="reported-message">
              <strong>举报内容:</strong>
              <div class="message-preview">
                {{ report.message_content ? report.message_content.substring(0, 200) + '...' : '内容已删除' }}
              </div>
            </div>

            <div class="report-details">
              <p><strong>举报人:</strong> {{ report.reporter_username }}</p>
              <p v-if="report.reported_username"><strong>被举报人:</strong> {{ report.reported_username }}</p>
              <p v-if="report.report_description"><strong>详细描述:</strong> {{ report.report_description }}</p>
              <p v-if="report.session_title"><strong>对话:</strong> {{ report.session_title }}</p>
            </div>
          </div>

          <div class="report-actions" v-if="report.status === 'pending' || report.status === 'reviewing'">
            <button @click="startReview(report)" class="btn-action btn-review">
              开始审核
            </button>
          </div>

          <div class="review-info" v-else-if="report.status === 'resolved' || report.status === 'dismissed'">
            <p><strong>审核结果:</strong> {{ getModerationActionLabel(report.action_taken) }}</p>
            <p v-if="report.review_notes"><strong>审核备注:</strong> {{ report.review_notes }}</p>
            <p><strong>审核人:</strong> {{ report.reviewer_admin_username }}</p>
            <p><strong>审核时间:</strong> {{ formatDate(report.reviewed_at) }}</p>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination">
        <button
          @click="prevModerationPage"
          :disabled="moderationPage === 1"
          class="btn-page"
        >
          上一页
        </button>
        <span class="page-info">第 {{ moderationPage }} 页</span>
        <button
          @click="nextModerationPage"
          :disabled="moderationReports.length < moderationPageSize"
          class="btn-page"
        >
          下一页
        </button>
      </div>
    </div>

    <!-- 审核模态框 -->
    <div v-if="reviewModal.show" class="modal-overlay" @click="closeReviewModal">
      <div class="modal-content large" @click.stop>
        <div class="modal-header">
          <h3>内容审核</h3>
          <button @click="closeReviewModal" class="btn-close">×</button>
        </div>

        <div class="modal-body">
          <div class="review-section">
            <h4>举报信息</h4>
            <div class="review-details">
              <p><strong>举报原因:</strong> {{ getReasonLabel(reviewModal.report?.report_reason) }}</p>
              <p><strong>举报人:</strong> {{ reviewModal.report?.reporter_username }}</p>
              <p><strong>举报时间:</strong> {{ formatDate(reviewModal.report?.created_at) }}</p>
              <p v-if="reviewModal.report?.report_description"><strong>详细描述:</strong></p>
              <div v-if="reviewModal.report?.report_description" class="description-text">
                {{ reviewModal.report.report_description }}
              </div>
            </div>
          </div>

          <div class="review-section">
            <h4>被举报内容</h4>
            <div class="content-box">
              {{ reviewModal.report?.message_content || '内容已删除' }}
            </div>
          </div>

          <div class="review-section">
            <h4>审核操作</h4>
            <div class="action-form">
              <div class="form-group">
                <label>处理措施:</label>
                <select v-model="reviewForm.action" class="form-select">
                  <option value="">请选择处理措施</option>
                  <option value="dismiss">驳回举报</option>
                  <option value="warning">警告用户</option>
                  <option value="message_deleted">删除消息</option>
                  <option value="user_suspended">暂停用户</option>
                  <option value="user_banned">封禁用户</option>
                </select>
              </div>

              <div class="form-group">
                <label>审核备注:</label>
                <textarea
                  v-model="reviewForm.notes"
                  class="form-textarea"
                  rows="3"
                  placeholder="请输入审核备注..."
                ></textarea>
              </div>

              <div class="form-group">
                <label>优先级调整:</label>
                <select v-model="reviewForm.priority" class="form-select">
                  <option value="">保持原优先级</option>
                  <option value="urgent">紧急</option>
                  <option value="high">高</option>
                  <option value="medium">中</option>
                  <option value="low">低</option>
                </select>
              </div>
            </div>
          </div>

          <div class="modal-actions">
            <button @click="closeReviewModal" class="btn-cancel">取消</button>
            <button
              @click="submitReview"
              :disabled="!reviewForm.action || reviewSubmitting"
              class="btn-submit"
            >
              {{ reviewSubmitting ? '提交中...' : '提交审核' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 系统监控部分 -->
    <div v-if="activeTab === 'monitoring'" class="monitoring-section">
      <!-- 健康状态概览 -->
      <div class="monitoring-subsection">
        <div class="section-header">
          <h2>系统健康状态</h2>
          <button @click="loadSystemHealth" class="btn-refresh">🔄 刷新</button>
        </div>

        <div class="health-overview">
          <div class="overall-status">
            <div :class="['status-indicator', getHealthStatusClass(systemHealth.overall_status)]">
              <div class="status-dot"></div>
              <span class="status-text">{{ systemHealth.overall_status === 'healthy' ? '健康' : systemHealth.overall_status === 'warning' ? '警告' : '严重' }}</span>
            </div>
            <p class="status-time">更新时间: {{ formatDate(systemHealth.timestamp) }}</p>
          </div>

          <div class="alerts-section" v-if="systemHealth.alerts.length > 0">
            <h3>系统告警</h3>
            <div v-for="alert in systemHealth.alerts" :key="alert.timestamp" :class="['alert-item', alert.level]">
              <strong>{{ alert.component }}:</strong> {{ alert.message }}
              <span class="alert-time">{{ formatDate(alert.timestamp) }}</span>
            </div>
          </div>

          <div class="components-grid">
            <div v-for="(status, component) in systemHealth.components" :key="component" :class="['component-card', getHealthStatusClass(status.status)]">
              <div class="component-header">
                <span class="component-name">{{ getComponentDisplayName(component) }}</span>
                <span class="component-status">{{ status.status }}</span>
              </div>
              <p class="component-message">{{ status.message }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 成本分析 -->
      <div class="monitoring-subsection">
        <div class="section-header">
          <h2>成本分析</h2>
          <select v-model="costAnalysis.period_hours" @change="loadCostAnalysis(costAnalysis.period_hours)" class="filter-select">
            <option :value="24">最近24小时</option>
            <option :value="72">最近3天</option>
            <option :value="168">最近7天</option>
          </select>
          <button @click="loadCostAnalysis(costAnalysis.period_hours)" class="btn-refresh">🔄 刷新</button>
        </div>

        <div class="cost-overview">
          <div class="cost-summary">
            <div class="cost-card">
              <h3>总成本</h3>
              <div class="cost-value">{{ formatCurrency(costAnalysis.total_cost) }}</div>
            </div>
            <div class="cost-card">
              <h3>总Token数</h3>
              <div class="cost-value">{{ formatNumber(costAnalysis.total_tokens) }}</div>
            </div>
            <div class="cost-card">
              <h3>总请求数</h3>
              <div class="cost-value">{{ formatNumber(costAnalysis.total_requests) }}</div>
            </div>
          </div>

          <div class="cost-charts">
            <div class="chart-section">
              <h3>按提供商分布</h3>
              <div class="provider-costs">
                <div v-for="(cost, provider) in costAnalysis.cost_by_provider" :key="provider" class="provider-cost">
                  <span class="provider-name">{{ provider }}</span>
                  <span class="provider-cost-value">{{ formatCurrency(cost) }}</span>
                  <div class="cost-bar">
                    <div class="cost-fill" :style="{ width: `${(cost / Math.max(...Object.values(costAnalysis.cost_by_provider))) * 100}%` }"></div>
                  </div>
                </div>
              </div>
            </div>

            <div class="chart-section">
              <h3>每日成本趋势</h3>
              <div class="daily-cost-chart">
                <div v-for="day in costAnalysis.daily_costs" :key="day.date" class="daily-cost-item">
                  <span class="date-label">{{ formatDate(day.date) }}</span>
                  <span class="cost-amount">{{ formatCurrency(day.cost) }}</span>
                  <div class="cost-bar">
                    <div class="cost-fill" :style="{ width: `${(day.cost / Math.max(...costAnalysis.daily_costs.map(d => d.cost))) * 100}%` }"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 使用指标 -->
      <div class="monitoring-subsection">
        <div class="section-header">
          <h2>使用指标</h2>
          <select v-model="usageMetrics.period_hours" @change="loadUsageMetrics(usageMetrics.period_hours)" class="filter-select">
            <option :value="24">最近24小时</option>
            <option :value="72">最近3天</option>
            <option :value="168">最近7天</option>
          </select>
          <button @click="loadUsageMetrics(usageMetrics.period_hours)" class="btn-refresh">🔄 刷新</button>
        </div>

        <div class="usage-overview">
          <div class="usage-stats">
            <div class="usage-card">
              <h3>活跃用户</h3>
              <div class="usage-value">{{ formatNumber(usageMetrics.active_users) }}</div>
            </div>
            <div class="usage-card">
              <h3>总请求数</h3>
              <div class="usage-value">{{ formatNumber(usageMetrics.total_requests) }}</div>
            </div>
            <div class="usage-card">
              <h3>平均响应时间</h3>
              <div class="usage-value">{{ (usageMetrics.avg_response_time / 1000).toFixed(2) }}s</div>
            </div>
            <div class="usage-card">
              <h3>成功率</h3>
              <div class="usage-value">{{ usageMetrics.success_rate.toFixed(1) }}%</div>
            </div>
          </div>

          <div class="top-models">
            <h3>热门模型</h3>
            <div class="model-list">
              <div v-for="model in usageMetrics.top_models" :key="model.model" class="model-item">
                <span class="model-name">{{ model.model }}</span>
                <span class="model-usage">{{ formatNumber(model.usage_count) }} 次</span>
                <span class="model-response-time">{{ (model.avg_response_time / 1000).toFixed(2) }}s</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 性能指标 -->
      <div class="monitoring-subsection">
        <div class="section-header">
          <h2>性能指标</h2>
          <select v-model="performanceMetrics.period_hours" @change="loadPerformanceMetrics(performanceMetrics.period_hours)" class="filter-select">
            <option :value="24">最近24小时</option>
            <option :value="72">最近3天</option>
            <option :value="168">最近7天</option>
          </select>
          <button @click="loadPerformanceMetrics(performanceMetrics.period_hours)" class="btn-refresh">🔄 刷新</button>
        </div>

        <div class="performance-overview">
          <div class="system-resources">
            <h3>系统资源</h3>
            <div v-if="performanceMetrics.system_resources.cpu" class="resource-item">
              <span class="resource-name">CPU</span>
              <div class="resource-bar">
                <div class="resource-fill cpu" :style="{ width: `${performanceMetrics.system_resources.cpu.usage_percent}%` }"></div>
              </div>
              <span class="resource-value">{{ performanceMetrics.system_resources.cpu.usage_percent.toFixed(1) }}%</span>
            </div>
            <div v-if="performanceMetrics.system_resources.memory" class="resource-item">
              <span class="resource-name">内存</span>
              <div class="resource-bar">
                <div class="resource-fill memory" :style="{ width: `${performanceMetrics.system_resources.memory.usage_percent}%` }"></div>
              </div>
              <span class="resource-value">{{ performanceMetrics.system_resources.memory.usage_percent.toFixed(1) }}%</span>
              <span class="resource-detail">{{ formatBytes(performanceMetrics.system_resources.memory.available_gb * 1024**3) }} 可用</span>
            </div>
            <div v-if="performanceMetrics.system_resources.disk" class="resource-item">
              <span class="resource-name">磁盘</span>
              <div class="resource-bar">
                <div class="resource-fill disk" :style="{ width: `${performanceMetrics.system_resources.disk.usage_percent}%` }"></div>
              </div>
              <span class="resource-value">{{ performanceMetrics.system_resources.disk.usage_percent.toFixed(1) }}%</span>
              <span class="resource-detail">{{ formatBytes(performanceMetrics.system_resources.disk.free_gb * 1024**3) }} 可用</span>
            </div>
          </div>

          <div class="bottlenecks" v-if="performanceMetrics.bottlenecks.length > 0">
            <h3>系统瓶颈</h3>
            <div v-for="bottleneck in performanceMetrics.bottlenecks" :key="bottleneck.type" :class="['bottleneck-item', bottleneck.severity]">
              <strong>{{ bottleneck.type }}:</strong> {{ bottleneck.description }}
              <p class="bottleneck-recommendation">建议: {{ bottleneck.recommendation }}</p>
            </div>
          </div>
        </div>
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
import { ref, onMounted, onUnmounted } from 'vue';
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

    // 审计日志状态
    const auditLogs = ref([]);
    const auditLoading = ref(false);
    const auditError = ref(null);
    const auditFilters = ref({
      action: '',
      status: ''
    });
    const auditPage = ref(1);
    const auditPageSize = ref(20);

    // 内容审核状态
    const activeTab = ref('audit'); // 默认显示审计日志标签页
    const moderationReports = ref([]);
    const moderationStats = ref({
      total_reports: 0,
      pending_reports: 0,
      resolved_reports: 0,
      dismissed_reports: 0,
      reports_by_reason: {},
      reports_by_priority: {}
    });
    const moderationLoading = ref(false);
    const moderationError = ref(null);
    const moderationFilters = ref({
      status: '',
      priority: '',
      reason: ''
    });
    const moderationPage = ref(1);
    const moderationPageSize = ref(20);

    // 审核模态框状态
    const reviewModal = ref({
      show: false,
      report: null
    });
    const reviewForm = ref({
      action: '',
      notes: '',
      priority: ''
    });
    const reviewSubmitting = ref(false);

    // 系统监控状态
    const systemHealth = ref({
      overall_status: 'healthy',
      components: {},
      system_metrics: {},
      alerts: []
    });
    const costAnalysis = ref({
      period_hours: 24,
      total_cost: 0,
      total_tokens: 0,
      total_requests: 0,
      cost_by_provider: {},
      cost_by_model: {},
      daily_costs: []
    });
    const usageMetrics = ref({
      period_hours: 24,
      active_users: 0,
      total_requests: 0,
      avg_response_time: 0,
      success_rate: 0,
      top_models: []
    });
    const performanceMetrics = ref({
      system_resources: {},
      response_times: {},
      error_rates: {},
      bottlenecks: []
    });

    const monitoringLoading = ref(false);
    const monitoringError = ref(null);
    const isMounted = ref(false);

    // 标签页配置
    const tabs = ref([
      { key: 'audit', label: '审计日志' },
      { key: 'moderation', label: '内容审核', badge: null }, // 将在加载统计数据后更新
      { key: 'monitoring', label: '系统监控', badge: null }
    ]);
    
    // 加载统计数据
    const loadStats = async () => {
      try {
        const response = await api.get('/admin/stats/users');
        if (isMounted.value) {
          stats.value = response.data;
        }
      } catch (err) {
        if (isMounted.value) {
          console.error('加载统计数据失败:', err);
        }
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

      if (!window.confirm(`确定要${action}用户 ${user.username} 吗？`)) {
        return;
      }

      try {
        await api.post(`/admin/users/${user.id}/toggle-active`);
        await loadUsers();
        await loadStats();
        window.alert(`用户已${action}`);
      } catch (err) {
        window.alert(`${action}失败: ` + (err.response?.data?.detail || err.message));
      }
    };
    
    // 查看用户详情
    const viewUserDetail = async (user) => {
      try {
        const response = await api.get(`/admin/users/${user.id}`);
        selectedUser.value = response.data;
      } catch (err) {
        window.alert('获取用户详情失败: ' + (err.response?.data?.detail || err.message));
      }
    };
    
    // 关闭模态框
    const closeModal = () => {
      selectedUser.value = null;
    };
    
    // 查看用户对话记录
    const viewUserConversations = () => {
      window.alert('对话记录功能开发中...');
      // TODO: 实现对话记录查看
    };

    // 查看用户 API 使用
    const viewUserApiUsage = () => {
      window.alert('API 使用记录功能开发中...');
      // TODO: 实现 API 使用记录查看
    };

    // 查看用户文档
    const viewUserDocuments = () => {
      window.alert('文档任务功能开发中...');
      // TODO: 实现文档任务查看
    };

    // 加载审计日志
    const loadAuditLogs = async () => {
      auditLoading.value = true;
      auditError.value = null;

      try {
        const params = {
          page: auditPage.value,
          page_size: auditPageSize.value
        };

        if (auditFilters.value.action) {
          params.action = auditFilters.value.action;
        }

        if (auditFilters.value.status) {
          params.status = auditFilters.value.status;
        }

        const response = await api.get('/admin/audit-logs', { params });
        auditLogs.value = response.data.logs;
      } catch (err) {
        auditError.value = '加载审计日志失败: ' + (err.response?.data?.detail || err.message);
      } finally {
        auditLoading.value = false;
      }
    };

    // 审计日志分页
    const prevAuditPage = () => {
      if (auditPage.value > 1) {
        auditPage.value--;
        loadAuditLogs();
      }
    };

    const nextAuditPage = () => {
      auditPage.value++;
      loadAuditLogs();
    };

    // 审计日志工具函数
    const getActionLabel = (action) => {
      const labels = {
        'USER_BAN': '用户封禁',
        'USER_UNBAN': '用户解封',
        'USER_UPDATE': '用户更新',
        'USER_VIEW': '查看用户',
        'SYSTEM_HEALTH_CHECK': '系统检查',
        'SUBSCRIPTION_UPDATE': '订阅更新',
        'VIEW_REPORTS': '查看报告',
        'EXPORT_DATA': '导出数据',
        'CONTENT_MODERATION': '内容审核'
      };
      return labels[action] || action;
    };

    const getActionClass = (action) => {
      if (action.includes('BAN')) return 'danger';
      if (action.includes('UNBAN')) return 'success';
      if (action.includes('UPDATE')) return 'warning';
      if (action.includes('VIEW')) return 'info';
      return 'default';
    };

    const getStatusLabel = (status) => {
      const labels = {
        'success': '成功',
        'failed': '失败',
        'partial': '部分成功'
      };
      return labels[status] || status;
    };

    // 内容审核相关方法
    const loadModerationQueue = async () => {
      moderationLoading.value = true;
      moderationError.value = null;

      try {
        const params = {
          limit: moderationPageSize.value,
          offset: (moderationPage.value - 1) * moderationPageSize.value
        };

        if (moderationFilters.value.status) {
          params.status = moderationFilters.value.status;
        }
        if (moderationFilters.value.priority) {
          params.priority = moderationFilters.value.priority;
        }
        if (moderationFilters.value.reason) {
          params.reason = moderationFilters.value.reason;
        }

        const response = await api.get('/api/moderation/admin/queue', { params });
        moderationReports.value = response.data;
      } catch (err) {
        moderationError.value = '加载审核队列失败: ' + (err.response?.data?.detail || err.message);
      } finally {
        moderationLoading.value = false;
      }
    };

    const loadModerationStats = async () => {
      try {
        const response = await api.get('/api/moderation/admin/stats');
        moderationStats.value = response.data;

        // 更新标签页徽章显示待处理数量
        const moderationTab = tabs.value.find(tab => tab.key === 'moderation');
        if (moderationTab && response.data.pending_reports > 0) {
          moderationTab.badge = response.data.pending_reports;
        }
      } catch (err) {
        console.error('加载审核统计失败:', err);
      }
    };

    const startReview = (report) => {
      reviewModal.value = {
        show: true,
        report: report
      };
      reviewForm.value = {
        action: '',
        notes: '',
        priority: ''
      };
    };

    const closeReviewModal = () => {
      reviewModal.value = {
        show: false,
        report: null
      };
      reviewForm.value = {
        action: '',
        notes: '',
        priority: ''
      };
    };

    const submitReview = async () => {
      if (!reviewForm.value.action || !reviewModal.value.report) return;

      reviewSubmitting.value = true;

      try {
        const response = await api.post(`/api/moderation/admin/${reviewModal.value.report.id}/review`, {
          action: reviewForm.value.action,
          review_notes: reviewForm.value.notes,
          priority_change: reviewForm.value.priority || undefined
        });

        // 重新加载审核队列和统计
        await loadModerationQueue();
        await loadModerationStats();

        closeReviewModal();
        window.alert('审核结果已提交');
      } catch (err) {
        window.alert('提交审核失败: ' + (err.response?.data?.detail || err.message));
      } finally {
        reviewSubmitting.value = false;
      }
    };

    // 内容审核分页
    const prevModerationPage = () => {
      if (moderationPage.value > 1) {
        moderationPage.value--;
        loadModerationQueue();
      }
    };

    const nextModerationPage = () => {
      moderationPage.value++;
      loadModerationQueue();
    };

    // 内容审核工具函数
    const getPriorityLabel = (priority) => {
      const labels = {
        'urgent': '紧急',
        'high': '高',
        'medium': '中',
        'low': '低'
      };
      return labels[priority] || priority;
    };

    const getModerationStatusLabel = (status) => {
      const labels = {
        'pending': '待处理',
        'reviewing': '审核中',
        'resolved': '已处理',
        'dismissed': '已驳回'
      };
      return labels[status] || status;
    };

    const getReasonLabel = (reason) => {
      const labels = {
        'spam': '垃圾信息',
        'harassment': '骚扰欺凌',
        'violence': '暴力威胁',
        'inappropriate_content': '不当内容',
        'misinformation': '虚假信息',
        'other': '其他'
      };
      return labels[reason] || reason;
    };

    const getModerationActionLabel = (action) => {
      const labels = {
        'none': '无操作',
        'warning': '警告用户',
        'message_deleted': '删除消息',
        'user_suspended': '暂停用户',
        'user_banned': '封禁用户',
        'dismiss': '驳回举报'
      };
      return labels[action] || action;
    };

    // 系统监控相关方法
    const loadSystemHealth = async () => {
      try {
        const response = await api.get('/api/monitoring/health');
        systemHealth.value = response.data;
      } catch (err) {
        console.error('加载系统健康状态失败:', err);
      }
    };

    const loadCostAnalysis = async (hours = 24) => {
      try {
        const response = await api.get('/api/monitoring/costs', { params: { hours } });
        costAnalysis.value = response.data;
      } catch (err) {
        console.error('加载成本分析失败:', err);
      }
    };

    const loadUsageMetrics = async (hours = 24) => {
      try {
        const response = await api.get('/api/monitoring/usage', { params: { hours } });
        usageMetrics.value = response.data;
      } catch (err) {
        console.error('加载使用指标失败:', err);
      }
    };

    const loadPerformanceMetrics = async (hours = 24) => {
      try {
        const response = await api.get('/api/monitoring/performance', { params: { hours } });
        performanceMetrics.value = response.data;
      } catch (err) {
        console.error('加载性能指标失败:', err);
      }
    };

    const loadAllMonitoringData = async () => {
      monitoringLoading.value = true;
      monitoringError.value = null;

      try {
        await Promise.all([
          loadSystemHealth(),
          loadCostAnalysis(),
          loadUsageMetrics(),
          loadPerformanceMetrics()
        ]);
      } catch (err) {
        monitoringError.value = '加载监控数据失败: ' + (err.response?.data?.detail || err.message);
      } finally {
        monitoringLoading.value = false;
      }
    };

    // 监控工具函数
    const getHealthStatusClass = (status) => {
      const classes = {
        'healthy': 'success',
        'warning': 'warning',
        'critical': 'danger'
      };
      return classes[status] || 'secondary';
    };

    const formatCurrency = (amount) => {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2
      }).format(amount);
    };

    const formatNumber = (num) => {
      return new Intl.NumberFormat('en-US').format(num);
    };

    const formatBytes = (bytes) => {
      if (bytes === 0) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    const getComponentDisplayName = (component) => {
      const names = {
        'database': '数据库',
        'llm_deepseek': 'DeepSeek',
        'llm_ollama': 'Ollama',
        'llm_moonshot': 'Moonshot',
        'llm_router': 'LLM路由器',
        'cpu': 'CPU',
        'memory': '内存',
        'disk': '磁盘',
        'moderation': '内容审核'
      };
      return names[component] || component;
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
      isMounted.value = true;
      loadStats();
      loadUsers();
      loadAuditLogs();
      loadModerationStats();
      loadModerationQueue();
      loadAllMonitoringData();
    });

    // 清理
    onUnmounted(() => {
      isMounted.value = false;
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
      auditLogs,
      auditLoading,
      auditError,
      auditFilters,
      auditPage,
      auditPageSize,
      activeTab,
      tabs,
      moderationReports,
      moderationStats,
      moderationLoading,
      moderationError,
      moderationFilters,
      moderationPage,
      moderationPageSize,
      reviewModal,
      reviewForm,
      reviewSubmitting,
      systemHealth,
      costAnalysis,
      usageMetrics,
      performanceMetrics,
      monitoringLoading,
      monitoringError,
      loadStats,
      loadUsers,
      toggleUserActive,
      viewUserDetail,
      closeModal,
      viewUserConversations,
      viewUserApiUsage,
      viewUserDocuments,
      loadAuditLogs,
      prevAuditPage,
      nextAuditPage,
      loadModerationQueue,
      loadModerationStats,
      startReview,
      closeReviewModal,
      submitReview,
      prevModerationPage,
      nextModerationPage,
      loadSystemHealth,
      loadCostAnalysis,
      loadUsageMetrics,
      loadPerformanceMetrics,
      loadAllMonitoringData,
      prevPage,
      nextPage,
      getRoleLabel,
      getActionLabel,
      getActionClass,
      getStatusLabel,
      getPriorityLabel,
      getModerationStatusLabel,
      getReasonLabel,
      getModerationActionLabel,
      getHealthStatusClass,
      formatCurrency,
      formatNumber,
      formatBytes,
      getComponentDisplayName,
      formatDate
    };
  }
};
</script>

<style scoped>
:root {
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  --spacing-xxl: 3rem;
  --primary-bg: #f5f5f5;
  --card-bg: #ffffff;
  --border-color: #e0e0e0;
  --text-primary: #333333;
  --text-secondary: #666666;
  --radius-xlarge: 16px;
  --shadow-elev: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-elev-high: 0 8px 12px rgba(0, 0, 0, 0.15);
  --blur: blur(10px);
  --gradient-blue: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

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

.admin-header {
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

.admin-header:hover {
  box-shadow: var(--shadow-elev-high);
}

.admin-header h1 {
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

/* 审计日志部分 */
.audit-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-top: 2rem;
}

.audit-filters {
  display: flex;
  gap: 1rem;
}

.audit-table-container {
  overflow-x: auto;
  margin-top: 1rem;
}

.audit-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.audit-table th,
.audit-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.audit-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #495057;
}

.audit-table tr:hover {
  background-color: #f8f9fa;
}

.action-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
}

.action-badge.danger {
  background: #ffebee;
  color: #c62828;
}

.action-badge.success {
  background: #e8f5e9;
  color: #2e7d32;
}

.action-badge.warning {
  background: #fff3e0;
  color: #f57c00;
}

.action-badge.info {
  background: #e3f2fd;
  color: #1565c0;
}

.action-badge.default {
  background: #f5f5f5;
  color: #6c757d;
}

/* 标签页导航 */
.tabs-navigation {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  border-bottom: 2px solid #eee;
}

.tab-button {
  padding: 0.75rem 1.5rem;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  font-size: 1rem;
  color: #666;
  transition: all 0.2s ease;
  position: relative;
}

.tab-button:hover {
  color: #333;
  background: rgba(0, 0, 0, 0.05);
}

.tab-button.active {
  color: #2196F3;
  border-bottom-color: #2196F3;
}

.tab-badge {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background: #f44336;
  color: white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

/* 内容审核部分 */
.moderation-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.moderation-filters {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.moderation-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card.small {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.stat-card.small.pending {
  background: #fff3cd;
  color: #856404;
}

.stat-card.small.resolved {
  background: #d1ecf1;
  color: #0c5460;
}

.stat-card.small.dismissed {
  background: #f8d7da;
  color: #721c24;
}

.stat-card.small .stat-value {
  font-size: 1.5rem;
  font-weight: bold;
  margin-bottom: 0.25rem;
}

.stat-card.small .stat-label {
  font-size: 0.9rem;
  opacity: 0.8;
}

.moderation-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.report-item {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1rem;
  background: #fafafa;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.report-meta {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.priority-badge,
.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 500;
}

.priority-badge.urgent {
  background: #ffebee;
  color: #c62828;
}

.priority-badge.high {
  background: #fff3e0;
  color: #f57c00;
}

.priority-badge.medium {
  background: #f3e5f5;
  color: #7b1fa2;
}

.priority-badge.low {
  background: #e8f5e9;
  color: #2e7d32;
}

.status-badge.pending {
  background: #fff3cd;
  color: #856404;
}

.status-badge.reviewing {
  background: #cce5ff;
  color: #004085;
}

.status-badge.resolved {
  background: #d1ecf1;
  color: #0c5460;
}

.status-badge.dismissed {
  background: #f8d7da;
  color: #721c24;
}

.report-reason {
  background: #e9ecef;
  color: #495057;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
}

.report-time {
  color: #666;
  font-size: 0.9rem;
}

.report-content {
  margin-bottom: 1rem;
}

.reported-message {
  margin-bottom: 1rem;
}

.message-preview {
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 0.75rem;
  margin-top: 0.5rem;
  font-family: monospace;
  white-space: pre-wrap;
  max-height: 100px;
  overflow-y: auto;
}

.report-details {
  font-size: 0.9rem;
}

.report-details p {
  margin: 0.25rem 0;
}

.report-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-review {
  background: #ff9800;
  color: white;
}

.btn-review:hover {
  background: #f57c00;
}

.review-info {
  background: #e8f5e9;
  border: 1px solid #c3e6cb;
  border-radius: 4px;
  padding: 0.75rem;
  font-size: 0.9rem;
}

.review-info p {
  margin: 0.25rem 0;
}

/* 审核模态框 */
.modal-content.large {
  max-width: 800px;
  width: 90%;
}

.review-section {
  margin-bottom: 2rem;
}

.review-section h4 {
  margin-bottom: 1rem;
  color: #333;
  border-bottom: 1px solid #eee;
  padding-bottom: 0.5rem;
}

.review-details {
  background: #f8f9fa;
  border-radius: 4px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.description-text {
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 0.75rem;
  margin-top: 0.5rem;
  white-space: pre-wrap;
}

.content-box {
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 1rem;
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
  font-family: monospace;
}

.action-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
  color: #333;
}

.form-select,
.form-textarea {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: #2196F3;
  box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.2);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
  font-family: inherit;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid #eee;
}

.btn-cancel {
  padding: 0.75rem 1.5rem;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-cancel:hover {
  background: #5a6268;
}

.btn-submit {
  padding: 0.75rem 1.5rem;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-submit:hover:not(:disabled) {
  background: #218838;
}

.btn-submit:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

/* 系统监控部分 */
.monitoring-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.monitoring-subsection {
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid #eee;
}

.monitoring-subsection:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

/* 健康状态样式 */
.health-overview {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.overall-status {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-weight: 500;
}

.status-indicator.success {
  background: #d1ecf1;
  color: #0c5460;
}

.status-indicator.warning {
  background: #fff3cd;
  color: #856404;
}

.status-indicator.danger {
  background: #f8d7da;
  color: #721c24;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: currentColor;
}

.status-indicator.success .status-dot {
  background: #28a745;
}

.status-indicator.warning .status-dot {
  background: #ffc107;
}

.status-indicator.danger .status-dot {
  background: #dc3545;
}

.status-time {
  color: #666;
  font-size: 0.9rem;
}

.alerts-section {
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 8px;
  padding: 1rem;
}

.alerts-section h3 {
  margin: 0 0 1rem 0;
  color: #856404;
}

.alert-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid #ffeaa7;
}

.alert-item:last-child {
  border-bottom: none;
}

.alert-item.critical {
  color: #721c24;
  font-weight: 500;
}

.alert-time {
  font-size: 0.8rem;
  color: #666;
}

.components-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.component-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1rem;
  background: #fafafa;
}

.component-card.success {
  border-color: #28a745;
  background: #d1ecf1;
}

.component-card.warning {
  border-color: #ffc107;
  background: #fff3cd;
}

.component-card.danger {
  border-color: #dc3545;
  background: #f8d7da;
}

.component-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.component-name {
  font-weight: 600;
  color: #333;
}

.component-status {
  text-transform: uppercase;
  font-size: 0.8rem;
  font-weight: 500;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
}

.component-message {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

/* 成本分析样式 */
.cost-overview {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.cost-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.cost-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  padding: 1.5rem;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.cost-card h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  opacity: 0.9;
}

.cost-value {
  font-size: 2rem;
  font-weight: bold;
}

.cost-charts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
}

.chart-section {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
}

.chart-section h3 {
  margin: 0 0 1rem 0;
  color: #333;
}

.provider-costs {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.provider-cost {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.provider-name {
  min-width: 100px;
  font-weight: 500;
}

.provider-cost-value {
  min-width: 80px;
  text-align: right;
  font-weight: 600;
  color: #667eea;
}

.cost-bar {
  flex: 1;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
}

.cost-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.daily-cost-chart {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: 300px;
  overflow-y: auto;
}

.daily-cost-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid #dee2e6;
}

.daily-cost-item:last-child {
  border-bottom: none;
}

.date-label {
  min-width: 100px;
  font-size: 0.9rem;
  color: #666;
}

.cost-amount {
  min-width: 80px;
  text-align: right;
  font-weight: 600;
  color: #667eea;
}

/* 使用指标样式 */
.usage-overview {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.usage-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.usage-card {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 1.5rem;
  text-align: center;
}

.usage-card h3 {
  margin: 0 0 0.5rem 0;
  color: #666;
  font-size: 0.9rem;
}

.usage-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #333;
}

.top-models {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 1.5rem;
}

.top-models h3 {
  margin: 0 0 1rem 0;
  color: #333;
}

.model-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.model-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: white;
  border-radius: 6px;
  border: 1px solid #dee2e6;
}

.model-name {
  font-weight: 500;
  color: #333;
}

.model-usage {
  color: #667eea;
  font-weight: 600;
}

.model-response-time {
  color: #28a745;
  font-size: 0.9rem;
}

/* 性能指标样式 */
.performance-overview {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.system-resources {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 1.5rem;
}

.system-resources h3 {
  margin: 0 0 1.5rem 0;
  color: #333;
}

.resource-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.resource-name {
  min-width: 60px;
  font-weight: 500;
}

.resource-bar {
  flex: 1;
  height: 20px;
  background: #e9ecef;
  border-radius: 10px;
  overflow: hidden;
  position: relative;
}

.resource-fill {
  height: 100%;
  border-radius: 10px;
  transition: width 0.3s ease;
}

.resource-fill.cpu {
  background: linear-gradient(90deg, #28a745, #20c997);
}

.resource-fill.memory {
  background: linear-gradient(90deg, #007bff, #6610f2);
}

.resource-fill.disk {
  background: linear-gradient(90deg, #ffc107, #fd7e14);
}

.resource-value {
  min-width: 50px;
  text-align: right;
  font-weight: 600;
  margin-left: 0.5rem;
}

.resource-detail {
  font-size: 0.8rem;
  color: #666;
  margin-left: 0.5rem;
}

.bottlenecks {
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 8px;
  padding: 1.5rem;
}

.bottlenecks h3 {
  margin: 0 0 1rem 0;
  color: #856404;
}

.bottleneck-item {
  margin-bottom: 1rem;
  padding: 1rem;
  border-radius: 6px;
}

.bottleneck-item.high {
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  color: #721c24;
}

.bottleneck-item.medium {
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  color: #856404;
}

.bottleneck-recommendation {
  margin: 0.5rem 0 0 0;
  font-size: 0.9rem;
  font-style: italic;
}
</style>
