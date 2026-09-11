<template>
  <div class="help-center">
    <div class="help-header">
      <h2>帮助中心</h2>
      <div class="header-actions">
        <div class="search-box">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索帮助内容..."
            class="search-input"
            @input="searchHelp"
          />
          <button class="search-btn">🔍</button>
        </div>
        <button @click="showContactModal = true" class="btn btn-primary">
          💬 联系支持
        </button>
      </div>
    </div>

    <div class="help-content">
      <div class="help-sidebar">
        <div class="help-navigation">
          <h3>导航菜单</h3>
          <div class="nav-items">
            <div
              v-for="category in helpCategories"
              :key="category.id"
              class="nav-item"
              :class="{ active: activeCategory === category.id }"
              @click="selectCategory(category.id)"
            >
              <span class="nav-icon">{{ category.icon }}</span>
              <span class="nav-label">{{ category.name }}</span>
              <span class="nav-count">({{ category.articles.length }})</span>
            </div>
          </div>
        </div>

        <div class="quick-links">
          <h3>快速链接</h3>
          <div class="link-items">
            <a href="#" @click.prevent="openVideoTutorial" class="link-item">
              🎥 视频教程
            </a>
            <a href="#" @click.prevent="openUserGuide" class="link-item">
              📖 用户手册
            </a>
            <a href="#" @click.prevent="openFAQ" class="link-item">
              ❓ 常见问题
            </a>
            <a href="#" @click.prevent="openAPIReference" class="link-item">
              🔧 API文档
            </a>
            <a href="#" @click.prevent="openCommunity" class="link-item">
              👥 社区论坛
            </a>
          </div>
        </div>

        <div class="help-status">
          <h3>系统状态</h3>
          <div class="status-items">
            <div class="status-item">
              <span class="status-label">系统状态:</span>
              <span class="status-value online">正常</span>
            </div>
            <div class="status-item">
              <span class="status-label">响应时间:</span>
              <span class="status-value">125ms</span>
            </div>
            <div class="status-item">
              <span class="status-label">在线用户:</span>
              <span class="status-value">1,234</span>
            </div>
          </div>
        </div>
      </div>

      <div class="help-main">
        <div v-if="searchQuery" class="search-results">
          <h3>搜索结果</h3>
          <div v-if="searchResults.length === 0" class="no-results">
            <p>未找到相关的帮助内容</p>
          </div>
          <div v-else class="search-results-list">
            <div
              v-for="result in searchResults"
              :key="result.id"
              class="search-result-item"
              @click="openArticle(result)"
            >
              <h4>{{ result.title }}</h4>
              <p>{{ result.summary }}</p>
              <span class="result-category">{{ result.category }}</span>
            </div>
          </div>
        </div>

        <div v-else-if="activeCategory" class="category-content">
          <div class="category-header">
            <h3>{{ getCurrentCategory().name }}</h3>
            <p>{{ getCurrentCategory().description }}</p>
          </div>

          <div class="articles-grid">
            <div
              v-for="article in getCurrentCategory().articles"
              :key="article.id"
              class="article-card"
              @click="openArticle(article)"
            >
              <div class="article-icon">
                <span>{{ article.icon || '📄' }}</span>
              </div>
              <div class="article-content">
                <h4>{{ article.title }}</h4>
                <p>{{ article.summary }}</p>
                <div class="article-meta">
                  <span class="article-type">{{ article.type }}</span>
                  <span class="article-time">{{ article.readTime }}分钟阅读</span>
                  <span class="article-views">{{ article.views }}次查看</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="help-overview">
          <div class="overview-header">
            <h3>欢迎使用帮助中心</h3>
            <p>选择左侧分类或搜索您需要帮助的内容</p>
          </div>

          <div class="popular-articles">
            <h4>热门文章</h4>
            <div class="popular-list">
              <div
                v-for="article in popularArticles"
                :key="article.id"
                class="popular-item"
                @click="openArticle(article)"
              >
                <span class="popular-number">{{ article.rank }}</span>
                <span class="popular-title">{{ article.title }}</span>
                <span class="popular-views">{{ article.views }}次</span>
              </div>
            </div>
          </div>

          <div class="getting-started">
            <h4>快速入门</h4>
            <div class="starter-cards">
              <div class="starter-card" @click="selectCategory('getting-started')">
                <div class="starter-icon">🚀</div>
                <h5>新手入门</h5>
                <p>了解平台基本功能和操作</p>
              </div>
              <div class="starter-card" @click="selectCategory('code-sandbox')">
                <div class="starter-icon">💻</div>
                <h5>代码沙盒</h5>
                <p>学习如何安全执行代码</p>
              </div>
              <div class="starter-card" @click="selectCategory('research')">
                <div class="starter-icon">🔬</div>
                <h5>深度研究</h5>
                <p>掌握智能研究工作流程</p>
              </div>
              <div class="starter-card" @click="selectCategory('knowledge-base')">
                <div class="starter-icon">📚</div>
                <h5>知识库管理</h5>
                <p>构建和管理知识库</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 文章详情模态框 -->
    <div v-if="showArticleModal" class="modal-overlay" @click="closeArticleModal">
      <div class="modal-content large" @click.stop>
        <div class="modal-header">
          <h3>{{ currentArticle?.title }}</h3>
          <button @click="closeArticleModal" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div v-if="currentArticle" class="article-content">
            <div class="article-meta-info">
              <span class="article-category-tag">{{ currentArticle.category }}</span>
              <span class="article-type-tag">{{ currentArticle.type }}</span>
              <span class="article-views-info">{{ currentArticle.views }}次查看</span>
              <span class="article-update-time">更新于{{ formatDate(currentArticle.updatedAt) }}</span>
            </div>

            <div class="article-body" v-html="currentArticle.content"></div>

            <div class="article-actions">
              <button @click="likeArticle" class="btn btn-outline">
                👍 有帮助 ({{ articleLikes }})
              </button>
              <button @click="shareArticle" class="btn btn-outline">
                🔗 分享
              </button>
              <button @click="printArticle" class="btn btn-outline">
                🖨️ 打印
              </button>
            </div>

            <div class="related-articles">
              <h4>相关文章</h4>
              <div class="related-list">
                <div
                  v-for="related in currentArticle.relatedArticles"
                  :key="related.id"
                  class="related-item"
                  @click="openArticle(related)"
                >
                  <h5>{{ related.title }}</h5>
                  <p>{{ related.summary }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 联系支持模态框 -->
    <div v-if="showContactModal" class="modal-overlay" @click="closeContactModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>联系技术支持</h3>
          <button @click="closeContactModal" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div class="contact-options">
            <div class="contact-option" @click="selectContactType('chat')">
              <div class="contact-icon">💬</div>
              <div class="contact-info">
                <h4>在线聊天</h4>
                <p>实时技术支持，工作日 9:00-18:00</p>
              </div>
            </div>
            <div class="contact-option" @click="selectContactType('email')">
              <div class="contact-icon">📧</div>
              <div class="contact-info">
                <h4>邮件支持</h4>
                <p>support@example.com，24小时内回复</p>
              </div>
            </div>
            <div class="contact-option" @click="selectContactType('phone')">
              <div class="contact-icon">📞</div>
              <div class="contact-info">
                <h4>电话支持</h4>
                <p>400-123-4567，工作日 9:00-18:00</p>
              </div>
            </div>
          </div>

          <div v-if="selectedContactType" class="contact-form">
            <h4>{{ getContactTitle() }}</h4>
            <form @submit.prevent="submitContactForm">
              <div class="form-group">
                <label>问题类型</label>
                <select v-model="contactForm.issueType" class="form-select">
                  <option value="">请选择问题类型</option>
                  <option value="technical">技术问题</option>
                  <option value="account">账户问题</option>
                  <option value="billing">计费问题</option>
                  <option value="feature">功能建议</option>
                  <option value="other">其他</option>
                </select>
              </div>

              <div class="form-group">
                <label>问题描述</label>
                <textarea
                  v-model="contactForm.description"
                  placeholder="请详细描述您遇到的问题..."
                  class="form-textarea"
                  rows="5"
                  required
                ></textarea>
              </div>

              <div class="form-group">
                <label>联系邮箱</label>
                <input
                  v-model="contactForm.email"
                  type="email"
                  placeholder="your@email.com"
                  class="form-input"
                  required
                />
              </div>

              <div class="form-group">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="contactForm.attachScreenshot" />
                  附上截图（如有）
                </label>
              </div>

              <div class="form-actions">
                <button type="button" @click="closeContactModal" class="btn btn-outline">
                  取消
                </button>
                <button type="submit" class="btn btn-primary" :disabled="submitting">
                  {{ submitting ? '提交中...' : '提交' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { notificationManager as notifications } from '@/composables/useNotifications.js';
import { ref, onMounted } from 'vue'

// 响应式数据
const searchQuery = ref('')
const activeCategory = ref('')
const searchResults = ref([])
const showArticleModal = ref(false)
const showContactModal = ref(false)
const currentArticle = ref(null)
const selectedContactType = ref('')
const submitting = ref(false)
const articleLikes = ref(0)

// 联系表单
const contactForm = ref({
  issueType: '',
  description: '',
  email: '',
  attachScreenshot: false
})

// 帮助分类
const helpCategories = ref([
  {
    id: 'getting-started',
    name: '新手入门',
    icon: '🚀',
    description: '平台基础功能和快速上手指南',
    articles: [
      {
        id: 1,
        title: '平台介绍',
        summary: '了解Deep Research平台的核心功能和价值',
        type: '指南',
        readTime: 5,
        views: 1234,
        updatedAt: new Date('2024-03-15'),
        icon: '📖'
      },
      {
        id: 2,
        title: '账户注册和登录',
        summary: '如何创建账户、登录和管理个人信息',
        type: '教程',
        readTime: 3,
        views: 892,
        updatedAt: new Date('2024-03-10'),
        icon: '👤'
      },
      {
        id: 3,
        title: '界面导览',
        summary: '熟悉平台界面布局和主要功能区域',
        type: '教程',
        readTime: 8,
        views: 756,
        updatedAt: new Date('2024-03-08'),
        icon: '🗺️'
      }
    ]
  },
  {
    id: 'code-sandbox',
    name: '代码沙盒',
    icon: '💻',
    description: '安全代码执行和开发环境使用',
    articles: [
      {
        id: 4,
        title: '代码沙盒概述',
        summary: '了解代码沙盒的安全机制和使用场景',
        type: '指南',
        readTime: 6,
        views: 1456,
        updatedAt: new Date('2024-03-12'),
        icon: '🔒'
      },
      {
        id: 5,
        title: 'Python代码执行',
        summary: '在沙盒环境中安全执行Python代码',
        type: '教程',
        readTime: 10,
        views: 1892,
        updatedAt: new Date('2024-03-14'),
        icon: '🐍'
      },
      {
        id: 6,
        title: '代码模板使用',
        summary: '使用预置模板快速开始编程',
        type: '技巧',
        readTime: 4,
        views: 623,
        updatedAt: new Date('2024-03-11'),
        icon: '📋'
      }
    ]
  },
  {
    id: 'research',
    name: '深度研究',
    icon: '🔬',
    description: '智能研究工具和工作流程管理',
    articles: [
      {
        id: 7,
        title: '研究工作台介绍',
        summary: '掌握研究工作台的核心功能和操作',
        type: '指南',
        readTime: 12,
        views: 2103,
        updatedAt: new Date('2024-03-16'),
        icon: '🔍'
      },
      {
        id: 8,
        title: '智能查询技巧',
        summary: '构建有效的研究查询和问题表述',
        type: '技巧',
        readTime: 7,
        views: 1567,
        updatedAt: new Date('2024-03-13'),
        icon: '💡'
      }
    ]
  },
  {
    id: 'knowledge-base',
    name: '知识库管理',
    icon: '📚',
    description: '构建、管理和搜索知识库内容',
    articles: [
      {
        id: 9,
        title: '创建知识库',
        summary: '从零开始创建和管理个人知识库',
        type: '教程',
        readTime: 9,
        views: 987,
        updatedAt: new Date('2024-03-09'),
        icon: '🏗️'
      },
      {
        id: 10,
        title: '文档导入和管理',
        summary: '高效导入和组织各类文档资料',
        type: '指南',
        readTime: 6,
        views: 745,
        updatedAt: new Date('2024-03-07'),
        icon: '📄'
      }
    ]
  },
  {
    id: 'document-analysis',
    name: '文档分析',
    icon: '📋',
    description: '文档处理、分析和内容提取',
    articles: [
      {
        id: 11,
        title: 'OCR文字识别',
        summary: '从图片和PDF中提取文字内容',
        type: '教程',
        readTime: 8,
        views: 1678,
        updatedAt: new Date('2024-03-15'),
        icon: '🔤'
      },
      {
        id: 12,
        title: '批量文档处理',
        summary: '高效处理大量文档的技巧',
        type: '技巧',
        readTime: 5,
        views: 534,
        updatedAt: new Date('2024-03-06'),
        icon: '📁'
      }
    ]
  },
  {
    id: 'monitoring',
    name: '系统监控',
    icon: '📊',
    description: '系统状态监控和性能分析',
    articles: [
      {
        id: 13,
        title: '监控面板使用',
        summary: '查看系统状态和性能指标',
        type: '指南',
        readTime: 7,
        views: 423,
        updatedAt: new Date('2024-03-05'),
        icon: '📈'
      }
    ]
  }
])

// 热门文章
const popularArticles = ref([
  {
    id: 5,
    title: 'Python代码执行',
    summary: '在沙盒环境中安全执行Python代码',
    views: 1892,
    rank: 1
  },
  {
    id: 7,
    title: '研究工作台介绍',
    summary: '掌握研究工作台的核心功能和操作',
    views: 2103,
    rank: 2
  },
  {
    id: 11,
    title: 'OCR文字识别',
    summary: '从图片和PDF中提取文字内容',
    views: 1678,
    rank: 3
  },
  {
    id: 1,
    title: '平台介绍',
    summary: '了解Deep Research平台的核心功能和价值',
    views: 1234,
    rank: 4
  }
])

// 模拟文章内容
const articleContents = {
  1: {
    content: `
      <h2>Deep Research平台介绍</h2>
      <p>Deep Research是一个AI驱动的智能研究平台，为用户提供强大的研究工具和知识管理功能。</p>

      <h3>核心功能</h3>
      <ul>
        <li><strong>代码沙盒</strong>：安全执行代码，支持多种编程语言</li>
        <li><strong>深度研究</strong>：AI辅助的智能研究工作流</li>
        <li><strong>知识库管理</strong>：构建和维护个人知识库</li>
        <li><strong>文档分析</strong>：OCR识别和文档内容提取</li>
        <li><strong>智能搜索</strong>：跨平台的内容搜索功能</li>
      </ul>

      <h3>平台优势</h3>
      <p>Deep Research平台采用最新的AI技术，为用户提供：</p>
      <ul>
        <li>高度安全的代码执行环境</li>
        <li>智能化的研究辅助功能</li>
        <li>便捷的知识管理工具</li>
        <li>强大的文档处理能力</li>
      </ul>
    `
  },
  5: {
    content: `
      <h2>Python代码执行</h2>
      <p>在Deep Research平台的代码沙盒中，您可以安全地执行Python代码。</p>

      <h3>安全特性</h3>
      <ul>
        <li>隔离的执行环境</li>
        <li>资源限制和监控</li>
        <li>代码安全性检查</li>
        <li>执行时间限制</li>
      </ul>

      <h3>使用步骤</h3>
      <ol>
        <li>打开代码沙盒</li>
        <li>输入Python代码</li>
        <li>配置执行参数（可选）</li>
        <li>点击执行按钮</li>
        <li>查看执行结果</li>
      </ol>

      <h3>支持的功能</h3>
      <ul>
        <li>标准库支持</li>
        <li>常用第三方库</li>
        <li>代码模板</li>
        <li>执行历史记录</li>
      </ul>
    `
  }
}

// 计算属性
const getCurrentCategory = () => {
  return helpCategories.value.find(cat => cat.id === activeCategory.value) || {}
}

// 方法
const selectCategory = (categoryId) => {
  activeCategory.value = categoryId
  searchQuery.value = ''
  searchResults.value = []
}

const searchHelp = () => {
  if (!searchQuery.value.trim()) {
    searchResults.value = []
    return
  }

  const query = searchQuery.value.toLowerCase()
  const results = []

  helpCategories.value.forEach(category => {
    category.articles.forEach(article => {
      if (article.title.toLowerCase().includes(query) ||
          article.summary.toLowerCase().includes(query)) {
        results.push({
          ...article,
          category: category.name
        })
      }
    })
  })

  searchResults.value = results
}

const openArticle = (article) => {
  currentArticle.value = {
    ...article,
    content: articleContents[article.id]?.content || '<p>文章内容正在加载中...</p>',
    relatedArticles: getRelatedArticles(article)
  }
  showArticleModal.value = true
  articleLikes.value = Math.floor(Math.random() * 100) + 20
}

const getRelatedArticles = (currentArticle) => {
  // 模拟相关文章
  return helpCategories.value
    .flatMap(cat => cat.articles)
    .filter(article => article.id !== currentArticle.id)
    .slice(0, 3)
}

const closeArticleModal = () => {
  showArticleModal.value = false
  currentArticle.value = null
}

const likeArticle = () => {
  articleLikes.value++
}

const shareArticle = () => {
  // 分享功能
  console.log('分享文章:', currentArticle.value?.title)
}

const printArticle = () => {
  window.print()
}

const selectContactType = (type) => {
  selectedContactType.value = type
}

const getContactTitle = () => {
  const titles = {
    chat: '在线聊天支持',
    email: '邮件支持',
    phone: '电话支持'
  }
  return titles[selectedContactType.value] || '联系支持'
}

const submitContactForm = async () => {
  submitting.value = true
  try {
    // 模拟提交
    await new Promise(resolve => setTimeout(resolve, 2000))
    notifications.info('您的问题已提交，我们会尽快回复您！')
    closeContactModal()
  } catch (error) {
    console.error('提交失败:', error)
  } finally {
    submitting.value = false
  }
}

const closeContactModal = () => {
  showContactModal.value = false
  selectedContactType.value = ''
  contactForm.value = {
    issueType: '',
    description: '',
    email: '',
    attachScreenshot: false
  }
}

// 快速链接处理
const openVideoTutorial = () => {
  console.log('打开视频教程')
}

const openUserGuide = () => {
  selectCategory('getting-started')
}

const openFAQ = () => {
  searchQuery.value = '常见问题'
  searchHelp()
}

const openAPIReference = () => {
  console.log('打开API文档')
}

const openCommunity = () => {
  console.log('打开社区论坛')
}

// 工具方法
const formatDate = (date) => {
  return date.toLocaleDateString('zh-CN')
}

// 生命周期
onMounted(() => {
  // 可以在这里加载帮助数据
})
</script>

<style scoped>
.help-center {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}

.help-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  background: white;
  border-bottom: 1px solid #e1e8ed;
}

.help-header h2 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.5rem;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.search-box {
  display: flex;
  align-items: center;
  background: #f8f9fa;
  border: 1px solid #e1e8ed;
  border-radius: 6px;
  padding: 0.5rem;
}

.search-input {
  border: none;
  background: none;
  padding: 0.25rem 0.5rem;
  font-size: 0.9rem;
  width: 300px;
}

.search-input:focus {
  outline: none;
}

.search-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  padding: 0.25rem;
}

.help-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.help-sidebar {
  width: 320px;
  background: white;
  border-right: 1px solid #e1e8ed;
  padding: 1.5rem;
  overflow-y: auto;
}

.help-navigation h3,
.quick-links h3,
.help-status h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  font-size: 1.1rem;
}

