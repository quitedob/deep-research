<template>
  <div class="homepage" :class="{ 'dark-theme': isDark }">
    <!-- 背景动画 -->
    <div class="background-animation">
      <div class="floating-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
        <div class="shape shape-4"></div>
        <div class="shape shape-5"></div>
      </div>
      <div class="gradient-overlay"></div>
    </div>

    <!-- 导航栏 -->
    <nav class="navbar">
      <div class="nav-container">
        <div class="nav-brand">
          <div class="logo">
            <img src="@/assets/logo.svg" alt="Deep Research" class="logo-icon">
            <span class="logo-text">Deep Research</span>
          </div>
        </div>
        <div class="nav-actions">
          <button @click="toggleTheme" class="theme-toggle" :title="isDark ? '切换到亮色模式' : '切换到暗色模式'">
            {{ isDark ? '☀️' : '🌙' }}
          </button>
          <div class="auth-buttons">
            <router-link to="/login" class="btn btn-outline">登录</router-link>
            <router-link to="/register" class="btn btn-primary">注册</router-link>
          </div>
        </div>
      </div>
    </nav>

    <!-- 主要内容 -->
    <main class="main-content">
      <div class="content-container">
        <!-- 标题区域 -->
        <section class="hero-section">
          <div class="hero-content">
            <h1 class="hero-title">
              <span class="gradient-text">AI 驱动的</span>
              <br>
              <span class="highlight-text">深度研究平台</span>
            </h1>
            <p class="hero-subtitle">
              基于先进的大语言模型，为您提供专业的研究分析、文档处理和智能对话服务
            </p>
            <div class="hero-cta">
              <router-link to="/register" class="btn btn-large btn-primary">
                开始免费体验
                <span class="btn-arrow">→</span>
              </router-link>
              <router-link to="/login" class="btn btn-large btn-outline">
                立即登录
              </router-link>
            </div>
          </div>
        </section>

        <!-- 功能展示 -->
        <section class="features-section">
          <h2 class="section-title">核心功能</h2>
          <div class="features-grid">
            <div class="feature-card" v-for="feature in features" :key="feature.id">
              <div class="feature-icon">{{ feature.icon }}</div>
              <h3 class="feature-title">{{ feature.title }}</h3>
              <p class="feature-description">{{ feature.description }}</p>
            </div>
          </div>
        </section>

        <!-- 使用场景 -->
        <section class="scenarios-section">
          <h2 class="section-title">适用场景</h2>
          <div class="scenarios-container">
            <div class="scenario-tabs">
              <button
                v-for="scenario in scenarios"
                :key="scenario.id"
                @click="activeScenario = scenario.id"
                :class="['scenario-tab', { active: activeScenario === scenario.id }]"
              >
                {{ scenario.title }}
              </button>
            </div>
            <div class="scenario-content">
              <div class="scenario-icon">{{ currentScenario.icon }}</div>
              <h3 class="scenario-title">{{ currentScenario.title }}</h3>
              <p class="scenario-description">{{ currentScenario.description }}</p>
              <ul class="scenario-features">
                <li v-for="item in currentScenario.features" :key="item">{{ item }}</li>
              </ul>
            </div>
          </div>
        </section>

        <!-- 数据统计 -->
        <section class="stats-section">
          <div class="stats-container">
            <div class="stat-item" v-for="stat in stats" :key="stat.label">
              <div class="stat-number">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.label }}</div>
            </div>
          </div>
        </section>
      </div>
    </main>

    <!-- 页脚 -->
    <footer class="footer">
      <div class="footer-container">
        <div class="footer-content">
          <div class="footer-brand">
            <div class="logo">
              <img src="@/assets/logo.svg" alt="Deep Research" class="logo-icon">
              <span class="logo-text">Deep Research</span>
            </div>
            <p class="footer-description">专业的AI研究分析平台</p>
          </div>
          <div class="footer-links">
            <div class="link-group">
              <h4>产品</h4>
              <a href="#" @click.prevent>功能介绍</a>
              <a href="#" @click.prevent>价格方案</a>
              <a href="#" @click.prevent>使用案例</a>
            </div>
            <div class="link-group">
              <h4>支持</h4>
              <a href="#" @click.prevent>帮助中心</a>
              <a href="#" @click.prevent>联系我们</a>
              <a href="#" @click.prevent>API文档</a>
            </div>
            <div class="link-group">
              <h4>关于</h4>
              <a href="#" @click.prevent>关于我们</a>
              <a href="#" @click.prevent>隐私政策</a>
              <a href="#" @click.prevent>服务条款</a>
            </div>
          </div>
        </div>
        <div class="footer-bottom">
          <p>&copy; 2024 Deep Research. All rights reserved.</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';

