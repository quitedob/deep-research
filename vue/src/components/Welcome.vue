<template>
  <div class="welcome-container">
    <div class="welcome-card">
      <div class="welcome-header">
        <div class="logo-section">
          <div class="logo-icon">🔬</div>
          <h1 class="app-title">Deep Research</h1>
        </div>
        <div class="welcome-subtitle">
          <h2>欢迎使用 AI 深度研究平台</h2>
          <p>让我们开始您的智能研究之旅</p>
        </div>
      </div>

      <div class="welcome-content">
        <!-- 平台介绍 -->
        <div class="platform-intro">
          <h3>探索 AI 驱动的深度研究平台</h3>
          <p class="intro-text">
            Deep Research 是一个专业的AI研究平台，集成了先进的语言模型、智能分析工具和多模态处理能力，
            为研究人员、开发者和企业提供全方位的智能研究支持。
          </p>
        </div>

        <!-- 核心功能展示 -->
        <div class="features-showcase">
          <h3>核心功能</h3>
          <div class="feature-grid">
            <div class="feature-item">
              <div class="feature-icon">🤖</div>
              <div class="feature-content">
                <h4>智能对话</h4>
                <p>与多模态AI助手进行自然语言交流</p>
              </div>
            </div>
            <div class="feature-item">
              <div class="feature-icon">📊</div>
              <div class="feature-content">
                <h4>深度研究</h4>
                <p>AI驱动的自动化研究流程</p>
              </div>
            </div>
            <div class="feature-item">
              <div class="feature-icon">🧪</div>
              <div class="feature-content">
                <h4>代码执行</h4>
                <p>安全的代码沙盒环境</p>
              </div>
            </div>
            <div class="feature-item">
              <div class="feature-icon">📄</div>
              <div class="feature-content">
                <h4>文档分析</h4>
                <p>智能文档理解和处理</p>
              </div>
            </div>
            <div class="feature-item">
              <div class="feature-icon">🔍</div>
              <div class="feature-content">
                <h4>知识管理</h4>
                <p>企业级知识库系统</p>
              </div>
            </div>
            <div class="feature-item">
              <div class="feature-icon">📈</div>
              <div class="feature-content">
                <h4>数据可视化</h4>
                <p>图表生成和分析</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 适用场景 -->
        <div class="use-cases">
          <h3>适用场景</h3>
          <div class="use-case-tabs">
            <div class="use-case-tab" :class="{ active: activeTab === 'academic' }" @click="activeTab = 'academic'">
              <span class="tab-icon">🎓</span>
              学术研究
            </div>
            <div class="use-case-tab" :class="{ active: activeTab === 'business' }" @click="activeTab = 'business'">
              <span class="tab-icon">💼</span>
              商业分析
            </div>
            <div class="use-case-tab" :class="{ active: activeTab === 'development' }" @click="activeTab = 'development'">
              <span class="tab-icon">💻</span>
              软件开发
            </div>
          </div>
          <div class="use-case-content">
            <div v-if="activeTab === 'academic'" class="tab-content">
              <h4>学术研究助手</h4>
              <p>• 文献综述自动生成</p>
              <p>• 研究方法论建议</p>
              <p>• 数据分析和可视化</p>
              <p>• 论文写作辅助</p>
            </div>
            <div v-if="activeTab === 'business'" class="tab-content">
              <h4>商业智能分析</h4>
              <p>• 市场趋势分析</p>
              <p>• 竞争对手研究</p>
              <p>• 商业计划书生成</p>
              <p>• 财务数据解读</p>
            </div>
            <div v-if="activeTab === 'development'" class="tab-content">
              <h4>开发效率工具</h4>
              <p>• 代码审查和优化</p>
              <p>• 技术文档生成</p>
              <p>• Bug诊断和修复</p>
              <p>• API 设计建议</p>
            </div>
          </div>
        </div>

        <!-- 平台优势 -->
        <div class="advantages">
          <h3>为什么选择 Deep Research？</h3>
          <div class="advantage-list">
            <div class="advantage-item">
              <div class="advantage-icon">⚡</div>
              <div class="advantage-content">
                <h4>高性能</h4>
                <p>优化的计算架构，提供快速响应和高并发处理能力</p>
              </div>
            </div>
            <div class="advantage-item">
              <div class="advantage-icon">🔒</div>
              <div class="advantage-content">
                <h4>安全可靠</h4>
                <p>企业级安全保障，确保数据隐私和安全</p>
              </div>
            </div>
            <div class="advantage-item">
              <div class="advantage-icon">🎯</div>
              <div class="advantage-content">
                <h4>智能路由</h4>
                <p>自动选择最适合的AI模型，优化结果质量</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="welcome-footer">
        <div class="auth-actions">
          <router-link to="/login" class="btn btn-outline">
            立即登录
          </router-link>
          <router-link to="/register" class="btn btn-primary">
            免费注册
          </router-link>
        </div>
        <div class="secondary-actions">
          <button @click="showFeatureTour" class="btn btn-secondary">
            <span class="btn-icon">🎯</span>
            功能导览
          </button>
          <router-link to="/help" class="btn btn-text">
            <span class="btn-icon">❓</span>
            帮助中心
          </router-link>
        </div>
      </div>
    </div>

    <!-- Feature Tour Modal -->
    <div v-if="showTourModal" class="modal-overlay" @click="closeTourModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>功能导览</h3>
          <button @click="closeTourModal" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <FeatureTour @tour-complete="onTourComplete" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import FeatureTour from '@/components/FeatureTour.vue'

