<template>
  <div class="feature-tour">
    <div class="tour-header">
      <h2>平台功能导览</h2>
      <p>了解Deep Research平台的所有强大功能</p>
    </div>

    <div class="tour-progress">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: `${((currentStep + 1) / totalSteps) * 100}%` }"></div>
      </div>
      <span class="progress-text">{{ currentStep + 1 }} / {{ totalSteps }}</span>
    </div>

    <div class="tour-content">
      <div class="feature-showcase">
        <div class="feature-visual">
          <div class="feature-icon">{{ currentFeature.icon }}</div>
          <div class="feature-animation">
            <div v-if="currentFeature.animation" class="animation-container">
              <component :is="currentFeature.animation" />
            </div>
          </div>
        </div>

        <div class="feature-info">
          <h3>{{ currentFeature.title }}</h3>
          <p class="feature-description">{{ currentFeature.description }}</p>

          <div class="feature-highlights">
            <div v-for="highlight in currentFeature.highlights" :key="highlight" class="highlight-item">
              <span class="highlight-bullet">✓</span>
              <span>{{ highlight }}</span>
            </div>
          </div>

          <div class="feature-demo" v-if="currentFeature.demo">
            <h4>功能演示</h4>
            <div class="demo-container">
              <component :is="currentFeature.demo" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="tour-navigation">
      <button @click="previousStep" :disabled="currentStep === 0" class="btn btn-outline">
        ← 上一步
      </button>

      <div class="tour-dots">
        <span v-for="(feature, index) in features" :key="index"
              :class="['dot', { active: index === currentStep }]"
              @click="goToStep(index)"></span>
      </div>

      <button @click="nextStep" :disabled="currentStep === totalSteps - 1" class="btn btn-primary">
        {{ currentStep === totalSteps - 1 ? '完成导览' : '下一步' }} →
      </button>
    </div>

    <div class="tour-actions">
      <button @click="skipTour" class="btn btn-text">跳过导览</button>
      <button @click="completeTour" class="btn btn-secondary">直接完成</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const emit = defineEmits(['tour-complete'])

// 当前步骤
const currentStep = ref(0)

// 功能特性列表
const features = [
  {
    id: 'chat',
    icon: '💬',
    title: '智能对话',
    description: '与AI助手进行自然语言对话，获得即时回答和专业建议。',
    highlights: [
      '支持多轮对话，保持上下文理解',
      '智能回复，快速响应',
      '支持多种对话场景和模式',
      '自动保存对话历史'
    ],
    animation: 'ChatAnimation'
  },
  {
    id: 'research',
    icon: '📊',
    title: '深度研究',
    description: '利用AI进行深度研究和分析，生成专业的研究报告。',
    highlights: [
      '自动文献检索和分析',
      '智能内容总结和提炼',
      '生成结构化研究报告',
      '支持多种研究领域'
    ],
    animation: 'ResearchAnimation'
  },
  {
    id: 'code',
    icon: '🧪',
    title: '代码沙盒',
    description: '在安全的隔离环境中执行Python代码，支持数据科学和分析。',
    highlights: [
      '完全隔离的执行环境',
      '支持常用数据科学库',
      '实时结果反馈',
      '代码安全检查'
    ],
    animation: 'CodeAnimation'
  },
  {
    id: 'documents',
    icon: '📄',
    title: '文档处理',
    description: '上传、解析和分析各种格式的文档，提取关键信息。',
    highlights: [
      '支持PDF、Word、图片等格式',
      '智能内容提取和总结',
      'OCR文字识别',
      '文档知识库构建'
    ],
    animation: 'DocumentAnimation'
  },
  {
    id: 'monitoring',
    icon: '📈',
    title: '系统监控',
    description: '实时监控系统运行状态，分析使用情况和性能指标。',
    highlights: [
      '实时性能监控',
      '使用统计分析',
      '健康状态检查',
      '成本分析报告'
    ],
    animation: 'MonitoringAnimation'
  },
  {
    id: 'collaboration',
    icon: '🤝',
    title: '协作功能',
    description: '与团队成员共享研究成果，协作完成项目。',
    highlights: [
      '项目协作和共享',
      '版本控制和历史记录',
      '团队成员管理',
      '权限控制和安全'
    ],
    animation: 'CollaborationAnimation'
  }
]

// 计算属性
const totalSteps = computed(() => features.length)
const currentFeature = computed(() => features[currentStep.value])

// 导航方法
const nextStep = () => {
  if (currentStep.value < totalSteps.value - 1) {
    currentStep.value++
  } else {
    completeTour()
  }
}

const previousStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const goToStep = (step) => {
  currentStep.value = step
}

const skipTour = () => {
  completeTour()
}

const completeTour = () => {
  emit('tour-complete')
}

// 生命周期
onMounted(() => {
  // 可以在这里添加初始化逻辑
})
</script>