const isDark = ref(false);
const activeScenario = ref('research');

const features = [
  {
    id: 1,
    icon: '📊',
    title: '智能研究分析',
    description: '基于先进的AI算法，快速生成专业的研究报告和数据分析'
  },
  {
    id: 2,
    icon: '💬',
    title: '多轮对话',
    description: '支持上下文理解的多轮对话，提供连贯的交流体验'
  },
  {
    id: 3,
    icon: '📄',
    title: '文档处理',
    description: '智能文档解析和知识提取，支持多种文档格式'
  },
  {
    id: 4,
    icon: '🎯',
    title: '个性化定制',
    description: '根据用户需求定制AI模型参数，提供个性化的服务'
  },
  {
    id: 5,
    icon: '🔒',
    title: '安全可靠',
    description: '企业级安全保障，确保数据隐私和安全'
  },
  {
    id: 6,
    icon: '⚡',
    title: '高性能计算',
    description: '优化的计算架构，提供快速响应和高并发处理能力'
  }
];

const scenarios = [
  {
    id: 'research',
    title: '学术研究',
    icon: '🎓',
    description: '为学术研究人员提供智能的研究辅助工具',
    features: [
      '文献综述自动生成',
      '研究方法论建议',
      '数据分析和可视化',
      '论文写作辅助'
    ]
  },
  {
    id: 'business',
    title: '商业分析',
    icon: '💼',
    description: '帮助企业进行市场分析和商业决策',
    features: [
      '市场趋势分析',
      '竞争对手研究',
      '商业计划书生成',
      '财务数据解读'
    ]
  },
  {
    id: 'creative',
    title: '内容创作',
    icon: '✨',
    description: '为内容创作者提供灵感和创作支持',
    features: [
      '创意头脑风暴',
      '内容大纲生成',
      '多语言翻译',
      '风格优化建议'
    ]
  }
];

const stats = [
  { value: '10K+', label: '活跃用户' },
  { value: '50K+', label: '处理文档' },
  { value: '1M+', label: 'AI对话' },
  { value: '99.9%', label: '服务可用性' }
];

const currentScenario = computed(() => {
  return scenarios.find(s => s.id === activeScenario.value) || scenarios[0];
});

const toggleTheme = () => {
  isDark.value = !isDark.value;
  console.log('[Homepage] 主题切换', { isDark: isDark.value });
  // 这里可以保存用户偏好到本地存储
  localStorage.setItem('theme_preference', isDark.value ? 'dark' : 'light');
};

onMounted(() => {
  console.log('[Homepage] 主页加载完成');

  // 智能重定向检查 - 如果用户应该被引导到其他页面
  const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
  const isFirstVisit = !localStorage.getItem('has_visited_before');
  const hasCompletedWelcome = localStorage.getItem('welcome_completed') === 'true';

  console.log('[Homepage] 用户状态检查', {
    hasToken: !!token,
    isFirstVisit,
    hasCompletedWelcome
  });

  // 如果用户已登录且有token，应该被重定向到home而不是显示homepage
  if (token) {
    console.log('[Homepage] 检测到已登录用户，重定向到主页');
    window.location.href = '/home';
    return;
  }

  // 如果这不是直接访问根路径（比如通过路由导航到/homepage），则可能需要特殊处理
  // 但如果用户已经完成欢迎流程，可能更适合显示其他内容
  if (hasCompletedWelcome && !isFirstVisit) {
    console.log('[Homepage] 用户已完成欢迎流程，可以考虑展示更个性化的内容');
    // 这里可以加载个性化推荐等内容
  }

  // 恢复用户的主题偏好
  const savedTheme = localStorage.getItem('theme_preference');
  if (savedTheme === 'dark') {
    isDark.value = true;
  }

  // 添加滚动动画效果
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-in');
      }
    });
  }, observerOptions);

  // 观察所有需要动画的元素
  setTimeout(() => {
    document.querySelectorAll('.feature-card, .scenario-content').forEach(el => {
      observer.observe(el);
    });
  }, 100);
});
</script>

