<template>
  <div class="quick-start">
    <div class="quick-start-header">
      <h2>快速开始</h2>
      <p>选择一个场景开始您的研究之旅</p>
    </div>

    <div class="scenario-grid">
      <div v-for="scenario in scenarios" :key="scenario.id"
           class="scenario-card"
           :class="{ 'featured': scenario.featured }"
           @click="selectScenario(scenario)">
        <div class="scenario-header">
          <div class="scenario-icon">{{ scenario.icon }}</div>
          <div class="scenario-badge" v-if="scenario.badge">{{ scenario.badge }}</div>
        </div>

        <div class="scenario-content">
          <h3>{{ scenario.title }}</h3>
          <p>{{ scenario.description }}</p>

          <div class="scenario-features">
            <div v-for="feature in scenario.features" :key="feature" class="feature-item">
              <span class="feature-icon">✓</span>
              <span>{{ feature }}</span>
            </div>
          </div>
        </div>

        <div class="scenario-footer">
          <button class="btn btn-primary">
            开始使用
            <span class="btn-arrow">→</span>
          </button>
        </div>
      </div>
    </div>

    <div class="quick-actions">
      <h3>或者直接使用功能</h3>
      <div class="action-buttons">
        <button @click="navigateToChat" class="action-btn">
          <span class="action-icon">💬</span>
          <span class="action-text">智能对话</span>
        </button>

        <button @click="navigateToResearch" class="action-btn">
          <span class="action-icon">📊</span>
          <span class="action-text">深度研究</span>
        </button>

        <button @click="navigateToCodeSandbox" class="action-btn">
          <span class="action-icon">🧪</span>
          <span class="action-text">代码沙盒</span>
        </button>

        <button @click="navigateToDocuments" class="action-btn">
          <span class="action-icon">📄</span>
          <span class="action-text">文档处理</span>
        </button>
      </div>
    </div>

    <div class="help-section">
      <h3>需要帮助？</h3>
      <div class="help-options">
        <button @click="showTour" class="help-btn">
          <span class="help-icon">🎯</span>
          <div class="help-content">
            <h4>功能导览</h4>
            <p>了解平台所有功能</p>
          </div>
        </button>

        <button @click="showHelpCenter" class="help-btn">
          <span class="help-icon">📚</span>
          <div class="help-content">
            <h4>帮助中心</h4>
            <p>查看使用指南</p>
          </div>
        </button>

        <button @click="showExamples" class="help-btn">
          <span class="help-icon">💡</span>
          <div class="help-content">
            <h4>使用示例</h4>
            <p>学习最佳实践</p>
          </div>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const emit = defineEmits(['scenario-selected', 'show-tour', 'show-help', 'show-examples'])

// 场景数据
const scenarios = ref([
  {
    id: 'academic_research',
    icon: '🎓',
    title: '学术研究',
    description: '进行文献综述、数据分析和学术论文写作',
    badge: '推荐',
    featured: true,
    features: [
      '自动文献检索和分析',
      '研究方法论建议',
      '数据统计和可视化',
      '论文结构和写作指导'
    ],
    route: '/research/academic'
  },
  {
    id: 'business_analysis',
    icon: '💼',
    title: '商业分析',
    description: '市场调研、竞品分析和商业计划制定',
    badge: '热门',
    featured: true,
    features: [
      '市场趋势分析',
      '竞争对手研究',
      '商业模式评估',
      '财务数据解读'
    ],
    route: '/research/business'
  },
  {
    id: 'data_science',
    icon: '📈',
    title: '数据科学',
    description: '数据分析、机器学习和可视化',
    features: [
      '数据清洗和预处理',
      '统计分析和建模',
      '机器学习算法',
      '交互式可视化'
    ],
    route: '/research/data-science'
  },
  {
    id: 'content_creation',
    icon: '✍️',
    title: '内容创作',
    description: '文章写作、创意发想和内容优化',
    features: [
      '创意头脑风暴',
      '内容结构规划',
      'SEO优化建议',
      '多语言翻译'
    ],
    route: '/research/content'
  },
  {
    id: 'learning_education',
    icon: '📚',
    title: '学习教育',
    description: '知识学习、概念解释和练习辅导',
    features: [
      '概念深度解析',
      '学习路径规划',
      '练习题目生成',
      '知识点关联'
    ],
    route: '/research/education'
  },
  {
    id: 'personal_assistant',
    icon: '🤖',
    title: '个人助手',
    description: '日常任务管理、信息整理和决策支持',
    features: [
      '任务规划和提醒',
      '信息总结整理',
      '决策分析支持',
      '时间管理优化'
    ],
    route: '/research/personal'
  }
])

