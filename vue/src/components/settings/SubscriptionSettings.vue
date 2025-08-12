<template>
  <div class="settings-section subscription-settings">
    <div class="subscription-header">
      <h3>DeepSeek 高级版</h3>
      <button class="manage-button subtle">
        管理
        <span class="dropdown-arrow">▼</span>
      </button>
    </div>
    <p class="renewal-info">您的套餐将于 2025年8月10日 取消</p>

    <div class="features-section">
      <p class="features-intro">感谢订阅 芝麻编程 高级版！您的 Plus 套餐包括：</p>
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

    <div class="payment-section">
      <div class="payment-header">
        <h4>付款</h4>
        <button class="manage-button subtle">
          管理
          <span class="dropdown-arrow">▼</span>
        </button>
      </div>
      <a href="#" class="billing-help-link">需要结算方面的帮助？</a>
    </div>
  </div>
</template>

<script setup>
// 目前为纯展示组件，未来可以添加与订阅相关的逻辑
</script>

<style scoped>
.subscription-settings {
  color: var(--text-primary);
}

.subscription-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.subscription-header h3 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.manage-button {
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 4px;
  background-color: transparent;
  color: var(--p-primary-500);
  border: 1px solid var(--p-primary-500);
  transform: translateX(-40px);
}
.manage-button.subtle {
  background-color: var(--secondary-bg); /* 调整为更柔和的背景 */
  color: var(--text-secondary); /* 调整为次要文字颜色 */
  border: 1px solid var(--border-color);
}
.manage-button.subtle:hover {
  background-color: var(--hover-bg);
}
.dropdown-arrow {
  font-size: 10px;
}

.renewal-info {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 30px;
}

.features-section {
  background-color: var(--primary-bg); /* 深色主题下可能需要一个略浅于 secondary-bg 的颜色，或者与 modal content 一致 */
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
  border: 1px solid var(--border-color);
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
  align-items: flex-start; /* 确保图标和文字顶部对齐 */
  gap: 10px;
  margin-bottom: 12px;
  font-size: 14px;
  line-height: 1.6;
}
.checkmark-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  margin-top: 3px; /* 微调使图标与文字对齐更好看 */
  color: #4ade80; /* 绿色勾选 */
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
  color: var(--button-bg); /* 使用按钮颜色以示可点击 */
  text-decoration: none;
}
.billing-help-link:hover {
  text-decoration: underline;
}
</style>