<style scoped>
/* 基础样式 */
.homepage {
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
  overflow-y: auto;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #333;
  transition: all 0.3s ease;
}

.homepage.dark-theme {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  color: #e0e0e0;
}

/* 背景动画 */
.background-animation {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
  overflow: hidden;
}

.floating-shapes {
  position: absolute;
  width: 100%;
  height: 100%;
}

.shape {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  animation: float 20s infinite ease-in-out;
}

.shape-1 {
  width: 80px;
  height: 80px;
  top: 20%;
  left: 10%;
  animation-delay: 0s;
  background: rgba(102, 126, 234, 0.3);
}

.shape-2 {
  width: 120px;
  height: 120px;
  top: 60%;
  right: 15%;
  animation-delay: 5s;
  background: rgba(118, 75, 162, 0.3);
}

.shape-3 {
  width: 60px;
  height: 60px;
  bottom: 30%;
  left: 25%;
  animation-delay: 10s;
  background: rgba(255, 255, 255, 0.2);
}

.shape-4 {
  width: 100px;
  height: 100px;
  top: 40%;
  right: 30%;
  animation-delay: 15s;
  background: rgba(102, 126, 234, 0.2);
}

.shape-5 {
  width: 40px;
  height: 40px;
  bottom: 20%;
  right: 10%;
  animation-delay: 8s;
  background: rgba(118, 75, 162, 0.2);
}

@keyframes float {
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  25% { transform: translateY(-20px) rotate(90deg); }
  50% { transform: translateY(10px) rotate(180deg); }
  75% { transform: translateY(-15px) rotate(270deg); }
}

.gradient-overlay {
  position: absolute;
  width: 100%;
  height: 100%;
  background: linear-gradient(45deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  pointer-events: none;
}

.dark-theme .gradient-overlay {
  background: linear-gradient(45deg, rgba(26, 26, 46, 0.8) 0%, rgba(22, 33, 62, 0.8) 100%);
}

/* 导航栏 */
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  backdrop-filter: blur(20px);
  background: rgba(255, 255, 255, 0.1);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.dark-theme .navbar {
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-brand .logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: white;
}

.logo-icon {
  height: 32px;
  width: 32px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.theme-toggle {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 1.2rem;
  transition: all 0.3s ease;
}

.theme-toggle:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

.auth-buttons {
  display: flex;
  gap: 0.5rem;
}

/* 按钮样式 */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s ease;
  cursor: pointer;
  border: none;
  font-size: 1rem;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
  position: relative;
  overflow: hidden;
}

.btn-primary::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.btn-primary:hover::before {
  left: 100%;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

.btn-outline {
  background: transparent;
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.btn-outline:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.5);
}

.btn-large {
  padding: 1rem 2rem;
  font-size: 1.1rem;
}

.btn-arrow {
  transition: transform 0.3s ease;
}

.btn:hover .btn-arrow {
  transform: translateX(4px);
}

/* 主要内容 */
.main-content {
  margin-top: 80px;
  position: relative;
  z-index: 1;
  min-height: calc(100vh - 80px);
}

.content-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

/* Hero 区域 */
.hero-section {
  text-align: center;
  padding: 6rem 0 4rem 0;
}

.hero-title {
  font-size: 3.5rem;
  font-weight: 800;
  line-height: 1.2;
  margin-bottom: 1.5rem;
}

.gradient-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: gradient-shift 3s ease-in-out infinite;
}

@keyframes gradient-shift {
  0%, 100% { filter: hue-rotate(0deg); }
  50% { filter: hue-rotate(10deg); }
}

.highlight-text {
  color: white;
  text-shadow: 0 0 30px rgba(255, 255, 255, 0.5);
}

