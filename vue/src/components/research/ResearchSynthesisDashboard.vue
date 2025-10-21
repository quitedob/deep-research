<template>
  <div class="research-synthesis-dashboard">
    <!-- Header -->
    <div class="dashboard-header">
      <h2 class="text-2xl font-bold text-gray-900 mb-2">Research Synthesis Dashboard</h2>
      <p class="text-gray-600">Comprehensive synthesis and analysis of research findings and insights</p>
    </div>

    <!-- Synthesis Controls -->
    <div class="synthesis-controls bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-semibold text-gray-900">Synthesis Control Panel</h3>
        <div class="flex space-x-2">
          <button
            @click="generateSynthesis"
            :disabled="isGeneratingSynthesis"
            class="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            <span v-if="isGeneratingSynthesis" class="flex items-center">
              <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Generating...
            </span>
            <span v-else>Generate Synthesis</span>
          </button>
          <button
            @click="exportSynthesis"
            :disabled="!currentSynthesis"
            class="px-4 py-2 text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50 transition-colors"
          >
            Export Report
          </button>
          <button
            @click="shareSynthesis"
            :disabled="!currentSynthesis"
            class="px-4 py-2 text-white bg-purple-600 rounded-md hover:bg-purple-700 disabled:opacity-50 transition-colors"
          >
            Share
          </button>
        </div>
      </div>

      <!-- Synthesis Configuration -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Synthesis Type
          </label>
          <select
            v-model="synthesisConfig.type"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="comprehensive">Comprehensive</option>
            <option value="thematic">Thematic</option>
            <option value="comparative">Comparative</option>
            <option value="analytical">Analytical</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Target Audience
          </label>
          <select
            v-model="synthesisConfig.targetAudience"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="general">General</option>
            <option value="academic">Academic</option>
            <option value="business">Business</option>
            <option value="technical">Technical</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Focus Areas
          </label>
          <input
            v-model="synthesisConfig.focusAreas"
            type="text"
            placeholder="Enter focus areas"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Detail Level
          </label>
          <select
            v-model="synthesisConfig.detailLevel"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="summary">Summary</option>
            <option value="detailed">Detailed</option>
            <option value="comprehensive">Comprehensive</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Synthesis Overview -->
    <div v-if="currentSynthesis" class="synthesis-overview bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
      <div class="border-b border-gray-200 p-6">
        <div class="flex justify-between items-start">
          <div>
            <h3 class="text-lg font-semibold text-gray-900">{{ currentSynthesis.title }}</h3>
            <p class="text-gray-600 mt-1">{{ currentSynthesis.description }}</p>
            <div class="flex items-center space-x-4 mt-3">
              <span class="text-sm text-gray-500">
                Generated: {{ formatDate(currentSynthesis.generated_at) }}
              </span>
              <span class="text-sm text-gray-500">
                Confidence: {{ Math.round(currentSynthesis.confidence_level * 100) }}%
              </span>
              <span class="text-sm text-gray-500">
                Quality Score: {{ Math.round(currentSynthesis.quality_score * 100) }}%
              </span>
            </div>
          </div>
          <div class="flex space-x-2">
            <button
              @click="viewSynthesisDetails"
              class="px-3 py-1 text-sm text-blue-600 bg-blue-50 rounded hover:bg-blue-100 transition-colors"
            >
              Full View
            </button>
            <button
              @click="regenerateSynthesis"
              :disabled="isGeneratingSynthesis"
              class="px-3 py-1 text-sm text-gray-700 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
            >
              Regenerate
            </button>
          </div>
        </div>
      </div>

      <div class="p-6">
        <!-- Executive Summary -->
        <div v-if="currentSynthesis.executive_summary" class="mb-6">
          <h4 class="font-medium text-gray-900 mb-3">Executive Summary</h4>
          <div class="p-4 bg-blue-50 rounded-lg border border-blue-200">
            <p class="text-gray-700">{{ currentSynthesis.executive_summary }}</p>
          </div>
        </div>

        <!-- Key Metrics -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="text-center">
              <div class="text-2xl font-bold text-gray-900">{{ currentSynthesis.sources_analyzed }}</div>
              <div class="text-sm text-gray-600 mt-1">Sources Analyzed</div>
            </div>
          </div>
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="text-center">
              <div class="text-2xl font-bold text-gray-900">{{ currentSynthesis.key_insights.length }}</div>
              <div class="text-sm text-gray-600 mt-1">Key Insights</div>
            </div>
          </div>
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="text-center">
              <div class="text-2xl font-bold text-gray-900">{{ currentSynthesis.recommendations.length }}</div>
              <div class="text-sm text-gray-600 mt-1">Recommendations</div>
            </div>
          </div>
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="text-center">
              <div class="text-2xl font-bold text-gray-900">{{ currentSynthesis.themes.length }}</div>
              <div class="text-sm text-gray-600 mt-1">Themes Identified</div>
            </div>
          </div>
        </div>

        <!-- Progress Indicators -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <div class="flex justify-between text-sm mb-1">
              <span class="text-gray-600">Data Quality</span>
              <span class="font-medium">{{ Math.round(currentSynthesis.data_quality * 100) }}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div
                class="bg-green-600 h-2 rounded-full transition-all duration-300"
                :style="{ width: `${currentSynthesis.data_quality * 100}%` }"
              ></div>
            </div>
          </div>
          <div>
            <div class="flex justify-between text-sm mb-1">
              <span class="text-gray-600">Coverage</span>
              <span class="font-medium">{{ Math.round(currentSynthesis.coverage_score * 100) }}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div
                class="bg-blue-600 h-2 rounded-full transition-all duration-300"
                :style="{ width: `${currentSynthesis.coverage_score * 100}%` }"
              ></div>
            </div>
          </div>
          <div>
            <div class="flex justify-between text-sm mb-1">
              <span class="text-gray-600">Reliability</span>
              <span class="font-medium">{{ Math.round(currentSynthesis.reliability_score * 100) }}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div
                class="bg-purple-600 h-2 rounded-full transition-all duration-300"
                :style="{ width: `${currentSynthesis.reliability_score * 100}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Key Insights Section -->
    <div class="key-insights bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
      <div class="border-b border-gray-200 p-6">
        <div class="flex justify-between items-center">
          <h3 class="text-lg font-semibold text-gray-900">Key Insights</h3>
          <div class="flex space-x-2">
            <button
              @click="insightView = 'cards'"
              :class="insightView === 'cards' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'"
              class="px-3 py-1 text-sm rounded-md transition-colors"
            >
              Cards
            </button>
            <button
              @click="insightView = 'list'"
              :class="insightView === 'list' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'"
              class="px-3 py-1 text-sm rounded-md transition-colors"
            >
              List
            </button>
            <button
              @click="insightView = 'graph'"
              :class="insightView === 'graph' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'"
              class="px-3 py-1 text-sm rounded-md transition-colors"
            >
              Graph
            </button>
          </div>
        </div>
      </div>

      <div class="p-6">
        <!-- Cards View -->
        <div v-if="insightView === 'cards'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v="(insight, index) in currentSynthesis?.key_insights || []"
            :key="index"
            class="insight-card border rounded-lg p-4 hover:shadow-md transition-shadow"
            :class="getInsightCardClass(insight.type)"
          >
            <div class="flex items-start justify-between mb-3">
              <div class="insight-icon w-10 h-10 rounded-full flex items-center justify-center"
                   :class="getInsightIconClass(insight.type)">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getInsightIcon(insight.type)"></path>
                </svg>
              </div>
              <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                    :class="getInsightTypeClass(insight.type)">
                {{ insight.type }}
              </span>
            </div>
            <h5 class="font-medium text-gray-900 mb-2">{{ insight.title }}</h5>
            <p class="text-sm text-gray-600 mb-3">{{ insight.description }}</p>
            <div class="flex items-center justify-between text-xs text-gray-500">
              <span>Confidence: {{ Math.round(insight.confidence * 100) }}%</span>
              <span>Impact: {{ insight.impact }}</span>
            </div>
          </div>
        </div>

        <!-- List View -->
        <div v-else-if="insightView === 'list'" class="space-y-4">
          <div
            v="(insight, index) in currentSynthesis?.key_insights || []"
            :key="index"
            class="insight-item border-l-4 pl-4 py-3 hover:bg-gray-50 transition-colors"
            :class="getInsightItemClass(insight.type)"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <div class="flex items-center space-x-3 mb-2">
                  <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                        :class="getInsightTypeClass(insight.type)">
                    {{ insight.type }}
                  </span>
                  <h5 class="font-medium text-gray-900">{{ insight.title }}</h5>
                </div>
                <p class="text-sm text-gray-600">{{ insight.description }}</p>
                <div class="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                  <span>Confidence: {{ Math.round(insight.confidence * 100) }}%</span>
                  <span>Impact: {{ insight.impact }}</span>
                  <span>Evidence: {{ insight.evidence_count }} sources</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Graph View -->
        <div v-else-if="insightView === 'graph'" class="h-96 bg-gray-50 rounded-lg flex items-center justify-center">
          <div class="text-center">
            <svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
            </svg>
            <p class="text-gray-500">Insight relationship graph</p>
            <p class="text-sm text-gray-400 mt-1">Visual mapping of insights and their connections</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Themes Analysis -->
    <div class="themes-analysis bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
      <div class="border-b border-gray-200 p-6">
        <h3 class="text-lg font-semibold text-gray-900">Themes Analysis</h3>
      </div>

      <div class="p-6">
        <div v-if="currentSynthesis?.themes && currentSynthesis.themes.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 class="font-medium text-gray-900 mb-4">Theme Distribution</h4>
            <div class="space-y-3">
              <div
                v="theme in currentSynthesis.themes"
                :key="theme.name"
                class="theme-bar"
              >
                <div class="flex justify-between text-sm mb-1">
                  <span class="font-medium">{{ theme.name }}</span>
                  <span>{{ theme.frequency }} occurrences</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                  <div
                    class="h-2 rounded-full transition-all duration-300"
                    :class="getThemeBarClass(theme.strength)"
                    :style="{ width: `${(theme.frequency / Math.max(...currentSynthesis.themes.map(t => t.frequency))) * 100}%` }"
                  ></div>
                </div>
                <p class="text-xs text-gray-600 mt-1">{{ theme.description }}</p>
              </div>
            </div>
          </div>

          <div>
            <h4 class="font-medium text-gray-900 mb-4">Theme Relationships</h4>
            <div class="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
              <div class="text-center">
                <svg class="w-12 h-12 text-gray-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                </svg>
                <p class="text-gray-500">Theme relationship network</p>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-8">
          <svg class="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
            </svg>
          <p class="text-gray-500">No themes identified yet</p>
        </div>
      </div>
    </div>

    <!-- Recommendations -->
    <div class="recommendations bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
      <div class="border-b border-gray-200 p-6">
        <h3 class="text-lg font-semibold text-gray-900">Evidence-Based Recommendations</h3>
      </div>

      <div class="p-6">
        <div v-if="currentSynthesis?.recommendations && currentSynthesis.recommendations.length > 0" class="space-y-4">
          <div
            v="(recommendation, index) in currentSynthesis.recommendations"
            :key="index"
            class="recommendation-item border rounded-lg p-4"
            :class="getRecommendationClass(recommendation.priority)"
          >
            <div class="flex items-start justify-between mb-3">
              <div class="flex items-center space-x-3">
                <div class="recommendation-number w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium text-white"
                     :class="getRecommendationNumberClass(recommendation.priority)">
                  {{ index + 1 }}
                </div>
                <div>
                  <h5 class="font-medium text-gray-900">{{ recommendation.title }}</h5>
                  <p class="text-sm text-gray-600 mt-1">{{ recommendation.description }}</p>
                </div>
              </div>
              <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                    :class="getPriorityClass(recommendation.priority)">
                {{ recommendation.priority }}
              </span>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span class="text-gray-600">Impact:</span>
                <span class="ml-1 font-medium">{{ recommendation.impact }}</span>
              </div>
              <div>
                <span class="text-gray-600">Effort:</span>
                <span class="ml-1 font-medium">{{ recommendation.effort }}</span>
              </div>
              <div>
                <span class="text-gray-600">Evidence Support:</span>
                <span class="ml-1 font-medium">{{ Math.round(recommendation.evidence_support * 100) }}%</span>
              </div>
            </div>

            <div v-if="recommendation.action_steps" class="mt-4">
              <h6 class="text-sm font-medium text-gray-900 mb-2">Action Steps:</h6>
              <ul class="text-sm text-gray-600 space-y-1">
                <li v="(step, stepIndex) in recommendation.action_steps" :key="stepIndex" class="flex items-start space-x-2">
                  <span class="text-gray-400 mt-1">•</span>
                  <span>{{ step }}</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-8">
          <svg class="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
          </svg>
          <p class="text-gray-500">No recommendations available yet</p>
        </div>
      </div>
    </div>

    <!-- Conclusions -->
    <div class="conclusions bg-white rounded-lg shadow-sm border border-gray-200">
      <div class="border-b border-gray-200 p-6">
        <h3 class="text-lg font-semibold text-gray-900">Research Conclusions</h3>
      </div>

      <div class="p-6">
        <div v-if="currentSynthesis?.conclusions && currentSynthesis.conclusions.length > 0" class="space-y-4">
          <div
            v="(conclusion, index) in currentSynthesis.conclusions"
            :key="index"
            class="conclusion-item p-4 bg-gray-50 rounded-lg"
          >
            <h5 class="font-medium text-gray-900 mb-2">{{ conclusion.title }}</h5>
            <p class="text-sm text-gray-700 mb-3">{{ conclusion.statement }}</p>
            <div class="flex items-center justify-between text-xs text-gray-500">
              <span>Confidence: {{ Math.round(conclusion.confidence * 100) }}%</span>
              <span>Evidence Support: {{ conclusion.supporting_evidence.length }} items</span>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-8">
          <svg class="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          <p class="text-gray-500">No conclusions formulated yet</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useResearchStore } from '@/stores/research'