.nav-items {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 2rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.nav-item:hover {
  background: #f8f9fa;
}

.nav-item.active {
  background: #e3f2fd;
  color: #1976d2;
}

.nav-icon {
  font-size: 1.2rem;
}

.nav-label {
  flex: 1;
  font-weight: 500;
}

.nav-count {
  font-size: 0.8rem;
  color: #5a6c7d;
}

.quick-links {
  margin-bottom: 2rem;
}

.link-items {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.link-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  color: #0369a1;
  text-decoration: none;
  border-radius: 4px;
  transition: background-color 0.3s ease;
}

.link-item:hover {
  background: #f8f9fa;
}

.status-items {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.status-item {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
}

.status-label {
  color: #5a6c7d;
}

.status-value.online {
  color: #28a745;
  font-weight: 600;
}

.help-main {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
}

.search-results h3,
.category-header h3,
.overview-header h3 {
  margin: 0 0 1.5rem 0;
  color: #2c3e50;
}

.no-results {
  text-align: center;
  padding: 2rem;
  color: #5a6c7d;
}

.search-results-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.search-result-item {
  padding: 1.5rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
}

.search-result-item:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.search-result-item h4 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.search-result-item p {
  margin: 0 0 0.5rem 0;
  color: #5a6c7d;
}

.result-category {
  font-size: 0.8rem;
  color: #0369a1;
  background: #e3f2fd;
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
}

.category-header p {
  color: #5a6c7d;
  margin-bottom: 1.5rem;
}

.articles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.article-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  gap: 1rem;
}

.article-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.article-icon {
  font-size: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 50px;
  height: 50px;
  background: #f8f9fa;
  border-radius: 50%;
}

.article-content {
  flex: 1;
}

.article-content h4 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.article-content p {
  margin: 0 0 1rem 0;
  color: #5a6c7d;
  font-size: 0.9rem;
}

.article-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.8rem;
  color: #5a6c7d;
}

