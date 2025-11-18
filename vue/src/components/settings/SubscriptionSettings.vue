<template>
  <div class="settings-section">
    <h3>订阅管理</h3>
    
    <div class="subscription-card">
      <div class="plan-header">
        <h4>当前计划</h4>
        <span class="plan-badge">{{ currentPlan }}</span>
      </div>
      <p class="plan-description">{{ planDescription }}</p>
      
      <div class="plan-features">
        <div class="feature-item" v-for="feature in features" :key="feature">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M20 6L9 17l-5-5" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <span>{{ feature }}</span>
        </div>
      </div>
    </div>

    <div class="upgrade-section" v-if="currentPlan === '免费版'">
      <h4>升级到专业版</h4>
      <div class="plans-grid">
        <div class="plan-card">
          <h5>专业版</h5>
          <div class="price">
            <span class="amount">¥99</span>
            <span class="period">/月</span>
          </div>
          <ul class="plan-benefits">
            <li>无限对话次数</li>
            <li>优先访问新功能</li>
            <li>更快的响应速度</li>
            <li>高级模型访问</li>
          </ul>
          <button @click="upgradePlan('pro')" class="upgrade-btn">升级</button>
        </div>

        <div class="plan-card featured">
          <div class="featured-badge">推荐</div>
          <h5>企业版</h5>
          <div class="price">
            <span class="amount">¥299</span>
            <span class="period">/月</span>
          </div>
          <ul class="plan-benefits">
            <li>专业版所有功能</li>
            <li>团队协作</li>
            <li>API访问</li>
            <li>专属客服支持</li>
          </ul>
          <button @click="upgradePlan('enterprise')" class="upgrade-btn primary">升级</button>
        </div>
      </div>
    </div>

    <div class="billing-info" v-if="currentPlan !== '免费版'">
      <h4>账单信息</h4>
      <div class="info-row">
        <span>下次续费日期:</span>
        <span>{{ nextBillingDate }}</span>
      </div>
      <div class="info-row">
        <span>付款方式:</span>
        <span>{{ paymentMethod }}</span>
      </div>
      <button @click="manageBilling" class="manage-btn">管理订阅</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const currentPlan = ref('免费版');
const nextBillingDate = ref('2024-02-01');
const paymentMethod = ref('支付宝');

const planDescription = computed(() => {
  switch (currentPlan.value) {
    case '免费版':
      return '基础功能，适合个人使用';
    case '专业版':
      return '高级功能，适合专业用户';
    case '企业版':
      return '完整功能，适合团队协作';
    default:
      return '';
  }
});

const features = computed(() => {
  switch (currentPlan.value) {
    case '免费版':
      return [
        '每日10次对话',
        '基础模型访问',
        '标准响应速度',
        '社区支持'
      ];
    case '专业版':
      return [
        '无限对话次数',
        '高级模型访问',
        '优先响应速度',
        '邮件支持'
      ];
    case '企业版':
      return [
        '专业版所有功能',
        'API访问权限',
        '团队协作功能',
        '专属客服支持'
      ];
    default:
      return [];
  }
});

const upgradePlan = (plan) => {
  alert(`升级到${plan === 'pro' ? '专业版' : '企业版'}功能开发中...`);
};

const manageBilling = () => {
  alert('管理订阅功能开发中...');
};
</script>

<style scoped>
.settings-section {
  max-width: 800px;
}

.settings-section h3 {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: var(--spacing-xl);
  color: var(--text-primary);
}

.subscription-card {
  padding: var(--spacing-xl);
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-large);
  margin-bottom: var(--spacing-xl);
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.plan-header h4 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.plan-badge {
  padding: 4px 12px;
  background: var(--accent-blue);
  color: white;
  border-radius: var(--radius-medium);
  font-size: 14px;
  font-weight: 500;
}

.plan-description {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-lg);
}

.plan-features {
  display: grid;
  gap: var(--spacing-sm);
}

.feature-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 14px;
  color: var(--text-primary);
}

.feature-item svg {
  color: var(--accent-green);
}

.upgrade-section {
  margin-bottom: var(--spacing-xl);
}

.upgrade-section h4 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-lg);
}

.plans-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--spacing-lg);
}

.plan-card {
  padding: var(--spacing-xl);
  background: var(--card-bg);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-large);
  position: relative;
  transition: all 0.2s ease;
}

.plan-card:hover {
  border-color: var(--accent-blue);
  transform: translateY(-4px);
}

.plan-card.featured {
  border-color: var(--accent-blue);
  background: linear-gradient(135deg, rgba(0, 122, 255, 0.05) 0%, rgba(0, 122, 255, 0.02) 100%);
}

.featured-badge {
  position: absolute;
  top: -12px;
  right: 20px;
  padding: 4px 12px;
  background: var(--gradient-blue);
  color: white;
  border-radius: var(--radius-medium);
  font-size: 12px;
  font-weight: 600;
}

.plan-card h5 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-md) 0;
}

.price {
  margin-bottom: var(--spacing-lg);
}

.price .amount {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
}

.price .period {
  font-size: 16px;
  color: var(--text-secondary);
}

.plan-benefits {
  list-style: none;
  padding: 0;
  margin: 0 0 var(--spacing-lg) 0;
}

.plan-benefits li {
  padding: var(--spacing-sm) 0;
  font-size: 14px;
  color: var(--text-secondary);
  position: relative;
  padding-left: 20px;
}

.plan-benefits li:before {
  content: "✓";
  position: absolute;
  left: 0;
  color: var(--accent-green);
  font-weight: 600;
}

.upgrade-btn {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-lg);
  background: var(--button-bg);
  color: var(--button-text);
  border: none;
  border-radius: var(--radius-medium);
  cursor: pointer;
  font-size: 15px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.upgrade-btn:hover {
  background: var(--button-hover-bg);
  transform: translateY(-1px);
}

.upgrade-btn.primary {
  background: var(--gradient-blue);
  color: white;
}

.billing-info {
  padding: var(--spacing-xl);
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-large);
}

.billing-info h4 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-lg) 0;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: var(--spacing-sm) 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.manage-btn {
  margin-top: var(--spacing-lg);
  padding: var(--spacing-sm) var(--spacing-lg);
  background: var(--button-bg);
  color: var(--button-text);
  border: none;
  border-radius: var(--radius-medium);
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.manage-btn:hover {
  background: var(--button-hover-bg);
}
</style>
