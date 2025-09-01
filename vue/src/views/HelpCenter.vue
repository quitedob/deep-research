<template>
  <div class="help-center-page">
    <!-- 返回聊天链接 -->
    <router-link to="/" class="back-link">← 返回聊天</router-link>

    <!-- 页面头部：标题与搜索栏 -->
    <header class="page-header">
      <h1>帮助中心</h1>
      <div class="search-bar">
        <input type="text" placeholder="搜索文章..." />
        <button>搜索</button>
      </div>
    </header>

    <!-- 主要内容区域 -->
    <main class="page-content">
      <!-- 入门指南版块 -->
      <section class="topic-section">
        <h2>入门指南</h2>
        <ul class="article-list">
          <li>
            <a href="#">DeepSeek 助手是什么？</a>
            <p>简介：了解 DeepSeek 助手的功能定位、核心优势及适用场景。</p>
          </li>
          <li>
            <a href="#">如何开始第一次对话？</a>
            <p>内容：快速上手步骤，包括创建账号、选择模型、发送第一条消息。</p>
          </li>
          <li>
            <a href="#">模型选择指南</a>
            <p>内容：介绍不同模型（如 GPT-4、GPT-3.5）之间的差异、性能和费用对比。</p>
          </li>
          <li>
            <a href="#">账户与安全设置</a>
            <p>内容：如何配置两步验证、修改密码、管理登录设备。</p>
          </li>
          <li>
            <a href="#">界面导航与主要功能概览</a>
            <p>内容：帮助新用户快速熟悉界面布局、常用菜单和侧边栏功能。</p>
          </li>
          <li>
            <a href="#">常见术语说明</a>
            <p>内容：解释“上下文窗口”、“温度（Temperature）”、“RAG”等常用术语。</p>
          </li>
        </ul>
      </section>

      <!-- 计费与订阅版块 -->
      <section class="topic-section">
        <h2>计费与订阅</h2>
        <ul class="article-list">
          <li>
            <a href="#">我们的订阅计划有哪些？</a>
            <p>简介：对比免费套餐、标准套餐、企业套餐的额度、价格与增值服务。</p>
          </li>
          <li>
            <a href="#">如何升级或降级您的套餐？</a>
            <p>内容：演示在“账户设置”中切换套餐的步骤及注意事项。</p>
          </li>
          <li>
            <a href="#">发票与付款历史记录</a>
            <p>内容：说明如何查看、下载发票，及常见付款方式（信用卡、PayPal 等）。</p>
          </li>
          <li>
            <a href="#">退款政策说明</a>
            <p>内容：何种情况下可以申请退款、退款流程与时效说明。</p>
          </li>
          <li>
            <a href="#">优惠码与活动说明</a>
            <p>内容：了解当前可用优惠码、使用规则及活动截止日期。</p>
          </li>
        </ul>
      </section>

      <!-- 功能与使用版块 -->
      <section class="topic-section">
        <h2>功能与使用</h2>
        <ul class="article-list">
          <li>
            <a href="#">如何使用自定义 Agent？</a>
            <p>内容：创建、配置与管理自定义 Agent 的教程与最佳实践。</p>
          </li>
          <li>
            <a href="#">文件上传与解析功能</a>
            <p>内容：支持的文件类型、上传限制、解析效果示例与常见问题解答。</p>
          </li>
          <li>
            <a href="#">代码生成与调试技巧</a>
            <p>内容：调用 API 生成代码、在本地调试、排错指南及示例演示。</p>
          </li>
          <li>
            <a href="#">隐私保护与数据处理</a>
            <p>内容：平台如何处理用户数据、保密措施以及数据删除流程说明。</p>
          </li>
          <li>
            <a href="#">多语言支持与切换</a>
            <p>内容：如何切换界面语言、已支持的语言列表及翻译质量说明。</p>
          </li>
          <li>
            <a href="#">API 文档与示例</a>
            <p>内容：API 接口说明、示例调用、返回格式及错误码说明。</p>
          </li>
        </ul>
      </section>

      <!-- 故障排除版块 -->
      <section class="topic-section">
        <h2>故障排除</h2>
        <ul class="article-list">
          <li>
            <a href="#">无法登录或访问服务</a>
            <p>内容：常见登录故障原因、排查网络与浏览器设置、账号锁定处理。</p>
          </li>
          <li>
            <a href="#">模型回复缓慢或无响应</a>
            <p>内容：可能的网络或服务器状况、优化提示及联系客服渠道。</p>
          </li>
          <li>
            <a href="#">页面显示异常或功能失效</a>
            <p>内容：常见浏览器兼容性问题、清除缓存步骤及临时解决方法。</p>
          </li>
          <li>
            <a href="#">文件无法正确解析</a>
            <p>内容：检查文件格式、大小限制、编码方式与重试方案。</p>
          </li>
          <li>
            <a href="#">API 调用返回错误码</a>
            <p>内容：常见错误码及含义、请求示例与参数校验方法。</p>
          </li>
          <li>
            <a href="#">联系技术支持</a>
            <p>内容：提供工单提交流程、必填信息模板及处理时效说明。</p>
          </li>
        </ul>
      </section>

      <!-- 常见问题版块 -->
      <section class="topic-section">
        <h2>常见问题</h2>
        <ul class="article-list">
          <li>
            <a href="#">免费用户有哪些使用限制？</a>
            <p>内容：免费套餐的请求次数限制、并发数限制和数据保留周期。</p>
          </li>
          <li>
            <a href="#">会话历史是否会被保存？</a>
            <p>内容：会话记录保存时长与删除选项。</p>
          </li>
          <li>
            <a href="#">如何更改绑定手机或邮箱？</a>
            <p>内容：更新联系方式的步骤及验证流程。</p>
          </li>
          <li>
            <a href="#">企业版如何接入 SSO？</a>
            <p>内容：支持的第三方 SSO 服务、配置示例与注意事项。</p>
          </li>
          <li>
            <a href="#">API 调用是否计入额度？</a>
            <p>内容：介绍调用 OpenAI API、RAG 服务等是否计费以及计费方式。</p>
          </li>
        </ul>
      </section>

      <!-- 社区与资源版块 -->
      <section class="topic-section">
        <h2>社区与资源</h2>
        <ul class="article-list">
          <li>
            <a href="#">官方技术论坛</a>
            <p>链接至社区讨论区，可以查看其他用户提问与官方回复。</p>
          </li>
          <li>
            <a href="#">示例项目与代码库</a>
            <p>汇总各类示例项目（如 Python、Vue、Go 等），附 GitHub 地址与快速入门指南。</p>
          </li>
          <li>
            <a href="#">博客与教程</a>
            <p>精选官方技术博客，对热点话题与进阶技巧进行深度解读。</p>
          </li>
          <li>
            <a href="#">开发者沙龙与线下活动</a>
            <p>发布即将举办的线上线下技术分享会、黑客马拉松等活动信息。</p>
          </li>
        </ul>
      </section>
    </main>
  </div>