// Props
const emit = defineEmits(['tour-complete'])

const router = useRouter()

// 响应式数据
const showTourModal = ref(false)
const activeTab = ref('academic')

// 功能导览
const showFeatureTour = () => {
  showTourModal.value = true
}

const closeTourModal = () => {
  showTourModal.value = false
}

const onTourComplete = () => {
  closeTourModal()
  emit('tour-complete')
}

// 生命周期
onMounted(() => {
  console.log('[Welcome Component] 产品介绍页面加载完成')
})

onUnmounted(() => {
  // 清理资源
})
</script>

<style scoped>
.welcome-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.welcome-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  max-width: 1000px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  animation: slideInUp 0.6s ease-out;
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.welcome-header {
  text-align: center;
  padding: 3rem 2rem 2rem;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  border-radius: 20px 20px 0 0;
}

.logo-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.logo-icon {
  font-size: 3rem;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.app-title {
  font-size: 2.5rem;
  font-weight: 800;
  color: #333;
  margin: 0;
}

.welcome-subtitle h2 {
  font-size: 1.8rem;
  color: #555;
  margin-bottom: 0.5rem;
}

.welcome-subtitle p {
  font-size: 1.1rem;
  color: #777;
  margin: 0;
}

.welcome-content {
  padding: 2rem;
}

/* 平台介绍 */
.platform-intro {
  text-align: center;
  margin-bottom: 3rem;
}

.platform-intro h3 {
  color: #333;
  margin-bottom: 1rem;
  font-size: 1.8rem;
  font-weight: 700;
}

.intro-text {
  color: #666;
  font-size: 1.1rem;
  line-height: 1.6;
  max-width: 800px;
  margin: 0 auto;
}

/* 功能展示 */
.features-showcase h3,
.use-cases h3,
.advantages h3 {
  color: #333;
  margin-bottom: 2rem;
  font-size: 1.8rem;
  font-weight: 700;
  text-align: center;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.feature-item {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.feature-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
  border-color: rgba(102, 126, 234, 0.3);
}

.feature-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.feature-content h4 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 1.2rem;
  font-weight: 600;
}

.feature-content p {
  margin: 0;
  color: #666;
  line-height: 1.5;
}

/* 使用场景 */
.use-case-tabs {
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.use-case-tab {
  background: white;
  border: 2px solid #e1e1e1;
  border-radius: 25px;
  padding: 0.75rem 1.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: #666;
}

.use-case-tab:hover,
.use-case-tab.active {
  background: #667eea;
  border-color: #667eea;
  color: white;
  transform: translateY(-2px);
}

.tab-icon {
  font-size: 1.2rem;
}

.use-case-content {
  background: rgba(255, 255, 255, 0.8);
  border-radius: 15px;
  padding: 2rem;
  margin-bottom: 2rem;
}

.tab-content h4 {
  color: #333;
  margin-bottom: 1rem;
  font-size: 1.3rem;
}

.tab-content p {
  margin: 0.5rem 0;
  color: #555;
  line-height: 1.6;
}

/* 平台优势 */
.advantage-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin-bottom: 2rem;
}

.advantage-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.5rem;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.advantage-item:hover {
  background: rgba(255, 255, 255, 1);
  transform: translateY(-2px);
}

.advantage-icon {
  font-size: 2rem;
  flex-shrink: 0;
  width: 50px;
  text-align: center;
}

.advantage-content h4 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 1.1rem;
  font-weight: 600;
}