<!-- 动画组件 -->
<script>
import { defineComponent, h } from 'vue'

// 聊天动画组件
const ChatAnimation = defineComponent({
  render() {
    return h('div', { class: 'chat-animation' }, [
      h('div', { class: 'message user-message' }, [
        h('div', { class: 'message-bubble' }, '你好，我想了解一下人工智能的发展趋势')
      ]),
      h('div', { class: 'message ai-message' }, [
        h('div', { class: 'message-bubble ai' }, 'AI正在思考...')
      ]),
      h('div', { class: 'message ai-message' }, [
        h('div', { class: 'message-bubble ai' }, '人工智能正在快速发展，主要包括机器学习、深度学习、自然语言处理等领域...')
      ])
    ])
  }
})

// 研究动画组件
const ResearchAnimation = defineComponent({
  render() {
    return h('div', { class: 'research-animation' }, [
      h('div', { class: 'search-box' }, [
        h('div', { class: 'search-input' })
      ]),
      h('div', { class: 'research-items' }, [
        h('div', { class: 'research-item' }, '📚 分析文献...'),
        h('div', { class: 'research-item' }, '📊 处理数据...'),
        h('div', { class: 'research-item' }, '📝 生成报告...')
      ]),
      h('div', { class: 'research-result' }, [
        h('div', { class: 'result-preview' }, '研究报告生成完成')
      ])
    ])
  }
})

// 代码动画组件
const CodeAnimation = defineComponent({
  render() {
    return h('div', { class: 'code-animation' }, [
      h('div', { class: 'code-editor' }, [
        h('div', { class: 'code-line' }, 'import pandas as pd'),
        h('div', { class: 'code-line' }, 'data = pd.read_csv(\'data.csv\')'),
        h('div', { class: 'code-line cursor' }, 'data.head()')
      ]),
      h('div', { class: 'code-output' }, [
        h('div', { class: 'output-line' }, '执行中...'),
        h('div', { class: 'output-line' }, '✓ 执行成功')
      ])
    ])
  }
})

// 文档动画组件
const DocumentAnimation = defineComponent({
  render() {
    return h('div', { class: 'document-animation' }, [
      h('div', { class: 'document-upload' }, [
        h('div', { class: 'upload-icon' }, '📄')
      ]),
      h('div', { class: 'document-processing' }, [
        h('div', { class: 'process-step' }, '解析文档...'),
        h('div', { class: 'process-step' }, '提取内容...'),
        h('div', { class: 'process-step' }, '分析完成')
      ])
    ])
  }
})

// 监控动画组件
const MonitoringAnimation = defineComponent({
  render() {
    return h('div', { class: 'monitoring-animation' }, [
      h('div', { class: 'metrics-chart' }, [
        h('div', { class: 'chart-bar', style: 'height: 60%' }),
        h('div', { class: 'chart-bar', style: 'height: 80%' }),
        h('div', { class: 'chart-bar', style: 'height: 45%' }),
        h('div', { class: 'chart-bar', style: 'height: 90%' })
      ]),
      h('div', { class: 'status-indicators' }, [
        h('div', { class: 'indicator green' }, '● 正常'),
        h('div', { class: 'indicator green' }, '● 健康')
      ])
    ])
  }
})

// 协作动画组件
const CollaborationAnimation = defineComponent({
  render() {
    return h('div', { class: 'collaboration-animation' }, [
      h('div', { class: 'team-members' }, [
        h('div', { class: 'member' }, '👤'),
        h('div', { class: 'member' }, '👥'),
        h('div', { class: 'member' }, '👤')
      ]),
      h('div', { class: 'collaboration-items' }, [
        h('div', { class: 'item' }, '📝 共享文档'),
        h('div', { class: 'item' }, '💬 实时讨论')
      ])
    ])
  }
})

export default {
  components: {
    ChatAnimation,
    ResearchAnimation,
    CodeAnimation,
    DocumentAnimation,
    MonitoringAnimation,
    CollaborationAnimation
  }
}
</script>

<style scoped>
.feature-tour {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;
}

.tour-header {
  text-align: center;
  margin-bottom: 2rem;
}

.tour-header h2 {
  font-size: 2rem;
  color: #333;
  margin-bottom: 0.5rem;
}

.tour-header p {
  color: #666;
  font-size: 1.1rem;
}

.tour-progress {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 3rem;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.progress-text {
  font-weight: 600;
  color: #667eea;
  min-width: 50px;
}

.feature-showcase {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3rem;
  margin-bottom: 3rem;
  align-items: center;
}

.feature-visual {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
}

.feature-icon {
  font-size: 4rem;
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-10px); }
  60% { transform: translateY(-5px); }
}

