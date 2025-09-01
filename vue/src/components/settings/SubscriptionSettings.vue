<template>
  <div class="settings-section subscription-settings">
    <div class="subscription-header">
      <h3>Deep Research 高级版</h3>
      <button class="manage-button subtle" @click="manageSubscription">
        管理
        <span class="dropdown-arrow">▼</span>
      </button>
    </div>
    
    <!-- 订阅状态显示 -->
    <div class="subscription-status" v-if="subscriptionInfo">
      <div class="status-badge" :class="subscriptionInfo.status">
        {{ getStatusText(subscriptionInfo.status) }}
      </div>
      <p class="renewal-info" v-if="subscriptionInfo.current_period_end">
        您的套餐将于 {{ formatDate(subscriptionInfo.current_period_end) }} 到期
      </p>
    </div>

    <!-- 记忆功能说明 -->
    <div class="memory-features-section">
      <h4>记忆功能</h4>
      <p class="features-intro">高级版包含强大的对话记忆功能：</p>
      <ul class="features-list">
        <li>
          <svg class="checkmark-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"></path></svg>
          <strong>长期记忆：</strong>AI会记住您之前的所有对话内容
        </li>
        <li>
          <svg class="checkmark-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"></path></svg>
          <strong>智能摘要：</strong>自动生成对话摘要，便于回顾
        </li>
        <li>
          <svg class="checkmark-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"></path></svg>
          <strong>个性化学习：</strong>AI根据您的偏好调整回答风格
        </li>
        <li>
          <svg class="checkmark-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"></path></svg>
          <strong>记忆搜索：</strong>快速搜索历史对话中的特定信息
        </li>
      </ul>
    </div>

    <!-- 核心功能说明 -->
    <div class="features-section">
      <h4>核心功能</h4>
      <p class="features-intro">感谢订阅 Deep Research 高级版！您的 Plus 套餐包括：</p>
      <ul class="features-list">
        <li>
          <svg class="checkmark-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"></path></svg>
          Free 套餐中的所有功能
        </li>
        <li>
          <svg class="checkmark-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"></path></svg>
          对消息、文件上传、高级数据分析、网页浏览和图片生成功能的扩展访问权限
        </li>
        <li>
          <svg class="checkmark-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"></path></svg>
          标准和高级语言模式
        </li>
        <li>
          <svg class="checkmark-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"></path></svg>
          对深度研究、多个推理模型（o4-mini、o4-mini-high 和 o3）以及 GPT-4.5 研究预览版的访问权限
        </li>
        <li>
          <svg class="checkmark-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"></path></svg>
          创建并执行任务和项目，以及自定义 GPT
        </li>
        <li>
          <svg class="checkmark-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"></path></svg>
          对 Sora 视频生成功能的有限访问权限
        </li>
        <li>
          <svg class="checkmark-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"></path></svg>
          测试新功能的机会
        </li>
      </ul>
    </div>

    <!-- 使用统计 -->
    <div class="usage-stats" v-if="usageStats">
      <h4>使用统计</h4>
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-value">{{ usageStats.total_conversations }}</div>
          <div class="stat-label">总对话数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ usageStats.total_messages }}</div>
          <div class="stat-label">总消息数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ usageStats.memory_tokens }}/{{ usageStats.memory_limit }}</div>
          <div class="stat-label">记忆令牌</div>
        </div>
      </div>
    </div>

    <!-- 付款管理 -->
    <div class="payment-section">
      <div class="payment-header">
        <h4>付款</h4>
        <button class="manage-button subtle" @click="managePayment">
          管理
          <span class="dropdown-arrow">▼</span>
        </button>
      </div>
      <a href="#" class="billing-help-link" @click="showBillingHelp">需要结算方面的帮助？</a>
    </div>

    <!-- 升级提示 -->
    <div class="upgrade-prompt" v-if="!subscriptionInfo?.has_active_subscription">
      <h4>升级到高级版</h4>
      <p>解锁所有功能，包括强大的对话记忆、无限API调用等</p>
      <button class="upgrade-button" @click="upgradeToPro">
        立即升级
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