.help-overview {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.overview-header {
  text-align: center;
}

.overview-header p {
  color: #5a6c7d;
}

.popular-articles h4,
.getting-started h4 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.popular-list {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.popular-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.popular-item:hover {
  background: #f8f9fa;
}

.popular-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: #0369a1;
  color: white;
  border-radius: 50%;
  font-size: 0.8rem;
  font-weight: 600;
}

.popular-title {
  flex: 1;
  color: #2c3e50;
  font-weight: 500;
}

.popular-views {
  font-size: 0.8rem;
  color: #5a6c7d;
}

.starter-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.starter-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
}

.starter-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.starter-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.starter-card h5 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.starter-card p {
  margin: 0;
  color: #5a6c7d;
  font-size: 0.9rem;
}

/* 按钮样式 */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  border: none;
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #0369a1;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #5aa4d8;
}

.btn-outline {
  background: transparent;
  color: #0369a1;
  border: 1px solid #0369a1;
}

.btn-outline:hover:not(:disabled) {
  background: #0369a1;
  color: white;
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
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-content.large {
  max-width: 900px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e1e8ed;
}

.modal-header h3 {
  margin: 0;
  color: #2c3e50;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #5a6c7d;
  padding: 0.25rem;
  border-radius: 4px;
}

.btn-close:hover {
  background: #f1f3f4;
}

.modal-body {
  padding: 1.5rem;
}

.article-meta-info {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.article-category-tag,
.article-type-tag {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}

.article-category-tag {
  background: #e3f2fd;
  color: #1976d2;
}

.article-type-tag {
  background: #e5f5f4;
  color: #115e59;
}

.article-views-info,
.article-update-time {
  font-size: 0.8rem;
  color: #5a6c7d;
}

.article-body {
  line-height: 1.6;
  color: #2c3e50;
  margin-bottom: 2rem;
}

.article-body h2 {
  color: #2c3e50;
  margin: 2rem 0 1rem 0;
}

.article-body h3 {
  color: #2c3e50;
  margin: 1.5rem 0 0.75rem 0;
}

.article-body ul,
.article-body ol {
  margin: 1rem 0;
  padding-left: 2rem;
}

.article-body li {
  margin-bottom: 0.5rem;
}

.article-actions {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
}

.related-articles h4 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.related-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.related-item {
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.related-item:hover {
  background: #e9ecef;
}

.related-item h5 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.related-item p {
  margin: 0;
  color: #5a6c7d;
  font-size: 0.9rem;
}

.contact-options {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
}

.contact-option {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.contact-option:hover {
  background: #e9ecef;
}

.contact-icon {
  font-size: 2rem;
}

.contact-info h4 {
  margin: 0 0 0.25rem 0;
  color: #2c3e50;
}

.contact-info p {
  margin: 0;
  color: #5a6c7d;
  font-size: 0.9rem;
}

.contact-form h4 {
  margin: 0 0 1.5rem 0;
  color: #2c3e50;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #2c3e50;
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e1e8ed;
  border-radius: 6px;
  font-size: 0.9rem;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: #0369a1;
  box-shadow: 0 0 0 2px rgba(3, 105, 161, 0.2);
}

.form-textarea {
  resize: vertical;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.9rem;
  color: #2c3e50;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .help-content {
    flex-direction: column;
  }

  .help-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #e1e8ed;
  }
}

@media (max-width: 768px) {
  .help-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .header-actions {
    justify-content: center;
  }

  .search-input {
    width: 200px;
  }

  .help-main {
    padding: 1rem;
  }

  .articles-grid {
    grid-template-columns: 1fr;
  }

  .starter-cards {
    grid-template-columns: repeat(2, 1fr);
  }

  .article-card {
    flex-direction: column;
    text-align: center;
  }

  .article-meta {
    justify-content: center;
  }

  .modal-content {
    width: 95%;
    margin: 1rem;
  }

  .contact-options {
    flex-direction: column;
  }
}

@media (max-width: 480px) {
  .help-sidebar {
    padding: 1rem;
  }

  .starter-cards {
    grid-template-columns: 1fr;
  }

  .article-actions {
    flex-direction: column;
  }

  .form-actions {
    flex-direction: column;
  }
}
</style>