.animation-container {
  width: 300px;
  height: 200px;
  background: rgba(102, 126, 234, 0.05);
  border-radius: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.feature-info h3 {
  font-size: 1.8rem;
  color: #333;
  margin-bottom: 1rem;
}

.feature-description {
  font-size: 1.1rem;
  color: #666;
  line-height: 1.6;
  margin-bottom: 2rem;
}

.feature-highlights {
  margin-bottom: 2rem;
}

.highlight-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.highlight-bullet {
  color: #28a745;
  font-weight: bold;
  font-size: 1.1rem;
}

.feature-demo h4 {
  color: #333;
  margin-bottom: 1rem;
}

.demo-container {
  background: #f8f9fa;
  border-radius: 10px;
  padding: 1.5rem;
  border: 1px solid #e9ecef;
}

.tour-navigation {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.tour-dots {
  display: flex;
  gap: 0.5rem;
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #dee2e6;
  cursor: pointer;
  transition: all 0.3s ease;
}

.dot.active {
  background: #667eea;
  width: 32px;
  border-radius: 6px;
}

.tour-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
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

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.btn-primary:hover:not(:disabled) {
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
  color: #667eea;
  border: 2px solid #667eea;
}

.btn-outline:hover:not(:disabled) {
  background: rgba(102, 126, 234, 0.1);
}

.btn-text {
  background: transparent;
  color: #999;
  border: none;
  text-decoration: underline;
}

.btn-text:hover {
  color: #667eea;
}

/* 动画样式 */
.chat-animation {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  width: 100%;
}

.message {
  display: flex;
  gap: 0.5rem;
}

.user-message {
  justify-content: flex-end;
}

.ai-message {
  justify-content: flex-start;
}

.message-bubble {
  background: #e3f2fd;
  color: #1976d2;
  padding: 0.5rem 1rem;
  border-radius: 12px;
  max-width: 200px;
}

.ai-message .message-bubble {
  background: #f5f5f5;
  color: #333;
}

.research-animation {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 100%;
}

.search-box {
  background: white;
  border: 2px solid #667eea;
  border-radius: 8px;
  padding: 0.5rem;
  height: 30px;
}

.search-input {
  background: #f0f0f0;
  border-radius: 4px;
  height: 100%;
  width: 80%;
  animation: pulse 2s infinite;
}

.research-items {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.research-item {
  background: #e8f5e9;
  padding: 0.5rem;
  border-radius: 6px;
  font-size: 0.9rem;
  animation: slideIn 0.5s ease-out;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(-20px); }
  to { opacity: 1; transform: translateX(0); }
}

.research-result {
  background: #fff3cd;
  padding: 0.75rem;
  border-radius: 8px;
  text-align: center;
  font-weight: 600;
  color: #856404;
}

.code-animation {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 100%;
}

.code-editor {
  background: #2d3748;
  color: #e2e8f0;
  padding: 1rem;
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
}

.code-line {
  margin-bottom: 0.5rem;
}

.cursor::after {
  content: '|';
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.code-output {
  background: #1a202c;
  color: #68d391;
  padding: 1rem;
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
}

.output-line {
  margin-bottom: 0.5rem;
}

.document-animation {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  width: 100%;
}

.document-upload {
  width: 80px;
  height: 100px;
  background: #e3f2fd;
  border: 2px dashed #1976d2;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
}

.upload-icon {
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}

.document-processing {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  width: 100%;
}

.process-step {
  background: #f0f9ff;
  padding: 0.5rem;
  border-radius: 6px;
  text-align: center;
  font-size: 0.9rem;
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.monitoring-animation {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 100%;
}

.metrics-chart {
  display: flex;
  align-items: end;
  gap: 0.5rem;
  height: 100px;
}

.chart-bar {
  width: 30px;
  background: linear-gradient(to top, #667eea, #764ba2);
  border-radius: 4px 4px 0 0;
  animation: grow 1s ease-out;
}

@keyframes grow {
  from { height: 0; }
}

.status-indicators {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.indicator {
  font-size: 0.9rem;
  font-weight: 600;
}

.indicator.green {
  color: #28a745;
}

.collaboration-animation {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  width: 100%;
}

.team-members {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.member {
  font-size: 2rem;
  animation: bounce 2s infinite;
}

.member:nth-child(2) {
  animation-delay: 0.5s;
}

.member:nth-child(3) {
  animation-delay: 1s;
}

.collaboration-items {
  display: flex;
  gap: 1rem;
}

.item {
  background: #e8f5e9;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.9rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .feature-tour {
    padding: 1rem;
  }

  .feature-showcase {
    grid-template-columns: 1fr;
    gap: 2rem;
  }

  .feature-visual {
    order: 2;
  }

  .feature-info {
    order: 1;
  }

  .animation-container {
    width: 100%;
    max-width: 300px;
  }

  .tour-navigation {
    flex-direction: column;
    gap: 1rem;
  }

  .tour-navigation > div {
    width: 100%;
    display: flex;
    justify-content: center;
  }

  .tour-actions {
    flex-direction: column;
  }

  .btn {
    width: 100%;
    justify-content: center;
  }
}
</style>