// 响应式数据
const subscriptionInfo = ref(null);
const usageStats = ref(null);

// 模拟数据（实际应该从API获取）
const mockSubscriptionInfo = {
  has_active_subscription: true,
  status: 'active',
  current_period_end: '2025-08-10T00:00:00Z',
  plan_name: 'Deep Research Pro'
};

const mockUsageStats = {
  total_conversations: 15,
  total_messages: 127,
  memory_tokens: 3200,
  memory_limit: 4000
};

// 方法
const getStatusText = (status) => {
  const statusMap = {
    'active': '活跃',
    'canceled': '已取消',
    'past_due': '逾期',
    'incomplete': '未完成'
  };
  return statusMap[status] || status;
};

const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
};

const manageSubscription = () => {
  // 这里应该调用Stripe客户门户
  console.log('管理订阅');
};

const managePayment = () => {
  // 这里应该调用Stripe客户门户
  console.log('管理付款');
};

const showBillingHelp = () => {
  // 显示结算帮助
  console.log('显示结算帮助');
};

const upgradeToPro = () => {
  // 升级到专业版
  console.log('升级到专业版');
};

// 生命周期
onMounted(async () => {
  try {
    // 这里应该从后端API获取实际的订阅信息
    // 暂时使用模拟数据
    subscriptionInfo.value = mockSubscriptionInfo;
    usageStats.value = mockUsageStats;
  } catch (error) {
    console.error('加载订阅信息失败：', error);
  }
});
</script>

<style scoped>
.subscription-settings {
  color: var(--text-primary);
}

.subscription-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.subscription-header h3 {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.manage-button {
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 4px;
  background-color: transparent;
  color: var(--p-primary-500);
  border: 1px solid var(--p-primary-500);
}

.manage-button.subtle {
  background-color: var(--secondary-bg);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.manage-button.subtle:hover {
  background-color: var(--hover-bg);
}

.dropdown-arrow {
  font-size: 10px;
}

.subscription-status {
  margin-bottom: 30px;
  padding: 15px;
  background-color: var(--primary-bg);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  margin-bottom: 10px;
}

.status-badge.active {
  background-color: #10b981;
  color: white;
}

.status-badge.canceled {
  background-color: #ef4444;
  color: white;
}

.status-badge.past_due {
  background-color: #f59e0b;
  color: white;
}

.renewal-info {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.memory-features-section {
  background-color: var(--primary-bg);
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
  border: 1px solid var(--border-color);
}

.memory-features-section h4 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 15px 0;
  color: #8b5cf6;
}

.features-section {
  background-color: var(--primary-bg);
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
  border: 1px solid var(--border-color);
}

.features-section h4 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 15px 0;
}

.features-intro {
  font-size: 15px;
  margin-bottom: 15px;
  font-weight: 500;
}

.features-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.features-list li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 12px;
  font-size: 14px;
  line-height: 1.6;
}

.checkmark-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  margin-top: 3px;
  color: #4ade80;
}

.usage-stats {
  background-color: var(--primary-bg);
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
  border: 1px solid var(--border-color);
}

.usage-stats h4 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 20px 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--button-bg);
  margin-bottom: 5px;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.payment-section {
  border-top: 1px solid var(--border-color);
  padding-top: 20px;
}

.payment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.payment-header h4 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.billing-help-link {
  font-size: 14px;
  color: var(--button-bg);
  text-decoration: none;
  cursor: pointer;
}

.billing-help-link:hover {
  text-decoration: underline;
}

.upgrade-prompt {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 25px;
  border-radius: 12px;
  text-align: center;
  margin-top: 30px;
}

.upgrade-prompt h4 {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 10px 0;
}

.upgrade-prompt p {
  margin: 0 0 20px 0;
  opacity: 0.9;
}

.upgrade-button {
  background-color: white;
  color: #667eea;
  border: none;
  padding: 12px 30px;
  border-radius: 25px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.upgrade-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.2);
}
</style>