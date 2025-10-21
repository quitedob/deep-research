import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useResearchStore = defineStore('research', () => {
  // State
  const currentPlan = ref(null)
  const historicalPlans = ref([])
  const evidenceChains = ref({})
  const researchInsights = ref([])
  const isLoading = ref(false)

  // Computed
  const hasCurrentPlan = computed(() => currentPlan.value !== null)
  const planProgress = computed(() => {
    if (!currentPlan.value) return 0
    return currentPlan.value.progress_percentage || 0
  })

  const currentStep = computed(() => {
    if (!currentPlan.value || !currentPlan.value.subtasks) return null
    return currentPlan.value.subtasks.find(step => step.status === 'in_progress')
  })

  const nextStep = computed(() => {
    if (!currentPlan.value || !currentPlan.value.subtasks) return null
    return currentPlan.value.subtasks.find(step => step.status === 'pending')
  })

  const completedSteps = computed(() => {
    if (!currentPlan.value || !currentPlan.value.subtasks) return []
    return currentPlan.value.subtasks.filter(step => step.status === 'completed')
  })

  // Actions
  const createPlan = async (planData) => {
    isLoading.value = true
    try {
      const response = await axios.post('/api/research/plans', planData)

      if (response.data.success) {
        currentPlan.value = response.data.plan
        return response.data.plan
      } else {
        throw new Error(response.data.error || 'Failed to create research plan')
      }
    } catch (error) {
      console.error('Failed to create research plan:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const loadCurrentPlan = async () => {
    try {
      const response = await axios.get('/api/research/plans/current')

      if (response.data.success && response.data.plan) {
        currentPlan.value = response.data.plan
        return response.data.plan
      }
    } catch (error) {
      console.error('Failed to load current plan:', error)
    }
  }

  const updatePlan = async (planId, updates) => {
    try {
      const response = await axios.put(`/api/research/plans/${planId}`, updates)

      if (response.data.success) {
        if (currentPlan.value && currentPlan.value.id === planId) {
          currentPlan.value = response.data.plan
        }
        return response.data.plan
      } else {
        throw new Error(response.data.error || 'Failed to update plan')
      }
    } catch (error) {
      console.error('Failed to update plan:', error)
      throw error
    }
  }

  const reviseCurrentPlan = async (revisionData) => {
    if (!currentPlan.value) {
      throw new Error('No current plan to revise')
    }

    try {
      const response = await axios.post(`/api/research/plans/${currentPlan.value.id}/revise`, revisionData)

      if (response.data.success) {
        currentPlan.value = response.data.plan
        return response.data.plan
      } else {
        throw new Error(response.data.error || 'Failed to revise plan')
      }
    } catch (error) {
      console.error('Failed to revise plan:', error)
      throw error
    }
  }

  const finishPlan = async (completionData) => {
    if (!currentPlan.value) {
      throw new Error('No current plan to finish')
    }

    try {
      const response = await axios.post(`/api/research/plans/${currentPlan.value.id}/finish`, completionData)

      if (response.data.success) {
        currentPlan.value = response.data.plan
        await loadHistoricalPlans() // Refresh historical plans
        return response.data.plan
      } else {
        throw new Error(response.data.error || 'Failed to finish plan')
      }
    } catch (error) {
      console.error('Failed to finish plan:', error)
      throw error
    }
  }

  const executePlanStep = async (stepData) => {
    if (!currentPlan.value) {
      throw new Error('No current plan')
    }

    try {
      const response = await axios.post(`/api/research/plans/${currentPlan.value.id}/execute-step`, stepData)

      if (response.data.success) {
        currentPlan.value = response.data.plan
        return response.data.result
      } else {
        throw new Error(response.data.error || 'Failed to execute step')
      }
    } catch (error) {
      console.error('Failed to execute plan step:', error)
      throw error
    }
  }

  const updateSubtaskStatus = async (subtaskId, status, notes = null) => {
    if (!currentPlan.value) {
      throw new Error('No current plan')
    }

    try {
      const response = await axios.put(`/api/research/plans/${currentPlan.value.id}/subtasks/${subtaskId}`, {
        status,
        notes
      })

      if (response.data.success) {
        currentPlan.value = response.data.plan
        return response.data.subtask
      } else {
        throw new Error(response.data.error || 'Failed to update subtask status')
      }
    } catch (error) {
      console.error('Failed to update subtask status:', error)
      throw error
    }
  }

  const addPlanInsight = async (insight) => {
    if (!currentPlan.value) {
      throw new Error('No current plan')
    }

    try {
      const response = await axios.post(`/api/research/plans/${currentPlan.value.id}/insights`, {
        insight
      })

      if (response.data.success) {
        currentPlan.value = response.data.plan
        return response.data.insight
      } else {
        throw new Error(response.data.error || 'Failed to add insight')
      }
    } catch (error) {
      console.error('Failed to add insight:', error)
      throw error
    }
  }

  const addPlanEvidence = async (evidence) => {
    if (!currentPlan.value) {
      throw new Error('No current plan')
    }

    try {
      const response = await axios.post(`/api/research/plans/${currentPlan.value.id}/evidence`, {
        evidence
      })

      if (response.data.success) {
        currentPlan.value = response.data.plan
        return response.data.evidence
      } else {
        throw new Error(response.data.error || 'Failed to add evidence')
      }
    } catch (error) {
      console.error('Failed to add evidence:', error)
      throw error
    }
  }

  const getHistoricalPlans = async (limit = 5) => {
    try {
      const response = await axios.get(`/api/research/plans/history?limit=${limit}`)

      if (response.data.success) {
        historicalPlans.value = response.data.plans
        return response.data.plans
      } else {
        throw new Error(response.data.error || 'Failed to get historical plans')
      }
    } catch (error) {
      console.error('Failed to get historical plans:', error)
      throw error
    }
  }

  const recoverHistoricalPlan = async (planId) => {
    try {
      const response = await axios.post(`/api/research/plans/${planId}/recover`)

      if (response.data.success) {
        currentPlan.value = response.data.plan
        await getHistoricalPlans() // Refresh historical plans
        return response.data.plan
      } else {
        throw new Error(response.data.error || 'Failed to recover plan')
      }
    } catch (error) {
      console.error('Failed to recover historical plan:', error)
      throw error
    }
  }

  const deletePlan = async (planId) => {
    try {
      const response = await axios.delete(`/api/research/plans/${planId}`)

      if (response.data.success) {
        if (currentPlan.value && currentPlan.value.id === planId) {
          currentPlan.value = null
        }
        await getHistoricalPlans() // Refresh historical plans
        return true
      } else {
        throw new Error(response.data.error || 'Failed to delete plan')
      }
    } catch (error) {
      console.error('Failed to delete plan:', error)
      throw error
    }
  }

  const getPlanDetails = async (planId) => {
    try {
      const response = await axios.get(`/api/research/plans/${planId}`)

      if (response.data.success) {
        return response.data.plan
      } else {
        throw new Error(response.data.error || 'Failed to get plan details')
      }
    } catch (error) {
      console.error('Failed to get plan details:', error)
      throw error
    }
  }

  // Evidence Chain Management
  const createEvidenceChain = async (chainData) => {
    try {
      const response = await axios.post('/api/research/evidence-chains', chainData)

      if (response.data.success) {
        evidenceChains.value[response.data.chain.id] = response.data.chain
        return response.data.chain
      } else {
        throw new Error(response.data.error || 'Failed to create evidence chain')
      }
    } catch (error) {
      console.error('Failed to create evidence chain:', error)
      throw error
    }
  }

  const getEvidenceChain = async (chainId) => {
    try {
      const response = await axios.get(`/api/research/evidence-chains/${chainId}`)

      if (response.data.success) {
        evidenceChains.value[chainId] = response.data.chain
        return response.data.chain
      } else {
        throw new Error(response.data.error || 'Failed to get evidence chain')
      }
    } catch (error) {
      console.error('Failed to get evidence chain:', error)
      throw error
    }
  }

  const addEvidence = async (chainId, evidenceData) => {
    try {
      const response = await axios.post(`/api/research/evidence-chains/${chainId}/evidence`, evidenceData)

      if (response.data.success) {
        // Update cached evidence chain
        if (evidenceChains.value[chainId]) {
          evidenceChains.value[chainId] = response.data.chain
        }
        return response.data.evidence
      } else {
        throw new Error(response.data.error || 'Failed to add evidence')
      }
    } catch (error) {
      console.error('Failed to add evidence:', error)
      throw error
    }
  }

  const analyzeEvidenceChain = async (chainId) => {
    try {
      const response = await axios.post(`/api/research/evidence-chains/${chainId}/analyze`)

      if (response.data.success) {
        // Update cached evidence chain with analysis results
        if (evidenceChains.value[chainId]) {
          evidenceChains.value[chainId] = response.data.chain
        }
        return response.data.analysis
      } else {
        throw new Error(response.data.error || 'Failed to analyze evidence chain')
      }
    } catch (error) {
      console.error('Failed to analyze evidence chain:', error)
      throw error
    }
  }

  // Research Insights
  const generateInsights = async (insightData) => {
    try {
      const response = await axios.post('/api/research/insights/generate', insightData)

      if (response.data.success) {
        researchInsights.value = response.data.insights
        return response.data.insights
      } else {
        throw new Error(response.data.error || 'Failed to generate insights')
      }
    } catch (error) {
      console.error('Failed to generate insights:', error)
      throw error
    }
  }

  const getInsights = async (filters = {}) => {
    try {
      const params = new URLSearchParams(filters)
      const response = await axios.get(`/api/research/insights?${params}`)

      if (response.data.success) {
        researchInsights.value = response.data.insights
        return response.data.insights
      } else {
        throw new Error(response.data.error || 'Failed to get insights')
      }
    } catch (error) {
      console.error('Failed to get insights:', error)
      throw error
    }
  }

  // Utility methods
  const clearCurrentPlan = () => {
    currentPlan.value = null
  }

  const clearEvidenceChains = () => {
    evidenceChains.value = {}
  }

  const clearInsights = () => {
    researchInsights.value = []
  }

  const reset = () => {
    currentPlan.value = null
    historicalPlans.value = []
    evidenceChains.value = {}
    researchInsights.value = []
    isLoading.value = false
  }

  return {
    // State
    currentPlan,
    historicalPlans,
    evidenceChains,
    researchInsights,
    isLoading,

    // Computed
    hasCurrentPlan,
    planProgress,
    currentStep,
    nextStep,
    completedSteps,

    // Plan Management
    createPlan,
    loadCurrentPlan,
    updatePlan,
    reviseCurrentPlan,
    finishPlan,
    executePlanStep,
    updateSubtaskStatus,
    addPlanInsight,
    addPlanEvidence,
    getHistoricalPlans,
    recoverHistoricalPlan,
    deletePlan,
    getPlanDetails,

    // Evidence Chain Management
    createEvidenceChain,
    getEvidenceChain,
    addEvidence,
    analyzeEvidenceChain,

    // Research Insights
    generateInsights,
    getInsights,

    // Utility
    clearCurrentPlan,
    clearEvidenceChains,
    clearInsights,
    reset
  }
})