<template>
  <div class="research-workspace">
    <div class="workspace-header">
      <div class="header-left">
        <h2>深度研究工作台</h2>
        <p>基于AI的智能研究和分析平台</p>
      </div>
      <div class="header-right">
        <div class="workspace-status">
          <span class="status-indicator" :class="researchStatus">
            {{ getResearchStatusText() }}
          </span>
        </div>
      </div>
    </div>

    <div class="workspace-main">
      <div class="research-panel">
        <div class="panel-header">
          <h3>研究任务</h3>
          <div class="panel-controls">
            <button @click="createNewResearch" class="btn btn-primary btn-sm">
              + 新建研究
            </button>
            <button @click="loadResearchList" class="btn btn-outline btn-sm" :disabled="loading">
              🔄 刷新
            </button>
          </div>
        </div>

        <div class="research-form">
          <div class="form-group">
            <label>研究主题</label>
            <input
              v-model="researchQuery"
              type="text"
              placeholder="输入您想要研究的主题或问题..."
              class="form-input"
              @keydown.enter="startResearch"
            />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>研究类型</label>
              <select v-model="researchType" class="form-select">
                <option value="comprehensive">综合研究</option>
                <option value="academic">学术研究</option>
                <option value="market">市场分析</option>
                <option value="technical">技术分析</option>
                <option value="creative">创意研究</option>
              </select>
            </div>

            <div class="form-group">
              <label>研究深度</label>
              <select v-model="researchDepth" class="form-select">
                <option value="quick">快速研究</option>
                <option value="standard">标准研究</option>
                <option value="deep">深度研究</option>
              </select>
            </div>

            <div class="form-group">
              <label>数据源</label>
              <div class="checkbox-group">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="dataSources.web" />
                  <span>网络搜索</span>
                </label>
                <label class="checkbox-label">
                  <input type="checkbox" v-model="dataSources.documents" />
                  <span>文档库</span>
                </label>
                <label class="checkbox-label">
                  <input type="checkbox" v-model="dataSources.knowledge" />
                  <span>知识库</span>
                </label>
              </div>
            </div>
          </div>

          <div class="form-actions">
            <button @click="startResearch" class="btn btn-primary" :disabled="!researchQuery.trim() || isResearching">
              <span class="btn-icon" v-if="!isResearching">🔍</span>
              <span class="btn-icon spinner" v-else>⟳</span>
              {{ isResearching ? '研究中...' : '开始研究' }}
            </button>
            <button @click="saveTemplate" class="btn btn-outline" :disabled="!researchQuery.trim()">
              💾 保存模板
            </button>
          </div>
        </div>
      </div>

      <div class="results-panel">
        <div class="panel-header">
          <h3>研究结果</h3>
          <div class="panel-controls">
            <button @click="exportResults" class="btn btn-outline btn-sm" :disabled="!hasResults">
              📄 导出
            </button>
            <button @click="shareResults" class="btn btn-outline btn-sm" :disabled="!hasResults">
              🔗 分享
            </button>
          </div>
        </div>

        <div class="results-content">
          <div v-if="isResearching" class="researching-state">
            <div class="researching-animation">
              <div class="searching-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <p>正在进行深度研究...</p>
              <div class="research-progress">
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: `${researchProgress}%` }"></div>
                </div>
                <span class="progress-text">{{ researchProgress }}% 完成</span>
              </div>
            </div>
          </div>

          <div v-else-if="hasResults" class="research-results">
            <div class="result-tabs">
              <button
                v-for="tab in resultTabs"
                :key="tab.key"
                :class="['tab-btn', { 'active': activeTab === tab.key }]"
                @click="activeTab = tab.key"
              >
                {{ tab.label }}
                <span v-if="tab.count" class="tab-count">{{ tab.count }}</span>
              </button>
            </div>

            <div class="tab-content">
              <!-- 摘要结果 -->
              <div v-if="activeTab === 'summary'" class="summary-content">
                <div class="summary-section">
                  <h4>研究摘要</h4>
                  <div class="summary-text" v-html="researchResults.summary"></div>
                </div>

                <div class="key-findings">
                  <h4>关键发现</h4>
                  <ul>
                    <li v-for="finding in researchResults.key_findings" :key="finding">
                      {{ finding }}
                    </li>
                  </ul>
                </div>

                <div class="recommendations">
                  <h4>建议行动</h4>
                  <ol>
                    <li v-for="recommendation in researchResults.recommendations" :key="recommendation">
                      {{ recommendation }}
                    </li>
                  </ol>
                </div>
              </div>

              <!-- 详细报告 -->
              <div v-else-if="activeTab === 'report'" class="report-content">
                <div class="report-sections">
                  <div v-for="(section, index) in researchResults.sections" :key="index" class="report-section">
                    <h4>{{ section.title }}</h4>
                    <div class="section-content" v-html="section.content"></div>
                  </div>
                </div>
              </div>

              <!-- 数据源 -->
              <div v-else-if="activeTab === 'sources'" class="sources-content">
                <div class="sources-grid">
                  <div v-for="source in researchResults.sources" :key="source.id" class="source-item">
                    <div class="source-header">
                      <h5>{{ source.title }}</h5>
                      <span class="source-type">{{ source.type }}</span>
                    </div>
                    <p class="source-summary">{{ source.summary }}</p>
                    <div class="source-meta">
                      <span class="source-relevance">相关性: {{ source.relevance }}%</span>
                      <a :href="source.url" target="_blank" class="source-link">查看原文</a>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 可视化 -->
              <div v-else-if="activeTab === 'visualizations'" class="visualizations-content">
                <div class="viz-grid">
                  <div v-for="viz in researchResults.visualizations" :key="viz.id" class="viz-item">
                    <div class="viz-header">
                      <h5>{{ viz.title }}</h5>
                      <span class="viz-type">{{ viz.type }}</span>
                    </div>
                    <div class="viz-content">
                      <img :src="viz.image" :alt="viz.title" v-if="viz.image" />
                      <div v-else class="viz-placeholder">
                        {{ viz.description }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="no-results">
            <div class="empty-icon">📊</div>
            <h4>暂无研究结果</h4>
            <p>输入研究主题并点击"开始研究"以获取结果</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 研究历史侧边栏 -->
    <div class="history-sidebar">
      <div class="sidebar-header">
        <h3>研究历史</h3>
        <button @click="clearHistory" class="btn btn-xs btn-outline" title="清空历史">
          🗑️
        </button>
      </div>

      <div class="history-list">
        <div
          v-for="item in researchHistory"
          :key="item.id"
          class="history-item"
          :class="{ 'active': selectedHistoryId === item.id }"
          @click="selectHistoryItem(item)"
        >
          <div class="history-title">{{ item.query }}</div>
          <div class="history-meta">
            <span class="history-time">{{ formatTime(item.timestamp) }}</span>
            <span class="history-status" :class="item.status">
              {{ getHistoryStatusText(item.status) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ragAPI } from '@/services/api'

// 响应式数据
const researchQuery = ref('')
const researchType = ref('comprehensive')
const researchDepth = ref('standard')
const dataSources = ref({
  web: true,
  documents: true,
  knowledge: false
})

const isResearching = ref(false)
const researchProgress = ref(0)
const researchResults = ref(null)
const researchStatus = ref('idle')
const activeTab = ref('summary')
const selectedHistoryId = ref(null)
const researchHistory = ref([])
const loading = ref(false)

// 结果标签页
const resultTabs = computed(() => {
  const tabs = [
    { key: 'summary', label: '摘要', count: null },
    { key: 'report', label: '详细报告', count: researchResults.value?.sections?.length || 0 },
    { key: 'sources', label: '数据源', count: researchResults.value?.sources?.length || 0 },
    { key: 'visualizations', label: '可视化', count: researchResults.value?.visualizations?.length || 0 }
  ]
  return tabs
})

const hasResults = computed(() => {
  return researchResults.value && !isResearching.value
})

// 方法
const getResearchStatusText = () => {
  const statusMap = {
    idle: '就绪',
    searching: '搜索中',
    analyzing: '分析中',
    generating: '生成报告',
    completed: '已完成',
    error: '错误'
  }
  return statusMap[researchStatus.value] || '未知'
}

const getHistoryStatusText = (status) => {
  const statusMap = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return statusMap[status] || status
}

const startResearch = async () => {
  if (!researchQuery.value.trim()) {
    return
  }

  isResearching.value = true
  researchStatus.value = 'searching'
  researchProgress.value = 0

  try {
    // 模拟研究进度
    const progressInterval = setInterval(() => {
      if (researchProgress.value < 90) {
        researchProgress.value += Math.random() * 15
      }
    }, 500)

    // 模拟API调用
    await simulateResearch()

    clearInterval(progressInterval)
    researchProgress.value = 100
    researchStatus.value = 'completed'

    // 添加到历史记录
    addToHistory()
  } catch (error) {
    researchStatus.value = 'error'
    console.error('研究失败:', error)
  } finally {
    isResearching.value = false
  }
}

const simulateResearch = async () => {
  // 模拟搜索阶段
  researchStatus.value = 'searching'
  await sleep(2000)

  // 模拟分析阶段
  researchStatus.value = 'analyzing'
  await sleep(3000)

  // 模拟生成报告阶段
  researchStatus.value = 'generating'
  await sleep(2000)

  // 生成模拟结果
  researchResults.value = generateMockResults()
}

const generateMockResults = () => {
  return {
    summary: `<p>基于对"<strong>${researchQuery.value}</strong>"的深度研究，我们发现了以下关键信息：</p>
<p>这是一个重要的研究领域，涉及多个方面的考量。通过综合分析现有资料和数据，我们可以得出以下结论。</p>`,
    key_findings: [
      '该主题具有广泛的研究价值和实际应用前景',
      '相关技术正在快速发展，值得关注最新进展',
      '市场需求持续增长，商业潜力巨大',
      '跨学科融合趋势明显，需要综合多领域知识'
    ],
    recommendations: [
      '持续关注该领域的技术发展和市场动态',
      '加强与相关机构的合作与交流',
      '建立完善的知识管理体系',
      '制定长远的发展战略规划'
    ],
    sections: [
      {
        title: '背景分析',
        content: `<p>随着科技的不断发展，${researchQuery.value}已成为一个备受关注的热点话题。本节将从多个角度分析其背景和重要性。</p>`
      },
      {
        title: '现状评估',
        content: `<p>当前${researchQuery.value}的发展状况总体良好，但仍面临一些挑战和机遇。我们需要客观评估现状，为未来发展指明方向。</p>`
      },
      {
        title: '发展趋势',
        content: `<p>展望未来，${researchQuery.value}将呈现出以下发展趋势：技术融合加速、应用场景拓展、产业生态完善等。</p>`
      }
    ],
    sources: [
      {
        id: 1,
        title: '相关研究报告',
        type: '学术论文',
        summary: '详细分析了该领域的发展现状和未来趋势',
        relevance: 95,
        url: '#'
      },
      {
        id: 2,
        title: '行业分析',
        type: '行业报告',
        summary: '提供了市场规模和竞争格局的深入分析',
        relevance: 88,
        url: '#'
      }
    ],
    visualizations: [
      {
        id: 1,
        title: '发展趋势图',
        type: '趋势图',
        description: '展示该领域的发展趋势和关键节点'
      },
      {
        id: 2,
        title: '市场份额分布',
        type: '饼图',
        description: '各细分领域的市场占比情况'
      }
    ]
  }
}

const createNewResearch = () => {
  researchQuery.value = ''
  researchType.value = 'comprehensive'
  researchDepth.value = 'standard'
  dataSources.value = { web: true, documents: true, knowledge: false }
  researchResults.value = null
  activeTab.value = 'summary'
}

const loadResearchList = async () => {
  loading.value = true
  try {
    // 这里应该调用实际的API
    await sleep(1000)
    // researchHistory.value = await ragAPI.getResearchHistory()
  } catch (error) {
    console.error('加载研究列表失败:', error)
  } finally {
    loading.value = false
  }
}

const saveTemplate = () => {
  const template = {
    query: researchQuery.value,
    type: researchType.value,
    depth: researchDepth.value,
    dataSources: dataSources.value,
    timestamp: new Date().toISOString()
  }

  // 这里应该调用API保存模板
  console.log('保存模板:', template)
  alert('模板已保存')
}

const exportResults = () => {
  if (!researchResults.value) return

  const content = [
    '=== 研究报告 ===',
    `主题: ${researchQuery.value}`,
    `类型: ${researchType.value}`,
    `深度: ${researchDepth.value}`,
    `生成时间: ${new Date().toLocaleString()}`,
    '',
    '=== 摘要 ===',
    researchResults.value.summary,
    '',
    '=== 关键发现 ===',
    ...researchResults.value.key_findings.map(f => `• ${f}`),
    '',
    '=== 建议 ===',
    ...researchResults.value.recommendations.map((r, i) => `${i + 1}. ${r}`),
    '',
    '=== 详细报告 ===',
    ...researchResults.value.sections.map(s => `${s.title}\n${s.content}`)
  ].join('\n')

  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `research_report_${Date.now()}.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const shareResults = () => {
  // 这里应该实现分享功能
  console.log('分享研究结果')
  alert('分享功能开发中')
}

const selectHistoryItem = (item) => {
  selectedHistoryId.value = item.id
  researchQuery.value = item.query
  researchType.value = item.type
  researchDepth.value = item.depth
  dataSources.value = item.dataSources

  if (item.results) {
    researchResults.value = item.results
  }
}

const clearHistory = () => {
  if (confirm('确定要清空研究历史吗？')) {
    researchHistory.value = []
    selectedHistoryId.value = null
  }
}

const addToHistory = () => {
  const historyItem = {
    id: Date.now().toString(),
    query: researchQuery.value,
    type: researchType.value,
    depth: researchDepth.value,
    dataSources: { ...dataSources.value },
    results: researchResults.value,
    status: 'completed',
    timestamp: new Date()
  }

  researchHistory.value.unshift(historyItem)
  selectedHistoryId.value = historyItem.id

  // 限制历史记录数量
  if (researchHistory.value.length > 50) {
    researchHistory.value = researchHistory.value.slice(0, 50)
  }
}

const formatTime = (timestamp) => {
  const now = new Date()
  const diff = now - timestamp
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  return `${days}天前`
}

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))

// 生命周期
onMounted(() => {
  loadResearchList()
})
</script>

<style scoped>
.research-workspace {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f8f9fa;
}

.workspace-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  background: white;
  border-bottom: 1px solid #e9ecef;
}

.header-left h2 {
  margin: 0 0 0.5rem 0;
  font-size: 1.8rem;
  color: #333;
}

.header-left p {
  margin: 0;
  color: #666;
  font-size: 1rem;
}

.workspace-status {
  display: flex;
  align-items: center;
}

.status-indicator {
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
}

.status-indicator.idle {
  background: #6c757d;
  color: white;
}

.status-indicator.searching,
.status-indicator.analyzing,
.status-indicator.generating {
  background: #007bff;
  color: white;
}

.status-indicator.completed {
  background: #28a745;
  color: white;
}

.status-indicator.error {
  background: #dc3545;
  color: white;
}

.workspace-main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.research-panel {
  flex: 1;
  border-right: 1px solid #e9ecef;
  display: flex;
  flex-direction: column;
}

.results-panel {
  width: 400px;
  min-width: 300px;
  background: white;
  display: flex;
  flex-direction: column;
}

.history-sidebar {
  width: 300px;
  background: white;
  border-left: 1px solid #e9ecef;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #e9ecef;
  background: #f8f9fa;
}

.panel-header h3 {
  margin: 0;
  font-size: 1.1rem;
  color: #333;
}

.panel-controls {
  display: flex;
  gap: 0.5rem;
}

.research-form {
  padding: 1.5rem;
  flex: 1;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #333;
}

.form-input,
.form-select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.checkbox-group {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #555;
  cursor: pointer;
}

.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.results-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.researching-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: #666;
}

.researching-animation {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.searching-dots {
  display: flex;
  gap: 0.5rem;
}

.searching-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #667eea;
  animation: bounce 1.4s infinite ease-in-out both;
}

.searching-dots span:nth-child(1) { animation-delay: -0.32s; }
.searching-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.research-progress {
  width: 200px;
}

.progress-bar {
  width: 100%;
  height: 6px;
  background: #e9ecef;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.85rem;
  color: #667eea;
  font-weight: 600;
}

.result-tabs {
  display: flex;
  border-bottom: 1px solid #e9ecef;
  margin-bottom: 1rem;
}

.tab-btn {
  position: relative;
  padding: 0.75rem 1rem;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  font-size: 0.9rem;
  color: #666;
  transition: all 0.3s ease;
}

.tab-btn.active {
  color: #667eea;
  border-bottom-color: #667eea;
}

.tab-count {
  background: #667eea;
  color: white;
  border-radius: 10px;
  padding: 0.125rem 0.5rem;
  font-size: 0.75rem;
  margin-left: 0.5rem;
}

.tab-content {
  max-height: calc(100% - 60px);
  overflow-y: auto;
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.summary-section,
.key-findings,
.recommendations {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1rem;
}

.summary-section h4,
.key-findings h4,
.recommendations h4 {
  margin: 0 0 1rem 0;
  color: #333;
  font-size: 1.1rem;
}

.summary-text {
  line-height: 1.6;
  color: #555;
}

.key-findings ul,
.recommendations ol {
  margin: 0;
  padding-left: 1.5rem;
  color: #555;
}

.key-findings li,
.recommendations li {
  margin-bottom: 0.5rem;
  line-height: 1.4;
}

.report-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.report-sections {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.report-section {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
}

.report-section h4 {
  margin: 0 0 1rem 0;
  color: #333;
  font-size: 1.2rem;
}

.section-content {
  line-height: 1.6;
  color: #555;
}

.sources-content {
  padding: 0;
}

.sources-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.source-item {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1rem;
  border-left: 4px solid #667eea;
}

.source-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.75rem;
}

.source-header h5 {
  margin: 0;
  color: #333;
  font-size: 1rem;
  line-height: 1.3;
}

.source-type {
  background: #667eea;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.source-summary {
  margin: 0 0 0.75rem 0;
  color: #666;
  font-size: 0.9rem;
  line-height: 1.4;
}

.source-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8rem;
}

.source-relevance {
  color: #28a745;
  font-weight: 600;
}

.source-link {
  color: #667eea;
  text-decoration: none;
}

.source-link:hover {
  text-decoration: underline;
}

.visualizations-content {
  padding: 0;
}

.viz-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.viz-item {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
}

.viz-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.viz-header h5 {
  margin: 0;
  color: #333;
  font-size: 0.9rem;
}

.viz-type {
  background: #6c757d;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.7rem;
}

.viz-content {
  height: 150px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.viz-placeholder {
  color: #999;
  font-size: 0.85rem;
  text-align: center;
}

.no-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: #999;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.no-results h4 {
  margin: 0 0 0.5rem 0;
  color: #666;
}

.no-results p {
  margin: 0;
  font-size: 0.9rem;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #e9ecef;
  background: #f8f9fa;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 1rem;
  color: #333;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.history-item {
  padding: 0.75rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 0.5rem;
}

.history-item:hover {
  background: #f8f9fa;
}

.history-item.active {
  background: rgba(102, 126, 234, 0.1);
  border-left: 3px solid #667eea;
}

.history-title {
  font-size: 0.9rem;
  color: #333;
  font-weight: 500;
  margin-bottom: 0.25rem;
  line-height: 1.3;
}

.history-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
}

.history-time {
  color: #999;
}

.history-status {
  padding: 0.125rem 0.5rem;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 600;
}

.history-status.completed {
  background: #d4edda;
  color: #155724;
}

.history-status.failed {
  background: #f8d7da;
  color: #721c24;
}

.history-status.pending {
  background: #fff3cd;
  color: #856404;
}

.history-status.processing {
  background: #cce5ff;
  color: #004085;
}

/* 按钮样式 */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
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

.btn-sm {
  padding: 0.25rem 0.75rem;
  font-size: 0.85rem;
}

.btn-xs {
  padding: 0.125rem 0.5rem;
  font-size: 0.75rem;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

.btn-outline {
  background: transparent;
  color: #6c757d;
  border: 1px solid #6c757d;
}

.btn-outline:hover:not(:disabled) {
  background: #6c757d;
  color: white;
}

.btn-icon {
  font-size: 1rem;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .workspace-main {
    flex-direction: column;
  }

  .research-panel {
    border-right: none;
    border-bottom: 1px solid #e9ecef;
    height: 400px;
  }

  .results-panel {
    width: 100%;
    height: 300px;
    min-width: auto;
    border-left: none;
  }

  .history-sidebar {
    width: 100%;
    height: 200px;
    border-left: none;
    border-top: 1px solid #e9ecef;
  }
}

@media (max-width: 768px) {
  .workspace-header {
    padding: 1rem;
  }

  .header-left h2 {
    font-size: 1.5rem;
  }

  .header-left p {
    font-size: 0.9rem;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .research-panel {
    height: 350px;
  }

  .results-panel {
    height: 250px;
  }

  .history-sidebar {
    height: 150px;
  }

  .form-actions {
    flex-direction: column;
  }
}

@media (max-width: 480px) {
  .workspace-header {
    padding: 0.75rem;
    flex-direction: column;
    gap: 0.75rem;
    align-items: stretch;
  }

  .panel-controls {
    flex-wrap: wrap;
  }

  .research-form {
    padding: 1rem;
  }

  .checkbox-group {
    flex-direction: column;
    gap: 0.5rem;
  }

  .tab-btn {
    padding: 0.5rem 0.75rem;
    font-size: 0.85rem;
  }

  .tab-count {
    display: none;
  }
}
</style>