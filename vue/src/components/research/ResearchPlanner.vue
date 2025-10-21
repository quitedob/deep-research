<template>
  <div class="research-planner">
    <!-- Header -->
    <div class="planner-header">
      <h2 class="text-2xl font-bold text-gray-900 mb-2">Research Planning</h2>
      <p class="text-gray-600">Create and manage intelligent research plans with AI-powered step generation</p>
    </div>

    <!-- Create New Plan Form -->
    <div v-if="!currentPlan" class="plan-creation bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
      <h3 class="text-lg font-semibold text-gray-900 mb-4">Create Research Plan</h3>

      <form @submit.prevent="createPlan" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Research Title *
          </label>
          <input
            v-model="planForm.title"
            type="text"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Enter research title"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Research Query *
          </label>
          <textarea
            v-model="planForm.researchQuery"
            required
            rows="3"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="What do you want to research?"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Description
          </label>
          <textarea
            v-model="planForm.description"
            rows="3"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Describe your research goals and objectives"
          />
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Research Domain
            </label>
            <select
              v-model="planForm.domain"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Auto-detect</option>
              <option value="technology">Technology</option>
              <option value="business">Business</option>
              <option value="science">Science</option>
              <option value="healthcare">Healthcare</option>
              <option value="education">Education</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Max Steps
            </label>
            <input
              v-model.number="planForm.maxSteps"
              type="number"
              min="3"
              max="10"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        <div class="flex justify-end space-x-3">
          <button
            type="button"
            @click="resetForm"
            class="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
          >
            Clear
          </button>
          <button
            type="submit"
            :disabled="isCreating"
            class="px-6 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            <span v-if="isCreating" class="flex items-center">
              <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Creating Plan...
            </span>
            <span v-else>Create Research Plan</span>
          </button>
        </div>
      </form>
    </div>

    <!-- Current Plan Display -->
    <div v-if="currentPlan" class="current-plan bg-white rounded-lg shadow-sm border border-gray-200">
      <!-- Plan Header -->
      <div class="plan-header border-b border-gray-200 p-6">
        <div class="flex justify-between items-start">
          <div>
            <h3 class="text-xl font-semibold text-gray-900">{{ currentPlan.title }}</h3>
            <p class="text-gray-600 mt-1">{{ currentPlan.description }}</p>
            <div class="flex items-center space-x-4 mt-3">
              <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                    :class="getStatusClass(currentPlan.status)">
                {{ currentPlan.status }}
              </span>
              <span class="text-sm text-gray-500">
                Progress: {{ currentPlan.completed_steps }}/{{ currentPlan.total_steps }} steps
              </span>
              <span class="text-sm text-gray-500">
                Created: {{ formatDate(currentPlan.created_at) }}
              </span>
            </div>
          </div>
          <div class="flex space-x-2">
            <button
              @click="viewHistory"
              class="px-3 py-1 text-sm text-gray-700 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
            >
              History
            </button>
            <button
              @click="finishPlan"
              :disabled="currentPlan.status === 'completed'"
              class="px-3 py-1 text-sm text-white bg-green-600 rounded hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              Finish Plan
            </button>
            <button
              @click="resetCurrentPlan"
              class="px-3 py-1 text-sm text-gray-700 bg-red-100 rounded hover:bg-red-200 transition-colors"
            >
              Close
            </button>
          </div>
        </div>

        <!-- Progress Bar -->
        <div class="mt-4">
          <div class="w-full bg-gray-200 rounded-full h-2">
            <div
              class="bg-blue-600 h-2 rounded-full transition-all duration-300"
              :style="{ width: `${progressPercentage}%` }"
            ></div>
          </div>
        </div>
      </div>

      <!-- Plan Steps -->
      <div class="plan-steps p-6">
        <h4 class="text-lg font-medium text-gray-900 mb-4">Research Steps</h4>

        <div class="space-y-4">
          <div
            v-for="(step, index) in currentPlan.subtasks"
            :key="step.id"
            class="step-item border rounded-lg p-4"
            :class="getStepClass(step)"
          >
            <div class="flex items-start justify-between">
              <div class="flex items-start space-x-3">
                <div class="step-number flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium"
                     :class="getStepNumberClass(step)">
                  {{ index + 1 }}
                </div>
                <div class="flex-1">
                  <h5 class="font-medium text-gray-900">{{ step.title }}</h5>
                  <p class="text-sm text-gray-600 mt-1">{{ step.description }}</p>

                  <!-- Current Step Working Plan -->
                  <div v-if="isCurrentStep(index) && step.working_plan" class="mt-3 p-3 bg-blue-50 rounded-md">
                    <p class="text-sm text-blue-800">{{ step.working_plan }}</p>
                  </div>

                  <!-- Step Status and Actions -->
                  <div class="flex items-center space-x-4 mt-3">
                    <span class="text-xs font-medium"
                          :class="getStepStatusClass(step)">
                      {{ step.status }}
                    </span>
                    <span v-if="step.start_time" class="text-xs text-gray-500">
                      Started: {{ formatDate(step.start_time) }}
                    </span>
                    <span v-if="step.end_time" class="text-xs text-gray-500">
                      Completed: {{ formatDate(step.end_time) }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Step Actions -->
              <div class="flex space-x-2">
                <button
                  v-if="isCurrentStep(index) && step.status === 'pending'"
                  @click="startStep(step)"
                  class="px-3 py-1 text-sm text-white bg-blue-600 rounded hover:bg-blue-700 transition-colors"
                >
                  Start
                </button>
                <button
                  v-if="isCurrentStep(index) && step.status === 'in_progress'"
                  @click="completeStep(step)"
                  class="px-3 py-1 text-sm text-white bg-green-600 rounded hover:bg-green-700 transition-colors"
                >
                  Complete
                </button>
                <button
                  @click="viewStepDetails(step)"
                  class="px-3 py-1 text-sm text-gray-700 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
                >
                  Details
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Plan Insights -->
      <div v-if="currentPlan.insights && currentPlan.insights.length > 0" class="plan-insights border-t border-gray-200 p-6">
        <h4 class="text-lg font-medium text-gray-900 mb-4">Research Insights</h4>
        <div class="space-y-3">
          <div
            v="(insight, index) in currentPlan.insights.slice(-5)"
            :key="index"
            class="p-3 bg-gray-50 rounded-md"
          >
            <p class="text-sm text-gray-700">{{ insight }}</p>
            <span class="text-xs text-gray-500">Latest insight</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Historical Plans -->
    <div v-if="showHistory && historicalPlans.length > 0" class="historical-plans bg-white rounded-lg shadow-sm border border-gray-200 mt-6">
      <div class="border-b border-gray-200 p-6">
        <h3 class="text-lg font-semibold text-gray-900">Historical Plans</h3>
      </div>
      <div class="p-6">
        <div class="space-y-4">
          <div
            v-for="plan in historicalPlans"
            :key="plan.plan_id"
            class="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors"
            @click="recoverPlan(plan.plan_id)"
          >
            <div class="flex justify-between items-start">
              <div>
                <h5 class="font-medium text-gray-900">{{ plan.title }}</h5>
                <p class="text-sm text-gray-600 mt-1">{{ plan.description.substring(0, 100) }}...</p>
                <div class="flex items-center space-x-3 mt-2">
                  <span class="text-xs text-gray-500">
                    Completed: {{ formatDate(plan.completed_at) }}
                  </span>
                  <span class="text-xs text-gray-500">
                    {{ plan.total_steps }} steps
                  </span>
                  <span class="text-xs text-gray-500">
                    {{ plan.insights_count }} insights
                  </span>
                </div>
              </div>
              <button
                @click.stop="recoverPlan(plan.plan_id)"
                class="px-3 py-1 text-sm text-blue-600 bg-blue-50 rounded hover:bg-blue-100 transition-colors"
              >
                Recover
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Step Details Modal -->
    <div v-if="showStepDetails" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div class="border-b border-gray-200 p-6">
          <h3 class="text-lg font-semibold text-gray-900">Step Details</h3>
        </div>
        <div class="p-6">
          <div v-if="selectedStep" class="space-y-4">
            <div>
              <h4 class="font-medium text-gray-900">{{ selectedStep.title }}</h4>
              <p class="text-gray-600 mt-1">{{ selectedStep.description }}</p>
            </div>

            <div>
              <h5 class="font-medium text-gray-900 mb-2">Working Plan</h5>
              <div class="p-3 bg-gray-50 rounded-md">
                <p class="text-sm text-gray-700">{{ selectedStep.working_plan || 'No working plan defined yet' }}</p>
              </div>
            </div>

            <div v-if="selectedStep.evidence_collected && selectedStep.evidence_collected.length > 0">
              <h5 class="font-medium text-gray-900 mb-2">Evidence Collected</h5>
              <div class="space-y-2">
                <div
                  v="(evidence, index) in selectedStep.evidence_collected"
                  :key="index"
                  class="p-2 bg-gray-50 rounded text-sm text-gray-700"
                >
                  {{ evidence }}
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="border-t border-gray-200 p-6 flex justify-end">
          <button
            @click="showStepDetails = false"
            class="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
          >
            Close
          </button>
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
  name: 'ResearchPlanner',
  setup() {
    const researchStore = useResearchStore()
    const notificationStore = useNotificationStore()

    // Reactive data
    const isCreating = ref(false)
    const showHistory = ref(false)
    const showStepDetails = ref(false)
    const selectedStep = ref(null)
    const historicalPlans = ref([])

    // Form data
    const planForm = ref({
      title: '',
      researchQuery: '',
      description: '',
      domain: '',
      maxSteps: 5
    })

    // Computed properties
    const currentPlan = computed(() => researchStore.currentPlan)
    const progressPercentage = computed(() => {
      if (!currentPlan.value) return 0
      return currentPlan.value.progress_percentage || 0
    })

    // Methods
    const createPlan = async () => {
      if (!planForm.value.title || !planForm.value.researchQuery) {
        notificationStore.showError('Title and research query are required')
        return
      }

      isCreating.value = true
      try {
        await researchStore.createPlan({
          title: planForm.value.title,
          description: planForm.value.description || `Research on: ${planForm.value.researchQuery}`,
          researchQuery: planForm.value.researchQuery,
          domain: planForm.value.domain,
          maxSteps: planForm.value.maxSteps
        })

        notificationStore.showSuccess('Research plan created successfully')
        resetForm()
      } catch (error) {
        notificationStore.showError(`Failed to create plan: ${error.message}`)
      } finally {
        isCreating.value = false
      }
    }

    const resetForm = () => {
      planForm.value = {
        title: '',
        researchQuery: '',
        description: '',
        domain: '',
        maxSteps: 5
      }
    }

    const startStep = async (step) => {
      try {
        await researchStore.updateSubtaskStatus(step.id, 'in_progress')
        notificationStore.showSuccess(`Started: ${step.title}`)
      } catch (error) {
        notificationStore.showError(`Failed to start step: ${error.message}`)
      }
    }

    const completeStep = async (step) => {
      try {
        await researchStore.updateSubtaskStatus(step.id, 'completed')
        notificationStore.showSuccess(`Completed: ${step.title}`)
      } catch (error) {
        notificationStore.showError(`Failed to complete step: ${error.message}`)
      }
    }

    const finishPlan = async () => {
      try {
        await researchStore.finishPlan({
          summary: 'Research completed successfully',
          finalInsights: currentPlan.value.insights || []
        })
        notificationStore.showSuccess('Research plan completed')
      } catch (error) {
        notificationStore.showError(`Failed to finish plan: ${error.message}`)
      }
    }

    const resetCurrentPlan = () => {
      researchStore.clearCurrentPlan()
    }

    const viewHistory = async () => {
      try {
        const plans = await researchStore.getHistoricalPlans()
        historicalPlans.value = plans
        showHistory.value = true
      } catch (error) {
        notificationStore.showError(`Failed to load history: ${error.message}`)
      }
    }

    const recoverPlan = async (planId) => {
      try {
        await researchStore.recoverHistoricalPlan(planId)
        showHistory.value = false
        notificationStore.showSuccess('Plan recovered successfully')
      } catch (error) {
        notificationStore.showError(`Failed to recover plan: ${error.message}`)
      }
    }

    const viewStepDetails = (step) => {
      selectedStep.value = step
      showStepDetails.value = true
    }

    // Helper methods
    const isCurrentStep = (index) => {
      if (!currentPlan.value) return false
      return currentPlan.value.subtasks[index].status === 'in_progress'
    }

    const getStatusClass = (status) => {
      const classes = {
        'created': 'bg-blue-100 text-blue-800',
        'in_progress': 'bg-yellow-100 text-yellow-800',
        'completed': 'bg-green-100 text-green-800',
        'failed': 'bg-red-100 text-red-800'
      }
      return classes[status] || 'bg-gray-100 text-gray-800'
    }

    const getStepClass = (step) => {
      const classes = {
        'pending': 'border-gray-200 bg-gray-50',
        'in_progress': 'border-blue-200 bg-blue-50',
        'completed': 'border-green-200 bg-green-50',
        'failed': 'border-red-200 bg-red-50'
      }
      return classes[step.status] || 'border-gray-200 bg-white'
    }

    const getStepNumberClass = (step) => {
      const classes = {
        'pending': 'bg-gray-300 text-gray-700',
        'in_progress': 'bg-blue-600 text-white',
        'completed': 'bg-green-600 text-white',
        'failed': 'bg-red-600 text-white'
      }
      return classes[step.status] || 'bg-gray-300 text-gray-700'
    }

    const getStepStatusClass = (step) => {
      const classes = {
        'pending': 'text-gray-600',
        'in_progress': 'text-blue-600',
        'completed': 'text-green-600',
        'failed': 'text-red-600'
      }
      return classes[step.status] || 'text-gray-600'
    }

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      return new Date(dateString).toLocaleDateString() + ' ' + new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }

    // Lifecycle
    onMounted(() => {
      // Load current plan if exists
      researchStore.loadCurrentPlan()
    })

    return {
      // Data
      isCreating,
      showHistory,
      showStepDetails,
      selectedStep,
      historicalPlans,
      planForm,

      // Computed
      currentPlan,
      progressPercentage,

      // Methods
      createPlan,
      resetForm,
      startStep,
      completeStep,
      finishPlan,
      resetCurrentPlan,
      viewHistory,
      recoverPlan,
      viewStepDetails,
      isCurrentStep,
      getStatusClass,
      getStepClass,
      getStepNumberClass,
      getStepStatusClass,
      formatDate
    }
  }
}
</script>

<style scoped>
.research-planner {
  max-width: 4xl;
  margin: 0 auto;
  padding: 1rem;
}

.step-number {
  transition: all 0.2s ease;
}

.step-item {
  transition: all 0.2s ease;
}

.step-item:hover {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Custom scrollbar for modal */
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
</style>