import { useNotificationStore } from '@/stores/notification'

export default {
  name: 'ResearchSynthesisDashboard',
  setup() {
    const researchStore = useResearchStore()
    const notificationStore = useNotificationStore()

    // Reactive data
    const isGeneratingSynthesis = ref(false)
    const insightView = ref('cards')
    const currentSynthesis = ref(null)

    const synthesisConfig = ref({
      type: 'comprehensive',
      targetAudience: 'general',
      focusAreas: '',
      detailLevel: 'detailed'
    })

    // Computed properties
    const hasSynthesis = computed(() => currentSynthesis.value !== null)

    // Methods
    const generateSynthesis = async () => {
      if (!researchStore.currentPlan) {
        notificationStore.showError('No active research plan found')
        return
      }

      isGeneratingSynthesis.value = true
      try {
        // Prepare synthesis data
        const synthesisData = {
          plan_id: researchStore.currentPlan.id,
          synthesis_type: synthesisConfig.value.type,
          target_audience: synthesisConfig.value.targetAudience,
          focus_areas: synthesisConfig.value.focusAreas.split(',').map(s => s.trim()).filter(s => s),
          detail_level: synthesisConfig.value.detailLevel,
          include_insights: true,
          include_recommendations: true,
          include_conclusions: true
        }

        // Generate synthesis (this would call the actual API)
        const synthesis = await mockGenerateSynthesis(synthesisData)
        currentSynthesis.value = synthesis

        notificationStore.showSuccess('Research synthesis generated successfully')
      } catch (error) {
        console.error('Failed to generate synthesis:', error)
        notificationStore.showError(`Failed to generate synthesis: ${error.message}`)
      } finally {
        isGeneratingSynthesis.value = false
      }
    }

    const regenerateSynthesis = () => {
      generateSynthesis()
    }

    const viewSynthesisDetails = () => {
      // Open full synthesis view modal
      notificationStore.showInfo('Full synthesis view coming soon')
    }

    const exportSynthesis = () => {
      if (!currentSynthesis.value) return

      try {
        const data = {
          synthesis: currentSynthesis.value,
          config: synthesisConfig.value,
          exportDate: new Date().toISOString()
        }

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `research-synthesis-${new Date().toISOString().split('T')[0]}.json`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)

        notificationStore.showSuccess('Synthesis exported successfully')
      } catch (error) {
        notificationStore.showError(`Failed to export synthesis: ${error.message}`)
      }
    }

    const shareSynthesis = () => {
      // Implement sharing functionality
      notificationStore.showInfo('Sharing functionality coming soon')
    }

    // Mock function to generate synthesis data
    const mockGenerateSynthesis = async (config) => {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 2000))

      return {
        id: `synthesis_${Date.now()}`,
        title: `Research Synthesis - ${config.synthesis_type}`,
        description: `Comprehensive synthesis of research findings with ${config.detail_level} detail level`,
        generated_at: new Date().toISOString(),
        confidence_level: 0.85,
        quality_score: 0.88,
        data_quality: 0.82,
        coverage_score: 0.90,
        reliability_score: 0.86,
        sources_analyzed: 15,
        themes: [
          {
            name: 'Innovation',
            frequency: 8,
            strength: 'high',
            description: 'Emerging trends and innovative approaches in the research domain'
          },
          {
            name: 'Methodology',
            frequency: 6,
            strength: 'medium',
            description: 'Research methods and analytical approaches used'
          },
          {
            name: 'Impact',
            frequency: 5,
            strength: 'high',
            description: 'Significant findings and their potential impact'
          }
        ],
        key_insights: [
          {
            type: 'strategic',
            title: 'Emerging Market Opportunities',
            description: 'Research indicates significant untapped potential in emerging markets with projected growth rates exceeding 25% annually.',
            confidence: 0.9,
            impact: 'high',
            evidence_count: 7
          },
          {
            type: 'operational',
            title: 'Process Optimization Potential',
            description: 'Current processes show 30% inefficiency that can be addressed through targeted improvements.',
            confidence: 0.85,
            impact: 'medium',
            evidence_count: 5
          },
          {
            type: 'predictive',
            title: 'Technology Adoption Forecast',
            description: 'Based on current trends, key technologies will reach mainstream adoption within 18-24 months.',
            confidence: 0.75,
            impact: 'high',
            evidence_count: 6
          }
        ],
        recommendations: [
          {
            title: 'Market Entry Strategy',
            description: 'Develop a phased market entry strategy focusing on high-potential segments identified in the research.',
            priority: 'high',
            impact: 'High',
            effort: 'Medium',
            evidence_support: 0.88,
            action_steps: [
              'Conduct detailed market analysis for target segments',
              'Develop tailored value propositions for each segment',
              'Create implementation timeline with milestones',
              'Establish metrics for success measurement'
            ]
          },
          {
            title: 'Process Improvement Initiative',
            description: 'Implement process optimization based on identified inefficiencies and best practices.',
            priority: 'medium',
            impact: 'Medium',
            effort: 'Low',
            evidence_support: 0.82,
            action_steps: [
              'Map current processes and identify bottlenecks',
              'Implement automation where appropriate',
              'Train staff on new procedures',
              'Monitor and measure improvements'
            ]
          }
        ],
        conclusions: [
          {
            title: 'Market Opportunity Validation',
            statement: 'The research validates significant market opportunities in emerging segments with strong evidence supporting the potential for substantial growth and profitability.',
            confidence: 0.92,
            supporting_evidence: ['evidence_1', 'evidence_2', 'evidence_3']
          },
          {
            title: 'Operational Efficiency Gains',
            statement: 'Clear evidence supports the potential for significant operational efficiency improvements through targeted process optimization and technology adoption.',
            confidence: 0.85,
            supporting_evidence: ['evidence_4', 'evidence_5']
          }
        ]
      }
    }

    // Helper methods
    const getInsightCardClass = (type) => {
      const classes = {
        'strategic': 'border-blue-200 bg-blue-50',
        'operational': 'border-green-200 bg-green-50',
        'predictive': 'border-purple-200 bg-purple-50'
      }
      return classes[type] || 'border-gray-200 bg-gray-50'
    }

    const getInsightIconClass = (type) => {
      const classes = {
        'strategic': 'bg-blue-600',
        'operational': 'bg-green-600',
        'predictive': 'bg-purple-600'
      }
      return classes[type] || 'bg-gray-600'
    }

    const getInsightTypeClass = (type) => {
      const classes = {
        'strategic': 'bg-blue-100 text-blue-800',
        'operational': 'bg-green-100 text-green-800',
        'predictive': 'bg-purple-100 text-purple-800'
      }
      return classes[type] || 'bg-gray-100 text-gray-800'
    }

    const getInsightItemClass = (type) => {
      const classes = {
        'strategic': 'border-blue-500 bg-blue-50',
        'operational': 'border-green-500 bg-green-50',
        'predictive': 'border-purple-500 bg-purple-50'
      }
      return classes[type] || 'border-gray-500 bg-gray-50'
    }

    const getInsightIcon = (type) => {
      const icons = {
        'strategic': 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
        'operational': 'M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4',
        'predictive': 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6'
      }
      return icons[type] || icons.strategic
    }

    const getThemeBarClass = (strength) => {
      const classes = {
        'high': 'bg-green-600',
        'medium': 'bg-yellow-600',
        'low': 'bg-red-600'
      }
      return classes[strength] || 'bg-gray-600'
    }

    const getRecommendationClass = (priority) => {
      const classes = {
        'high': 'border-red-200 bg-red-50',
        'medium': 'border-yellow-200 bg-yellow-50',
        'low': 'border-green-200 bg-green-50'
      }
      return classes[priority] || 'border-gray-200 bg-gray-50'
    }

    const getRecommendationNumberClass = (priority) => {
      const classes = {
        'high': 'bg-red-600',
        'medium': 'bg-yellow-600',
        'low': 'bg-green-600'
      }
      return classes[priority] || 'bg-gray-600'
    }

    const getPriorityClass = (priority) => {
      const classes = {
        'high': 'bg-red-100 text-red-800',
        'medium': 'bg-yellow-100 text-yellow-800',
        'low': 'bg-green-100 text-green-800'
      }
      return classes[priority] || 'bg-gray-100 text-gray-800'
    }

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      return new Date(dateString).toLocaleDateString() + ' ' + new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }

    // Lifecycle
    onMounted(() => {
      // Load existing synthesis if available
      if (researchStore.currentPlan) {
        // Could load previous synthesis here
      }
    })

    return {
      // Data
      isGeneratingSynthesis,
      insightView,
      currentSynthesis,
      synthesisConfig,

      // Computed
      hasSynthesis,

      // Methods
      generateSynthesis,
      regenerateSynthesis,
      viewSynthesisDetails,
      exportSynthesis,
      shareSynthesis,
      getInsightCardClass,
      getInsightIconClass,
      getInsightTypeClass,
      getInsightItemClass,
      getInsightIcon,
      getThemeBarClass,
      getRecommendationClass,
      getRecommendationNumberClass,
      getPriorityClass,
      formatDate
    }
  }
}
</script>

<style scoped>
.research-synthesis-dashboard {
  max-width: 7xl;
  margin: 0 auto;
  padding: 1rem;
}

.insight-card {
  transition: all 0.2s ease;
}

.insight-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.insight-item {
  transition: background-color 0.2s ease;
}

.recommendation-item {
  transition: all 0.2s ease;
}

.recommendation-item:hover {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Progress bars animation */
.transition-all {
  transition: all 0.3s ease;
}

/* Spin animation */
.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>