.advantage-content p {
  margin: 0;
  color: #666;
  line-height: 1.5;
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.action-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.action-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
  border-color: rgba(102, 126, 234, 0.3);
}

.action-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

.action-content {
  flex: 1;
}

.action-content h4 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 1.1rem;
}

.action-content p {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

.action-arrow {
  color: #667eea;
  font-size: 1.2rem;
  transition: transform 0.3s ease;
}

.action-card:hover .action-arrow {
  transform: translateX(4px);
}

.recent-activity {
  margin-bottom: 2rem;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(102, 126, 234, 0.05);
  border-radius: 10px;
}

.activity-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.activity-content {
  flex: 1;
}

.activity-text {
  margin: 0 0 0.25rem 0;
  color: #333;
  font-size: 0.95rem;
}

.activity-time {
  color: #999;
  font-size: 0.85rem;
}

.tips-section {
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.1) 0%, rgba(255, 152, 0, 0.1) 100%);
  border-radius: 15px;
  padding: 2rem;
  margin-bottom: 2rem;
}

.tips-carousel {
  position: relative;
  height: 60px;
  overflow: hidden;
  margin-bottom: 1rem;
}

.tip-item {
  position: absolute;
  width: 100%;
  opacity: 0;
  transform: translateX(100%);
  transition: all 0.5s ease;
  display: flex;
  align-items: center;
}

.tip-item.active {
  opacity: 1;
  transform: translateX(0);
}

.tip-item p {
  margin: 0;
  color: #555;
  font-size: 1.05rem;
  text-align: center;
  font-style: italic;
}

.tip-indicators {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
}

.indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ddd;
  cursor: pointer;
  transition: all 0.3s ease;
}

.indicator.active {
  background: #ffc107;
  width: 24px;
  border-radius: 4px;
}

.welcome-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2rem;
  background: rgba(102, 126, 234, 0.05);
  border-radius: 0 0 20px 20px;
  border-top: 1px solid rgba(102, 126, 234, 0.1);
}

.auth-actions {
  display: flex;
  gap: 1rem;
}

.secondary-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

/* 按钮样式 */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  border: none;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

.btn-secondary {
  background: white;
  color: #667eea;
  border: 2px solid #667eea;
}

.btn-secondary:hover {
  background: rgba(102, 126, 234, 0.1);
  transform: translateY(-2px);
}

.btn-outline {
  background: transparent;
  color: #999;
  border: 2px solid #ddd;
}

.btn-outline:hover {
  color: #667eea;
  border-color: #667eea;
}

.btn-text {
  background: transparent;
  color: #666;
  border: none;
  padding: 0.5rem 1rem;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  transition: color 0.3s ease;
}

.btn-text:hover {
  color: #667eea;
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
  border-radius: 15px;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
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
  color: #333;
  font-size: 1.5rem;
}

.btn-close {
  background: none;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.btn-close:hover {
  background: #f5f5f5;
  color: #333;
}

.modal-body {
  padding: 2rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .welcome-container {
    padding: 1rem;
  }

  .welcome-card {
    border-radius: 15px;
    margin: 1rem;
  }

  .welcome-header {
    padding: 2rem 1.5rem 1.5rem;
  }

  .app-title {
    font-size: 2rem;
  }

  .welcome-subtitle h2 {
    font-size: 1.5rem;
  }

  .welcome-content {
    padding: 1.5rem;
  }

  .action-grid {
    grid-template-columns: 1fr;
  }

  .user-info {
    flex-direction: column;
    text-align: center;
  }

  .welcome-footer {
    flex-direction: column;
    gap: 1.5rem;
    padding: 1.5rem;
  }

  .auth-actions {
    flex-direction: column;
    width: 100%;
    gap: 1rem;
  }

  .secondary-actions {
    flex-direction: column;
    width: 100%;
    gap: 0.75rem;
  }

  .btn {
    padding: 0.6rem 1.2rem;
    font-size: 0.9rem;
  }
}

@media (max-width: 480px) {
  .welcome-header {
    padding: 1.5rem 1rem 1rem;
  }

  .logo-section {
    flex-direction: column;
    gap: 0.5rem;
  }

  .app-title {
    font-size: 1.8rem;
  }

  .welcome-subtitle h2 {
    font-size: 1.3rem;
  }

  .welcome-content {
    padding: 1rem;
  }

  .action-card {
    padding: 1rem;
  }

  .tips-section {
    padding: 1.5rem;
  }
}
</style>