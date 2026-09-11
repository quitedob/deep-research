<template>
  <div class="terms-page">
    <div class="content-wrapper">
      <!-- 返回聊天链接 -->
      <router-link to="/" class="back-link">← 返回聊天</router-link>

      <!-- 页面主标题 -->
      <h1 class="main-title">条款与政策</h1>

      <!-- 法律相关条款部分 -->
      <section class="policy-section">
        <h2 class="section-title">法律</h2>
        <ul class="policy-list">
          <li class="policy-item">
            <a href="#">使用条款</a>
            <p>管理您使用 DeepSeek AI、DeepSeek Coder 及其他服务的条款，规定了用户行为规范、账户注册与注销、内容发布规则等。</p>
          </li>
          <li class="policy-item">
            <a href="#">隐私政策</a>
            <p>我们如何收集、使用和保护您的个人信息，包括数据收集范围、使用目的、共享方式及用户权利。</p>
          </li>
          <li class="policy-item">
            <a href="#">服务条款</a>
            <p>约束您特定服务（如 DeepSeek Chat、DeepSeek Coder 插件等）使用的附加条款，包含付费服务说明、试用期限及自动续费规则。</p>
          </li>
          <li class="policy-item">
            <a href="#">商业条款</a>
            <p>适用于企业、商业或开发者用户的服务条款，包含 API 调用限制、计费模式、商业授权及合规要求。</p>
          </li>
          <li class="policy-item">
            <a href="#">版权声明</a>
            <p>声明本平台内所有文字、图片、代码、音视频等内容的版权归属及使用许可，明确禁止未授权复制、转载或二次分发。</p>
          </li>
          <li class="policy-item">
            <a href="#">免责声明</a>
            <p>声明本平台对信息准确性、服务中断或不可抗力导致损失的免责范围，以及用户因使用服务可能产生风险的提示。</p>
          </li>
          <li class="policy-item">
            <a href="#">Cookie 使用政策</a>
            <p>说明我们如何使用 Cookie、LocalStorage 等技术来提升用户体验，包括会话管理、行为分析及广告定向。</p>
          </li>
          <li class="policy-item">
            <a href="#">第三方链接政策</a>
            <p>对平台页面或应用中出现的外部链接进行说明，明确本平台不对第三方内容承担责任，并建议用户在访问时自行评估风险。</p>
          </li>
          <li class="policy-item">
            <a href="#">国际用户条款</a>
            <p>针对不同国家和地区用户的特别规定，包括适用法律、数据传输限制、税收和关税说明等。</p>
          </li>
        </ul>
      </section>

      <!-- 政策相关说明部分 -->
      <section class="policy-section">
        <h2 class="section-title">政策</h2>
        <ul class="policy-list">
          <li class="policy-item">
            <a href="#">使用政策</a>
            <p>确保我们的技术被用于正当目的的准则，包括禁止仇恨言论、暴力威胁、违法犯罪和侵犯隐私等行为。</p>
          </li>
          <li class="policy-item">
            <a href="#">共享与发布政策</a>
            <p>关于研究成果分享、发布和访问的许可，涵盖学术引用规范、开源协议选择以及数据集共享流程。</p>
          </li>
          <li class="policy-item">
            <a href="#">企业隐私</a>
            <p>针对企业用户提交数据的保留和使用政策，包括商业机密保护、数据脱敏处理和合规审计要求。</p>
          </li>
          <li class="policy-item">
            <a href="#">漏洞协调披露政策</a>
            <p>在报告产品或服务漏洞时，对善意行为的定义、报告流程、漏洞确认与奖励机制的指导。</p>
          </li>
          <li class="policy-item">
            <a href="#">内容安全政策</a>
            <p>针对用户生成内容（UGC）的审核与控制流程，包括敏感词库管理、人工与自动化审核结合、申诉渠道。</p>
          </li>
          <li class="policy-item">
            <a href="#">数据保留政策</a>
            <p>我们如何收集、存储及删除用户数据，包括日志保留周期、备份策略及用户请求删除数据的流程。</p>
          </li>
          <li class="policy-item">
            <a href="#">儿童隐私政策</a>
            <p>针对未成年人使用服务的特别说明，严格遵守相关法律法规，家长或监护人同意机制及未成年人个人信息保护措施。</p>
          </li>
          <li class="policy-item">
            <a href="#">访问与可用性政策</a>
            <p>确保平台在不同设备、浏览器和网络环境下的可访问性要求，包括残障人士辅助功能支持及跨平台兼容性。</p>
          </li>
          <li class="policy-item">
            <a href="#">合规与报告政策</a>
            <p>用户如何报告违规行为（如侵权、违法内容），以及我们对举报内容的审核与处理流程，保护举报人隐私。</p>
          </li>
          <li class="policy-item">
            <a href="#">环境可持续性政策</a>
            <p>公司在服务运营和研发中如何减少碳足迹，包括数据中心节能措施、绿色采购优先策略及碳中和目标。</p>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>

<script setup>
// 脚本部分通常不需要修改，除非有新的交互逻辑
</script>

<style scoped>
.terms-page {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  background-color: var(--primary-bg);
  color: var(--text-primary);
  padding: 60px; /* 顶部内边距需要足够容纳返回链接 */
  box-sizing: border-box;
  display: flex;
  justify-content: center;
}

.content-wrapper {
  max-width: 800px;
  width: 100%;
  position: relative; /* 为返回链接的绝对定位提供参照 */
}

/* 新增：返回链接样式 */
.back-link {
  position: absolute;
  top: 20px;
  left: -150px; /* 从-80px微调到-150px以获得更好的视觉效果 */
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-color);
  text-decoration: none;
  font-weight: 500;
  padding: 10px 18px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  transition: all 0.3s ease;
}
.back-link:hover {
  text-decoration: underline;
  color: var(--button-bg); /* 悬停时颜色变化 */
}

.main-title {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 48px;
  margin-top: 20px; /* 为返回按钮留出空间 */
}

.policy-section {
  margin-bottom: 48px;
}

.section-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 24px;
}

.policy-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.policy-item a {
  font-size: 18px;
  font-weight: 500;
  color: var(--text-primary);
  text-decoration: none;
}
.policy-item a:hover {
  text-decoration: underline;
}

.policy-item p {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 8px 0 0 0;
  line-height: 1.6;
}
</style>