// 选择场景
const selectScenario = (scenario) => {
  emit('scenario-selected', scenario)
  if (scenario.route) {
    router.push(scenario.route)
  }
}

// 导航方法
const navigateToChat = () => {
  router.push('/home')
}

const navigateToResearch = () => {
  router.push('/home')
}

const navigateToCodeSandbox = () => {
  router.push('/code-sandbox')
}

const navigateToDocuments = () => {
  router.push('/documents')
}

// 帮助功能
const showTour = () => {
  emit('show-tour')
}

const showHelpCenter = () => {
  emit('show-help')
}

const showExamples = () => {
  emit('show-examples')
}
</script>

<style scoped>
.quick-start {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.quick-start-header {
  text-align: center;
  margin-bottom: 3rem;
}

.quick-start-header h2 {
  font-size: 2.5rem;
  color: #333;
  margin-bottom: 1rem;
}

.quick-start-header p {
  font-size: 1.2rem;
  color: #666;
}

.scenario-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 2rem;
  margin-bottom: 4rem;
}

.scenario-card {
  background: white;
  border-radius: 15px;
  padding: 2rem;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.scenario-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
  border-color: rgba(102, 126, 234, 0.3);
}

.scenario-card.featured {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  border-color: rgba(102, 126, 234, 0.2);
}

.scenario-card.featured::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
}

.scenario-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.scenario-icon {
  font-size: 3rem;
}

.scenario-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
}

.scenario-content h3 {
  font-size: 1.5rem;
  color: #333;
  margin-bottom: 1rem;
}

.scenario-content p {
  color: #666;
  line-height: 1.6;
  margin-bottom: 1.5rem;
}

.scenario-features {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.feature-icon {
  color: #28a745;
  font-weight: bold;
  font-size: 1.1rem;
}

.scenario-footer {
  margin-top: 2rem;
}

.quick-actions {
  text-align: center;
  margin-bottom: 4rem;
}

.quick-actions h3 {
  font-size: 1.8rem;
  color: #333;
  margin-bottom: 2rem;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  background: white;
  border: 2px solid #e9ecef;
  border-radius: 12px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 120px;
}

.action-btn:hover {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.05);
  transform: translateY(-4px);
}

.action-icon {
  font-size: 2rem;
}

.action-text {
  font-weight: 600;
  color: #333;
  font-size: 0.95rem;
}

.help-section {
  text-align: center;
}

.help-section h3 {
  font-size: 1.8rem;
  color: #333;
  margin-bottom: 2rem;
}

.help-options {
  display: flex;
  justify-content: center;
  gap: 2rem;
  flex-wrap: wrap;
}

.help-btn {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: #f8f9fa;
  border: 2px solid #e9ecef;
  border-radius: 12px;
  padding: 1.5rem 2rem;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: left;
  min-width: 250px;
}

.help-btn:hover {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.05);
  transform: translateY(-2px);
}

.help-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

.help-content h4 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 1.1rem;
}

.help-content p {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
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
  width: 100%;
  justify-content: center;
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

.btn-arrow {
  transition: transform 0.3s ease;
}

.btn:hover .btn-arrow {
  transform: translateX(4px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .quick-start {
    padding: 1rem;
  }

  .quick-start-header h2 {
    font-size: 2rem;
  }

  .scenario-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }

  .scenario-card {
    padding: 1.5rem;
  }

  .action-buttons {
    flex-direction: column;
    align-items: center;
  }

  .action-btn {
    width: 200px;
  }

  .help-options {
    flex-direction: column;
    align-items: center;
  }

  .help-btn {
    width: 100%;
    max-width: 300px;
  }
}

@media (max-width: 480px) {
  .quick-start-header h2 {
    font-size: 1.8rem;
  }

  .quick-start-header p {
    font-size: 1rem;
  }

  .scenario-card {
    padding: 1rem;
  }

  .scenario-icon {
    font-size: 2.5rem;
  }

  .action-btn {
    padding: 1rem;
    min-width: 100px;
  }

  .help-btn {
    padding: 1rem 1.5rem;
  }
}

/* 动画效果 */
.scenario-card {
  animation: fadeInUp 0.6s ease-out;
}

.scenario-card:nth-child(1) { animation-delay: 0.1s; }
.scenario-card:nth-child(2) { animation-delay: 0.2s; }
.scenario-card:nth-child(3) { animation-delay: 0.3s; }
.scenario-card:nth-child(4) { animation-delay: 0.4s; }
.scenario-card:nth-child(5) { animation-delay: 0.5s; }
.scenario-card:nth-child(6) { animation-delay: 0.6s; }

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>