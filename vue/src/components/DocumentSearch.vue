<template>
  <div class="document-search">
    <div class="search-header">
      <h3 class="search-title">
        <i class="icon-search"></i>
        文档搜索
      </h3>
      <div class="search-controls">
        <div class="search-input-wrapper">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="输入搜索关键词..."
            @keyup.enter="performSearch"
            class="search-input"
          />
          <button
            class="btn-search"
            @click="performSearch"
            :disabled="!searchQuery.trim() || searching"
          >
            <i class="icon-search"></i>
          </button>
        </div>
        <div class="search-options">
          <label class="option-item">
            <input
              type="checkbox"
              v-model="includeEvidence"
            />
            包含证据链
          </label>
          <label class="option-item">
            <input
              type="checkbox"
              v-model="exactMatch"
            />
            精确匹配
          </label>
        </div>
      </div>
    </div>

    <!-- 搜索结果 -->
    <div v-if="searchResults.length > 0" class="search-results">
      <div class="results-header">
        <h4>搜索结果 ({{ searchResults.length }})</h4>
        <div class="results-meta">
          <span>耗时: {{ searchDuration }}ms</span>
          <span>总计: {{ totalResults }}</span>
        </div>
      </div>

      <div class="results-list">
        <div
          v-for="result in searchResults"
          :key="result.chunk_id"
          class="result-item"
          @click="selectResult(result)"
        >
          <div class="result-header">
            <div class="result-source">
              <i :class="getFileIcon(result.filename)"></i>
              <span class="filename">{{ result.filename }}</span>
            </div>
            <div class="result-score">
              <span class="score-badge" :class="getScoreClass(result.score)">
                {{ (result.score * 100).toFixed(1) }}%
              </span>
            </div>
          </div>

          <div class="result-content">
            <div class="result-snippet">
              {{ result.snippet }}
            </div>
            <div v-if="result.content && result.content !== result.snippet" class="result-preview">
              {{ getPreviewText(result.content, result.snippet) }}
            </div>
          </div>

          <div class="result-meta">
            <div class="meta-item">
              <i class="icon-document"></i>
              分块 #{{ result.chunk_index || 'N/A' }}
            </div>
            <div class="meta-item" v-if="result.citation_id">
              <i class="icon-link"></i>
              引用: {{ result.citation_id }}
            </div>
            <div class="meta-item" v-if="result.source_url">
              <a :href="result.source_url" target="_blank" rel="noopener noreferrer">
                <i class="icon-external-link"></i>
                查看来源
              </a>
            </div>
          </div>

          <div class="result-actions">
            <button class="btn-preview" @click.stop="previewDocument(result)">
              <i class="icon-eye"></i>
              预览
            </button>
            <button class="btn-quote" @click.stop="quoteResult(result)">
              <i class="icon-quote"></i>
              引用
            </button>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="totalPages > 1" class="pagination">
        <button
          class="page-btn"
          :disabled="currentPage === 1"
          @click="changePage(currentPage - 1)"
        >
          <i class="icon-chevron-left"></i>
        </button>

        <span class="page-info">
          第 {{ currentPage }} 页，共 {{ totalPages }} 页
        </span>

        <button
          class="page-btn"
          :disabled="currentPage === totalPages"
          @click="changePage(currentPage + 1)"
        >
          <i class="icon-chevron-right"></i>
        </button>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="searched && !searching" class="no-results">
      <i class="icon-empty"></i>
      <h3>没有找到相关结果</h3>
      <p>尝试调整搜索关键词或搜索选项</p>
      <div class="search-tips">
        <h4>搜索提示：</h4>
        <ul>
          <li>使用更具体的关键词</li>
          <li>尝试同义词或相关术语</li>
          <li>减少搜索词的数量</li>
          <li>检查拼写是否正确</li>
        </ul>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-else-if="searching" class="searching">
      <div class="spinner"></div>
      <p>正在搜索中...</p>
    </div>

    <!-- 相关证据 -->
    <div v-if="relatedEvidence.length > 0" class="related-evidence">
      <h4 class="evidence-title">
        <i class="icon-link"></i>
        相关证据 ({{ relatedEvidence.length }})
      </h4>

      <div class="evidence-list">
        <div
          v-for="evidence in relatedEvidence"
          :key="evidence.id"
          class="evidence-item"
          :class="{ verified: evidence.verified_by_user }"
        >
          <div class="evidence-header">
            <span class="evidence-type">{{ getEvidenceTypeLabel(evidence.source_type) }}</span>
            <span class="evidence-score">置信度: {{ (evidence.confidence_score * 100).toFixed(1) }}%</span>
          </div>
          <div class="evidence-content">
            {{ evidence.snippet }}
          </div>
          <div class="evidence-actions">
            <button class="btn-view-evidence" @click="viewEvidence(evidence)">
              查看详情
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ragAPI, evidenceAPI } from '@/services/api.js'