.hero-subtitle {
  font-size: 1.3rem;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 3rem;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.hero-cta {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

/* 功能展示 */
.features-section {
  padding: 4rem 0;
}

.section-title {
  text-align: center;
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 3rem;
  color: white;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 2rem;
}

.feature-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border-radius: 1rem;
  padding: 2rem;
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
  opacity: 0;
  transform: translateY(30px);
}

.feature-card.animate-in {
  opacity: 1;
  transform: translateY(0);
  transition: all 0.6s ease;
}

.feature-card:hover {
  transform: translateY(-10px);
  background: rgba(255, 255, 255, 0.15);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.feature-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.feature-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
  color: white;
}

.feature-description {
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.6;
}

/* 场景展示 */
.scenarios-section {
  padding: 4rem 0;
}

.scenario-tabs {
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 3rem;
  flex-wrap: wrap;
}

.scenario-tab {
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.8);
  padding: 0.75rem 1.5rem;
  border-radius: 2rem;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 600;
}

.scenario-tab:hover,
.scenario-tab.active {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.4);
  color: white;
  transform: translateY(-2px);
}

.scenario-content {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border-radius: 1rem;
  padding: 3rem;
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.2);
  max-width: 800px;
  margin: 0 auto;
  opacity: 0;
  transform: translateY(30px);
}

.scenario-content.animate-in {
  opacity: 1;
  transform: translateY(0);
  transition: all 0.6s ease;
}

.scenario-icon {
  font-size: 4rem;
  margin-bottom: 1.5rem;
}

.scenario-title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 1rem;
  color: white;
}

.scenario-description {
  font-size: 1.2rem;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 2rem;
}

.scenario-features {
  list-style: none;
  text-align: left;
  max-width: 500px;
  margin: 0 auto;
}

.scenario-features li {
  padding: 0.5rem 0;
  color: rgba(255, 255, 255, 0.8);
  position: relative;
  padding-left: 1.5rem;
}

.scenario-features li::before {
  content: '✓';
  position: absolute;
  left: 0;
  color: #667eea;
  font-weight: bold;
}

/* 统计数据 */
.stats-section {
  padding: 4rem 0;
}

.stats-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 2rem;
  text-align: center;
}

.stat-item {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border-radius: 1rem;
  padding: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.stat-number {
  font-size: 2.5rem;
  font-weight: 800;
  color: white;
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: 1.1rem;
  color: rgba(255, 255, 255, 0.8);
}

/* 页脚 */
.footer {
  background: rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(20px);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding: 3rem 0 1rem;
  margin-top: 4rem;
}

.footer-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
}

.footer-content {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 3rem;
  margin-bottom: 2rem;
}

.footer-brand {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.footer-brand .logo-icon {
  height: 24px;
  width: 24px;
}

.footer-description {
  color: rgba(255, 255, 255, 0.8);
}

.footer-links {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
}

.link-group h4 {
  color: white;
  margin-bottom: 1rem;
  font-weight: 600;
}

.link-group a {
  display: block;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  padding: 0.25rem 0;
  transition: color 0.3s ease;
}

.link-group a:hover {
  color: white;
}

.footer-bottom {
  text-align: center;
  padding-top: 2rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.6);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .hero-title {
    font-size: 2.5rem;
  }

  .hero-subtitle {
    font-size: 1.1rem;
  }

  .features-grid {
    grid-template-columns: 1fr;
  }

  .scenario-content {
    padding: 2rem;
  }

  .footer-content {
    grid-template-columns: 1fr;
    gap: 2rem;
  }

  .footer-links {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .nav-container {
    padding: 1rem;
  }

  .auth-buttons {
    gap: 0.25rem;
  }

  .btn {
    padding: 0.5rem 1rem;
    font-size: 0.9rem;
  }

  .hero-cta {
    flex-direction: column;
    align-items: center;
  }
}

@media (max-width: 480px) {
  .content-container {
    padding: 1rem;
  }

  .section-title {
    font-size: 2rem;
  }

  .scenario-tabs {
    flex-direction: column;
    align-items: center;
  }

  .stats-container {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>