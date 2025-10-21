<template>
  <div class="evidence-chain-visualization">
    <!-- Header -->
    <div class="visualization-header">
      <h2 class="text-2xl font-bold text-gray-900 mb-2">Evidence Chain Analysis</h2>
      <p class="text-gray-600">Visualize and analyze evidence relationships and quality</p>
    </div>

    <!-- Evidence Chain Controls -->
    <div class="evidence-controls bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-semibold text-gray-900">Evidence Chain Management</h3>
        <div class="flex space-x-2">
          <button
            @click="refreshEvidenceChain"
            :disabled="isLoading"
            class="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            <span v-if="isLoading" class="flex items-center">
              <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Refreshing...
            </span>
            <span v-else>Refresh</span>
          </button>
          <button
            @click="analyzeEvidenceChain"
            :disabled="!currentChain || isAnalyzing"
            class="px-4 py-2 text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50 transition-colors"
          >
            <span v-if="isAnalyzing" class="flex items-center">
              <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Analyzing...
            </span>
            <span v-else>Analyze</span>
            </button>
          <button
            @click="exportEvidenceChain"
            :disabled="!currentChain"
            class="px-4 py-2 text-white bg-purple-600 rounded-md hover:bg-purple-700 disabled:opacity-50 transition-colors"
          >
            Export
          </button>
        </div>
      </div>

      <!-- Filter Controls -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Evidence Type
          </label>
          <select
            v-model="filters.evidenceType"
            @change="applyFilters"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Types</option>
            <option value="web_source">Web Source</option>
            <option value="academic_paper">Academic Paper</option>
            <option value="book">Book</option>
            <option value="documentation">Documentation</option>
            <option value="interview">Interview</option>
            <option value="survey">Survey</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Quality Level
          </label>
          <select
            v-model="filters.qualityLevel"
            @change="applyFilters"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Qualities</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Confidence Threshold
          </label>
          <input
            v-model.number="filters.confidenceThreshold"
            type="range"
            min="0"
            max="1"
            step="0.1"
            @input="applyFilters"
            class="w-full"
          />
          <div class="text-xs text-gray-600 text-center">{{ filters.confidenceThreshold.toFixed(1) }}</div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            View Mode
          </label>
          <select
            v-model="viewMode"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="network">Network Graph</option>
            <option value="timeline">Timeline</option>
            <option value="quality">Quality Analysis</option>
            <option value="relationships">Relationship Map</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Evidence Chain Summary -->
    <div v-if="currentChain" class="evidence-summary bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
      <div class="border-b border-gray-200 p-6">
        <h3 class="text-lg font-semibold text-gray-900">{{ currentChain.title }}</h3>
        <p class="text-gray-600 mt-1">{{ currentChain.description }}</p>
      </div>

      <div class="p-6">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div class="bg-blue-50 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-blue-600 font-medium">Total Evidence</p>
                <p class="text-2xl font-bold text-blue-900">{{ currentChain.evidence_items.length }}</p>
              </div>
              <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                </svg>
              </div>
            </div>
          </div>

          <div class="bg-green-50 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-green-600 font-medium">Confidence Level</p>
                <p class="text-2xl font-bold text-green-900">{{ Math.round(currentChain.confidence_level * 100) }}%</p>
              </div>
              <div class="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
              </div>
            </div>
          </div>

          <div class="bg-yellow-50 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-yellow-600 font-medium">Quality Score</p>
                <p class="text-2xl font-bold text-yellow-900">{{ Math.round(currentChain.quality_score * 100) }}%</p>
              </div>
              <div class="w-10 h-10 bg-yellow-100 rounded-full flex items-center justify-center">
                <svg class="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"></path>
                </svg>
              </div>
            </div>
          </div>

          <div class="bg-purple-50 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-purple-600 font-medium">Key Findings</p>
                <p class="text-2xl font-bold text-purple-900">{{ currentChain.key_findings.length }}</p>
              </div>
              <div class="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                <svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                </svg>
              </div>
            </div>
          </div>
        </div>

        <!-- Synthesis Summary -->
        <div v-if="currentChain.synthesis_summary" class="mb-6">
          <h4 class="font-medium text-gray-900 mb-2">Synthesis Summary</h4>
          <div class="p-4 bg-gray-50 rounded-lg">
            <p class="text-gray-700">{{ currentChain.synthesis_summary }}</p>
          </div>
        </div>

        <!-- Key Findings -->
        <div v-if="currentChain.key_findings.length > 0">
          <h4 class="font-medium text-gray-900 mb-3">Key Findings</h4>
          <div class="space-y-2">
            <div
              v="(finding, index) in currentChain.key_findings.slice(0, 5)"
              :key="index"
              class="p-3 bg-blue-50 border border-blue-200 rounded-lg"
            >
              <p class="text-sm text-blue-800">{{ finding }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Visualization Views -->
    <div class="visualization-views bg-white rounded-lg shadow-sm border border-gray-200">
      <div class="border-b border-gray-200 p-6">
        <h3 class="text-lg font-semibold text-gray-900">Evidence Visualization</h3>
      </div>

      <div class="p-6">
        <!-- Network Graph View -->
        <div v-if="viewMode === 'network'" class="network-view">
          <div class="h-96 bg-gray-50 rounded-lg flex items-center justify-center border-2 border-dashed border-gray-300">
            <div class="text-center">
              <svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
              </svg>
              <p class="text-gray-600">Network graph visualization</p>
              <p class="text-sm text-gray-500 mt-1">Interactive evidence relationship network</p>
            </div>
          </div>
        </div>

        <!-- Timeline View -->
        <div v-else-if="viewMode === 'timeline'" class="timeline-view">
          <div class="space-y-4">
            <div
              v-for="evidence in filteredEvidence"
              :key="evidence.id"
              class="timeline-item flex items-start space-x-4"
            >
              <div class="timeline-date flex-shrink-0 w-24">
                <p class="text-sm text-gray-600">{{ formatDate(evidence.collection_date) }}</p>
              </div>
              <div class="timeline-dot flex-shrink-0 w-4 h-4 rounded-full mt-1"
                   :class="getEvidenceQualityClass(evidence.quality)"></div>
              <div class="timeline-content flex-1 pb-8">
                <div class="bg-gray-50 rounded-lg p-4">
                  <div class="flex items-start justify-between mb-2">
                    <h5 class="font-medium text-gray-900">{{ evidence.source }}</h5>
                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                          :class="getEvidenceTypeClass(evidence.evidence_type)">
                      {{ formatEvidenceType(evidence.evidence_type) }}
                    </span>
                  </div>
                  <p class="text-sm text-gray-700 mb-3">{{ evidence.content.substring(0, 200) }}...</p>
                  <div class="flex items-center space-x-4 text-xs text-gray-600">
                    <span>Confidence: {{ Math.round(evidence.confidence_score * 100) }}%</span>
                    <span>Relevance: {{ Math.round(evidence.relevance_score * 100) }}%</span>
                    <span>Quality: {{ evidence.quality }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Quality Analysis View -->
        <div v-else-if="viewMode === 'quality'" class="quality-view">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Quality Distribution -->
            <div>
              <h4 class="font-medium text-gray-900 mb-4">Quality Distribution</h4>
              <div class="space-y-3">
                <div v-for="quality in ['high', 'medium', 'low']" :key="quality" class="quality-bar">
                  <div class="flex justify-between text-sm mb-1">
                    <span class="capitalize">{{ quality }}</span>
                    <span>{{ getQualityCount(quality) }} items</span>
                  </div>
                  <div class="w-full bg-gray-200 rounded-full h-2">
                    <div
                      class="h-2 rounded-full transition-all duration-300"
                      :class="getQualityBarClass(quality)"
                      :style="{ width: `${getQualityPercentage(quality)}%` }"
                    ></div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Evidence by Type -->
            <div>
              <h4 class="font-medium text-gray-900 mb-4">Evidence by Type</h4>
              <div class="space-y-3">
                <div v-for="(count, type) in evidenceByType" :key="type" class="type-bar">
                  <div class="flex justify-between text-sm mb-1">
                    <span class="capitalize">{{ formatEvidenceType(type) }}</span>
                    <span>{{ count }} items</span>
                  </div>
                  <div class="w-full bg-gray-200 rounded-full h-2">
                    <div
                      class="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                      :style="{ width: `${(count / filteredEvidence.length) * 100}%` }"
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Evidence Cards -->
          <div class="mt-6">
            <h4 class="font-medium text-gray-900 mb-4">Evidence Details</h4>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div
                v-for="evidence in filteredEvidence.slice(0, 9)"
                :key="evidence.id"
                class="evidence-card border rounded-lg p-4 hover:shadow-md transition-shadow"
                :class="getEvidenceCardClass(evidence)"
              >
                <div class="flex items-start justify-between mb-2">
                  <h5 class="font-medium text-gray-900 text-sm truncate">{{ evidence.source }}</h5>
                  <div class="w-3 h-3 rounded-full"
                       :class="getEvidenceQualityClass(evidence.quality)"></div>
                </div>
                <p class="text-xs text-gray-600 mb-2">{{ formatEvidenceType(evidence.evidence_type) }}</p>
                <p class="text-sm text-gray-700 line-clamp-3">{{ evidence.content }}</p>
                <div class="mt-3 pt-3 border-t border-gray-200">
                  <div class="flex justify-between text-xs text-gray-600">
                    <span>Conf: {{ Math.round(evidence.confidence_score * 100) }}%</span>
                    <span>Rel: {{ Math.round(evidence.relevance_score * 100) }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Relationship Map View -->
        <div v-else-if="viewMode === 'relationships'" class="relationships-view">
          <div v-if="currentChain.evidence_relationships.length > 0" class="space-y-4">
            <h4 class="font-medium text-gray-900">Evidence Relationships</h4>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div
                v="relationship in currentChain.evidence_relationships.slice(0, 6)"
                :key="`${relationship.evidence_1}-${relationship.evidence_2}`"
                class="relationship-card border rounded-lg p-4"
                :class="getRelationshipClass(relationship.relationship_type)"
              >
                <div class="flex items-center justify-between mb-2">
                  <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                        :class="getRelationshipTypeClass(relationship.relationship_type)">
                    {{ formatRelationshipType(relationship.relationship_type) }}
                  </span>
                  <span class="text-xs text-gray-600">
                    {{ Math.round(relationship.confidence * 100) }}% confidence
                  </span>
                </div>
                <div class="text-sm">
                  <p class="font-medium text-gray-900 truncate">{{ getEvidenceTitle(relationship.evidence_1) }}</p>
                  <div class="flex items-center justify-center py-1">
                    <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3"></path>
                    </svg>
                  </div>
                  <p class="font-medium text-gray-900 truncate">{{ getEvidenceTitle(relationship.evidence_2) }}</p>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-12">
            <svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
            </svg>
            <p class="text-gray-600">No evidence relationships found</p>
            <p class="text-sm text-gray-500 mt-1">Run analysis to identify relationships</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Evidence Details Modal -->
    <div v-if="showEvidenceDetails" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div class="border-b border-gray-200 p-6">
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold text-gray-900">Evidence Details</h3>
            <button
              @click="showEvidenceDetails = false"
              class="text-gray-400 hover:text-gray-600"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
        </div>

        <div v-if="selectedEvidence" class="p-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Evidence Info -->
            <div>
              <h4 class="font-medium text-gray-900 mb-3">Information</h4>
              <dl class="space-y-2">
                <div class="flex justify-between">
                  <dt class="text-sm text-gray-600">Source:</dt>
                  <dd class="text-sm font-medium">{{ selectedEvidence.source }}</dd>
                </div>
                <div class="flex justify-between">
                  <dt class="text-sm text-gray-600">Type:</dt>
                  <dd class="text-sm font-medium">{{ formatEvidenceType(selectedEvidence.evidence_type) }}</dd>
                </div>
                <div class="flex justify-between">
                  <dt class="text-sm text-gray-600">Quality:</dt>
                  <dd class="text-sm font-medium">{{ selectedEvidence.quality }}</dd>
                </div>
                <div class="flex justify-between">
                  <dt class="text-sm text-gray-600">Collected By:</dt>
                  <dd class="text-sm font-medium">{{ selectedEvidence.collected_by }}</dd>
                </div>
                <div class="flex justify-between">
                  <dt class="text-sm text-gray-600">Collection Date:</dt>
                  <dd class="text-sm font-medium">{{ formatDate(selectedEvidence.collection_date) }}</dd>
                </div>
              </dl>
            </div>

            <!-- Quality Metrics -->
            <div>
              <h4 class="font-medium text-gray-900 mb-3">Quality Metrics</h4>
              <dl class="space-y-2">
                <div class="flex justify-between">
                  <dt class="text-sm text-gray-600">Confidence Score:</dt>
                  <dd class="text-sm font-medium">{{ Math.round(selectedEvidence.confidence_score * 100) }}%</dd>
                </div>
                <div class="flex justify-between">
                  <dt class="text-sm text-gray-600">Relevance Score:</dt>
                  <dd class="text-sm font-medium">{{ Math.round(selectedEvidence.relevance_score * 100) }}%</dd>
                </div>
                <div class="flex justify-between">
                  <dt class="text-sm text-gray-600">Status:</dt>
                  <dd class="text-sm font-medium">{{ selectedEvidence.status }}</dd>
                </div>
                <div v-if="selectedEvidence.tags && selectedEvidence.tags.length > 0">
                  <dt class="text-sm text-gray-600">Tags:</dt>
                  <dd class="text-sm font-medium">
                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-800 mr-1"
                          v-for="tag in selectedEvidence.tags" :key="tag">
                      {{ tag }}
                    </span>
                  </dd>
                </div>
              </dl>
            </div>
          </div>

          <!-- Evidence Content -->
          <div class="mt-6">
            <h4 class="font-medium text-gray-900 mb-3">Content</h4>
            <div class="p-4 bg-gray-50 rounded-lg">
              <p class="text-gray-700">{{ selectedEvidence.content }}</p>
            </div>
          </div>

          <!-- Related Evidence -->
          <div v-if="selectedEvidence.related_evidence && selectedEvidence.related_evidence.length > 0" class="mt-6">
            <h4 class="font-medium text-gray-900 mb-3">Related Evidence</h4>
            <div class="space-y-2">
              <div
                v="relatedId in selectedEvidence.related_evidence"
                :key="relatedId"
                class="p-3 bg-gray-50 rounded-md text-sm"
              >
                <p class="font-medium text-gray-900">{{ getEvidenceTitle(relatedId) }}</p>
                <p class="text-gray-600">Related evidence ID: {{ relatedId }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useResearchStore } from '@/stores/research'
import { useNotificationStore } from '@/stores/notification'

export default {
  name: 'EvidenceChainVisualization',
  setup() {
    const researchStore = useResearchStore()
    const notificationStore = useNotificationStore()

    // Reactive data
    const isLoading = ref(false)
    const isAnalyzing = ref(false)
    const showEvidenceDetails = ref(false)
    const selectedEvidence = ref(null)
    const viewMode = ref('quality')

    const filters = ref({
      evidenceType: '',
      qualityLevel: '',
      confidenceThreshold: 0.0
    })

    // Computed properties
    const currentChain = computed(() => {
      // Get current plan's evidence chain or use first available
      if (researchStore.currentPlan) {
        const planId = researchStore.currentPlan.id
        return researchStore.evidenceChains[planId] || null
      }
      return Object.values(researchStore.evidenceChains)[0] || null
    })

    const filteredEvidence = computed(() => {
      if (!currentChain.value) return []

      let evidence = currentChain.value.evidence_items || []

      // Apply filters
      if (filters.value.evidenceType) {
        evidence = evidence.filter(item => item.evidence_type === filters.value.evidenceType)
      }

      if (filters.value.qualityLevel) {
        evidence = evidence.filter(item => item.quality === filters.value.qualityLevel)
      }

      if (filters.value.confidenceThreshold > 0) {
        evidence = evidence.filter(item => item.confidence_score >= filters.value.confidenceThreshold)
      }

      return evidence
    })

    const evidenceByType = computed(() => {
      const types = {}
      filteredEvidence.value.forEach(item => {
        types[item.evidence_type] = (types[item.evidence_type] || 0) + 1
      })
      return types
    })

    // Methods
    const refreshEvidenceChain = async () => {
      if (!currentChain.value) return

      isLoading.value = true
      try {
        await researchStore.getEvidenceChain(currentChain.value.id)
        notificationStore.showSuccess('Evidence chain refreshed')
      } catch (error) {
        notificationStore.showError(`Failed to refresh evidence chain: ${error.message}`)
      } finally {
        isLoading.value = false
      }
    }

    const analyzeEvidenceChain = async () => {
      if (!currentChain.value) return

      isAnalyzing.value = true
      try {
        await researchStore.analyzeEvidenceChain(currentChain.value.id)
        notificationStore.showSuccess('Evidence chain analysis completed')
      } catch (error) {
        notificationStore.showError(`Failed to analyze evidence chain: ${error.message}`)
      } finally {
        isAnalyzing.value = false
      }
    }

    const exportEvidenceChain = async () => {
      if (!currentChain.value) return

      try {
        const data = {
          chain: currentChain.value,
          evidence: filteredEvidence.value,
          exportDate: new Date().toISOString()
        }

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `evidence-chain-${currentChain.value.id}.json`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)

        notificationStore.showSuccess('Evidence chain exported successfully')
      } catch (error) {
        notificationStore.showError(`Failed to export evidence chain: ${error.message}`)
      }
    }

    const applyFilters = () => {
      // Filters are reactive, so this just triggers recomputation
    }

    const getEvidenceTitle = (evidenceId) => {
      if (!currentChain.value) return 'Unknown'
      const evidence = currentChain.value.evidence_items.find(item => item.id === evidenceId)
      return evidence ? evidence.source : 'Unknown'
    }

    // Helper methods
    const getQualityCount = (quality) => {
      return filteredEvidence.value.filter(item => item.quality === quality).length
    }

    const getQualityPercentage = (quality) => {
      if (filteredEvidence.value.length === 0) return 0
      return (getQualityCount(quality) / filteredEvidence.value.length) * 100
    }

    const getEvidenceQualityClass = (quality) => {
      const classes = {
        'high': 'bg-green-500',
        'medium': 'bg-yellow-500',
        'low': 'bg-red-500',
        'unverified': 'bg-gray-500'
      }
      return classes[quality] || 'bg-gray-500'
    }

    const getEvidenceTypeClass = (type) => {
      const classes = {
        'web_source': 'bg-blue-100 text-blue-800',
        'academic_paper': 'bg-green-100 text-green-800',
        'book': 'bg-purple-100 text-purple-800',
        'documentation': 'bg-gray-100 text-gray-800',
        'interview': 'bg-yellow-100 text-yellow-800',
        'survey': 'bg-indigo-100 text-indigo-800'
      }
      return classes[type] || 'bg-gray-100 text-gray-800'
    }

    const getEvidenceCardClass = (evidence) => {
      const qualityClasses = {
        'high': 'border-green-200 bg-green-50',
        'medium': 'border-yellow-200 bg-yellow-50',
        'low': 'border-red-200 bg-red-50',
        'unverified': 'border-gray-200 bg-white'
      }
      return qualityClasses[evidence.quality] || 'border-gray-200 bg-white'
    }

    const getQualityBarClass = (quality) => {
      const classes = {
        'high': 'bg-green-500',
        'medium': 'bg-yellow-500',
        'low': 'bg-red-500'
      }
      return classes[quality] || 'bg-gray-500'
    }

    const getRelationshipClass = (type) => {
      const classes = {
        'supports': 'border-green-200 bg-green-50',
        'contradicts': 'border-red-200 bg-red-50',
        'extends': 'border-blue-200 bg-blue-50',
        'clarifies': 'border-yellow-200 bg-yellow-50',
        'depends_on': 'border-purple-200 bg-purple-50'
      }
      return classes[type] || 'border-gray-200 bg-gray-50'
    }

    const getRelationshipTypeClass = (type) => {
      const classes = {
        'supports': 'bg-green-100 text-green-800',
        'contradicts': 'bg-red-100 text-red-800',
        'extends': 'bg-blue-100 text-blue-800',
        'clarifies': 'bg-yellow-100 text-yellow-800',
        'depends_on': 'bg-purple-100 text-purple-800'
      }
      return classes[type] || 'bg-gray-100 text-gray-800'
    }

    const formatEvidenceType = (type) => {
      return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
    }

    const formatRelationshipType = (type) => {
      return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
    }

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      return new Date(dateString).toLocaleDateString()
    }

    // Watch for changes in current plan
    watch(() => researchStore.currentPlan, (newPlan) => {
      if (newPlan) {
        // Load evidence chain for current plan
        refreshEvidenceChain()
      }
    })

    // Lifecycle
    onMounted(() => {
      if (currentChain.value) {
        refreshEvidenceChain()
      }
    })

    return {
      // Data
      isLoading,
      isAnalyzing,
      showEvidenceDetails,
      selectedEvidence,
      viewMode,
      filters,

      // Computed
      currentChain,
      filteredEvidence,
      evidenceByType,

      // Methods
      refreshEvidenceChain,
      analyzeEvidenceChain,
      exportEvidenceChain,
      applyFilters,
      getEvidenceTitle,
      getQualityCount,
      getQualityPercentage,
      getEvidenceQualityClass,
      getEvidenceTypeClass,
      getEvidenceCardClass,
      getQualityBarClass,
      getRelationshipClass,
      getRelationshipTypeClass,
      formatEvidenceType,
      formatRelationshipType,
      formatDate
    }
  }
}
</script>

<style scoped>
.evidence-chain-visualization {
  max-width: 7xl;
  margin: 0 auto;
  padding: 1rem;
}

.timeline-dot {
  transition: all 0.2s ease;
}

.timeline-item:hover .timeline-dot {
  transform: scale(1.2);
}

.evidence-card {
  transition: all 0.2s ease;
}

.evidence-card:hover {
  transform: translateY(-2px);
}

.relationship-card {
  transition: all 0.2s ease;
}

.relationship-card:hover {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* Quality bars animation */
.transition-all {
  transition: all 0.3s ease;
}

/* Custom scrollbar for modals */
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}

/* Line clamp utility */
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>