// Props
const props = defineProps({
  conversationId: {
    type: String,
    default: null
  }
})

// Emits
const emit = defineEmits(['result-selected', 'evidence-viewed'])

// Reactive data
const searchQuery = ref('')
const includeEvidence = ref(true)
const exactMatch = ref(false)
const searching = ref(false)
const searched = ref(false)
const searchResults = ref([])
const relatedEvidence = ref([])
const searchDuration = ref(0)
const totalResults = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

// Computed
const totalPages = computed(() => {
  return Math.ceil(totalResults.value / pageSize.value)
})

// Methods
const getFileIcon = (filename) => {
  const ext = filename.split('.').pop().toLowerCase()
  const icons = {
    pdf: 'icon-pdf',
    docx: 'icon-word',
    doc: 'icon-word',
    txt: 'icon-text',
    md: 'icon-markdown'
  }
  return icons[ext] || 'icon-file'
}

const getScoreClass = (score) => {
  if (score >= 0.8) return 'high'
  if (score >= 0.6) return 'medium'
  return 'low'
}

const getEvidenceTypeLabel = (type) => {
  const labels = {
    document: '文档',
    web: '网页',
    api: 'API',
    search: '搜索'
  }
  return labels[type] || type
}

const getPreviewText = (content, snippet) => {
  // 从完整内容中提取snippet周围的文本作为预览
  const snippetIndex = content.indexOf(snippet)
  if (snippetIndex === -1) return ''

  const start = Math.max(0, snippetIndex - 100)
  const end = Math.min(content.length, snippetIndex + snippet.length + 100)
  const preview = content.substring(start, end)

  return preview.replace(snippet, `**${snippet}**`)
}