</template>


<script setup>
// 脚本部分通常不需要修改，除非有新的交互逻辑
</script>

<style scoped>
.help-center-page {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  background-color: var(--primary-bg);
  color: var(--text-primary);
  padding: 80px 60px 40px; /* 修改：增加顶部内边距为返回链接留出空间 */
  box-sizing: border-box;
  position: relative; /* 为返回链接的绝对定位提供参照 */
}

/* 新增：返回链接样式 */
.back-link {
  position: absolute;
  top: 30px;
  left: 40px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 16px;
}
.back-link:hover {
  text-decoration: underline;
  color: var(--button-bg); /* 悬停时颜色变化，使其更明显 */
}

.page-header {
  text-align: center;
  margin-bottom: 60px;
}

.page-header h1 {
  font-size: 40px;
  font-weight: 700;
  margin-bottom: 24px;
}

.search-bar {
  max-width: 600px;
  margin: 0 auto;
  display: flex;
}
.search-bar input {
  flex-grow: 1;
  padding: 12px 16px;
  font-size: 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px 0 0 8px;
  background-color: var(--secondary-bg);
  color: var(--text-primary);
}
.search-bar input:focus {
  outline: none;
  border-color: var(--button-bg);
}
.search-bar button {
  padding: 12px 20px;
  font-size: 16px;
  border: none;
  background-color: var(--button-bg);
  color: var(--button-text);
  border-radius: 0 8px 8px 0;
  cursor: pointer;
}

.page-content {
  max-width: 900px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 40px;
}

.topic-section h2 {
  font-size: 22px;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 12px;
  margin-bottom: 20px;
}

.article-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.article-list li a {
  color: var(--text-primary);
  text-decoration: none;
  font-size: 16px;
  transition: color 0.2s;
}
.article-list li a:hover {
  color: var(--button-bg);
  text-decoration: underline;
}
</style>