const performSearch = async () => {
  if (!searchQuery.value.trim()) return

  console.log('开始搜索:', searchQuery.value)
  searching.value = true
  searched.value = true
  const startTime = Date.now()

  try {
    // 执行文档搜索
    const searchParams = new URLSearchParams({
      query: searchQuery.value,
      limit: pageSize.value.toString(),
      offset: ((currentPage.value - 1) * pageSize.value).toString()
    })

    if (exactMatch.value) {
      searchParams.append('exact_match', 'true')
    }

    const searchResponse = await fetch(`/api/rag/search?${searchParams}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (!searchResponse.ok) {
      throw new Error(`搜索失败: ${searchResponse.status}`)
    }

    const searchData = await searchResponse.json()
    console.log('搜索结果:', searchData)
    searchResults.value = searchData.results || []
    totalResults.value = searchData.total || 0

    // 如果需要包含证据链，获取相关证据
    if (includeEvidence.value && searchResults.value.length > 0) {
      console.log('加载相关证据...')
      await loadRelatedEvidence()
    }

  } catch (error) {
    console.error('搜索失败:', error)
    searchResults.value = []
    totalResults.value = 0
  } finally {
    searching.value = false
    searchDuration.value = Date.now() - startTime
  }
}

const loadRelatedEvidence = async () => {
  try {
    // 这里可以根据搜索结果获取相关的证据链
    // 暂时使用固定的证据数据作为示例
    relatedEvidence.value = []
  } catch (error) {
    console.error('加载相关证据失败:', error)
  }
}

const selectResult = (result) => {
  emit('result-selected', result)
}

const previewDocument = (result) => {
  // 实现文档预览功能
  console.log('预览文档:', result)
  // 可以打开模态框显示文档内容
}

const quoteResult = (result) => {
  // 实现引用功能
  const quote = {
    text: result.snippet,
    source: result.filename,
    citationId: result.citation_id,
    url: result.source_url
  }
  emit('result-selected', quote)
}

const viewEvidence = (evidence) => {
  emit('evidence-viewed', evidence)
}

const changePage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    performSearch()
  }
}

// 监听搜索查询变化
watch(searchQuery, () => {
  if (searched.value) {
    currentPage.value = 1
  }
})
</script>

<style scoped>
.document-search {
  background: var(--primary-bg);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.search-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  background: var(--secondary-bg);
}

.search-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.search-controls {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.search-input-wrapper {
  display: flex;
  gap: 8px;
}

.search-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--primary-bg);
  color: var(--text-primary);
  font-size: 14px;
}

.search-input:focus {
  outline: none;
  border-color: var(--accent-color);
}

.btn-search {
  padding: 8px 12px;
  border: 1px solid var(--accent-color);
  border-radius: 6px;
  background: var(--accent-color);
  color: white;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-search:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn-search:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.search-options {
  display: flex;
  gap: 16px;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
}

.search-results {
  padding: 20px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.results-header h4 {
  margin: 0;
  font-size: 14px;
  color: var(--text-primary);
}

.results-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--text-secondary);
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;
}

.result-item {
  background: var(--secondary-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.result-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-color: var(--accent-color);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.result-source {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.filename {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-score .score-badge {
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 600;
}

.score-badge.high {
  background: var(--success-color);
  color: white;
}

.score-badge.medium {
  background: var(--warning-color);
  color: white;
}

.score-badge.low {
  background: var(--error-color);
  color: white;
}

.result-content {
  margin-bottom: 12px;
}

.result-snippet {
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.result-preview {
  font-size: 13px;
  color: var(--text-secondary);
  font-style: italic;
  border-left: 2px solid var(--accent-color);
  padding-left: 8px;
}

.result-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 12px;
  color: var(--text-secondary);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.meta-item a {
  color: var(--accent-color);
  text-decoration: none;
}

.meta-item a:hover {
  text-decoration: underline;
}

.result-actions {
  display: flex;
  gap: 8px;
}

.btn-preview, .btn-quote {
  padding: 4px 8px;
  border: 1px solid var(--border-color);
  border-radius: 3px;
  background: var(--primary-bg);
  color: var(--text-primary);
  cursor: pointer;
  font-size: 11px;
  transition: all 0.2s;
}

.btn-preview:hover, .btn-quote:hover {
  background: var(--hover-bg);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  padding: 16px 0;
  border-top: 1px solid var(--border-color);
}

.page-btn {
  padding: 6px 8px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--primary-bg);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  background: var(--hover-bg);
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 12px;
  color: var(--text-secondary);
}

.no-results {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}

.no-results i {
  font-size: 64px;
  margin-bottom: 20px;
  opacity: 0.5;
}

.no-results h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: var(--text-primary);
}

.no-results p {
  margin: 0 0 20px 0;
  font-size: 14px;
}

.search-tips {
  text-align: left;
  max-width: 300px;
  margin: 0 auto;
}

.search-tips h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: var(--text-primary);
}

.search-tips ul {
  margin: 0;
  padding-left: 20px;
}

.search-tips li {
  font-size: 12px;
  margin-bottom: 4px;
}

.searching {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-color);
  border-top: 3px solid var(--accent-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.related-evidence {
  padding: 20px;
  border-top: 1px solid var(--border-color);
  background: var(--secondary-bg);
}

.evidence-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.evidence-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.evidence-item {
  background: var(--primary-bg);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 12px;
}

.evidence-item.verified {
  border-left: 3px solid var(--success-color);
}

.evidence-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
}

.evidence-type {
  background: var(--accent-color);
  color: white;
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 500;
}

.evidence-score {
  color: var(--text-secondary);
  font-weight: 500;
}

.evidence-content {
  font-size: 13px;
  color: var(--text-primary);
  margin-bottom: 8px;
  line-height: 1.4;
}

.evidence-actions {
  text-align: right;
}

.btn-view-evidence {
  padding: 4px 8px;
  border: 1px solid var(--accent-color);
  border-radius: 3px;
  background: var(--accent-color);
  color: white;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-view-evidence:hover {
  background: var(--accent-hover);
}
</style>
