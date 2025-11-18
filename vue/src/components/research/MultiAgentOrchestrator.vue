<template>
  <div class="multi-agent-orchestrator">
    <!-- Header -->
    <div class="orchestrator-header">
      <h2 class="text-2xl font-bold text-gray-900 mb-2">Multi-Agent Orchestration</h2>
      <p class="text-gray-600">Coordinate and monitor multiple AI agents for complex research tasks</p>
    </div>

    <!-- Orchestration Controls -->
    <div class="orchestrator-controls bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-semibold text-gray-900">Orchestration Control</h3>
        <div class="flex space-x-2">
          <button
            @click="initializeOrchestrator"
            :disabled="isInitialized"
            class="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            Initialize
          </button>
          <button
            @click="startOrchestration"
            :disabled="!isInitialized || isRunning"
            class="px-4 py-2 text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50 transition-colors"
          >
            Start
          </button>
          <button
            @click="pauseOrchestration"
            :disabled="!isRunning"
            class="px-4 py-2 text-white bg-yellow-600 rounded-md hover:bg-yellow-700 disabled:opacity-50 transition-colors"
          >
            Pause
          </button>
          <button
            @click="stopOrchestration"
            :disabled="!isRunning"
            class="px-4 py-2 text-white bg-red-600 rounded-md hover:bg-red-700 disabled:opacity-50 transition-colors"
          >
            Stop
          </button>
        </div>
      </div>

      <!-- Orchestration Configuration -->
      <div class="grid grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Execution Strategy
          </label>
          <select
            v-model="orchestrationConfig.strategy"
            :disabled="isRunning"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          >
            <option value="sequential">Sequential</option>
            <option value="parallel">Parallel</option>
            <option value="adaptive">Adaptive</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Max Concurrent Agents
          </label>
          <input
            v-model.number="orchestrationConfig.maxConcurrentAgents"
            type="number"
            min="1"
            max="10"
            :disabled="isRunning"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Coordination Mode
          </label>
          <select
            v-model="orchestrationConfig.coordinationMode"
            :disabled="isRunning"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          >
            <option value="centralized">Centralized</option>
            <option value="distributed">Distributed</option>
            <option value="hierarchical">Hierarchical</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Agent Pool -->
    <div class="agent-pool bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
      <div class="border-b border-gray-200 p-6">
        <div class="flex justify-between items-center">
          <h3 class="text-lg font-semibold text-gray-900">Agent Pool</h3>
          <button
            @click="showAgentModal = true"
            class="px-3 py-1 text-sm text-white bg-blue-600 rounded hover:bg-blue-700 transition-colors"
          >
            Add Agent
          </button>
        </div>
      </div>

      <div class="p-6">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="agent in agents"
            :key="agent.id"
            class="agent-card border rounded-lg p-4"
            :class="getAgentCardClass(agent)"
          >
            <div class="flex items-start justify-between mb-3">
              <div class="flex items-center space-x-3">
                <div class="agent-icon w-10 h-10 rounded-full flex items-center justify-center"
                     :class="getAgentIconClass(agent)">
                  <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getAgentIcon(agent.type)"></path>
                  </svg>
                </div>
                <div>
                  <h4 class="font-medium text-gray-900">{{ agent.name }}</h4>
                  <p class="text-sm text-gray-600">{{ agent.type }}</p>
                </div>
              </div>
              <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                    :class="getAgentStatusClass(agent.status)">
                {{ agent.status }}
              </span>
            </div>

            <div class="space-y-2">
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">Tasks:</span>
                <span class="font-medium">{{ agent.current_tasks }}/{{ agent.max_concurrent_tasks }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">Completed:</span>
                <span class="font-medium">{{ agent.tasks_completed }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">Success Rate:</span>
                <span class="font-medium">{{ Math.round(agent.success_rate * 100) }}%</span>
              </div>
            </div>

            <!-- Agent Progress Bar -->
            <div class="mt-3">
              <div class="w-full bg-gray-200 rounded-full h-2">
                <div
                  class="h-2 rounded-full transition-all duration-300"
                  :class="getAgentProgressClass(agent)"
                  :style="{ width: `${(agent.current_tasks / agent.max_concurrent_tasks) * 100}%` }"
                ></div>
              </div>
            </div>

            <!-- Agent Actions -->
            <div class="mt-4 flex space-x-2">
              <button
                @click="viewAgentDetails(agent)"
                class="px-3 py-1 text-sm text-gray-700 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
              >
                Details
              </button>
              <button
                @click="configureAgent(agent)"
                class="px-3 py-1 text-sm text-blue-600 bg-blue-50 rounded hover:bg-blue-100 transition-colors"
              >
                Configure
              </button>
              <button
                v-if="agent.status === 'idle'"
                @click="assignTask(agent)"
                class="px-3 py-1 text-sm text-green-600 bg-green-50 rounded hover:bg-green-100 transition-colors"
              >
                Assign Task
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Task Queue -->
    <div class="task-queue bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
      <div class="border-b border-gray-200 p-6">
        <div class="flex justify-between items-center">
          <h3 class="text-lg font-semibold text-gray-900">Task Queue</h3>
          <div class="flex items-center space-x-4">
            <span class="text-sm text-gray-600">
              {{ pendingTasks.length }} pending, {{ runningTasks.length }} running
            </span>
            <button
              @click="showTaskModal = true"
              class="px-3 py-1 text-sm text-white bg-blue-600 rounded hover:bg-blue-700 transition-colors"
            >
              Add Task
            </button>
          </div>
        </div>
      </div>

      <div class="p-6">
        <!-- Running Tasks -->
        <div v-if="runningTasks.length > 0" class="mb-6">
          <h4 class="font-medium text-gray-900 mb-3">Running Tasks</h4>
          <div class="space-y-3">
            <div
              v-for="task in runningTasks"
              :key="task.id"
              class="border rounded-lg p-4 border-blue-200 bg-blue-50"
            >
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <h5 class="font-medium text-gray-900">{{ task.description }}</h5>
                  <p class="text-sm text-gray-600 mt-1">Type: {{ task.task_type }}</p>
                  <div class="flex items-center space-x-4 mt-2">
                    <span class="text-sm text-gray-600">
                      Assigned to: {{ task.assigned_agent_name }}
                    </span>
                    <span class="text-sm text-gray-600">
                      Started: {{ formatDate(task.started_at) }}
                    </span>
                  </div>
                </div>
                <div class="flex items-center space-x-2">
                  <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  <button
                    @click="cancelTask(task.id)"
                    class="px-2 py-1 text-sm text-red-600 bg-red-50 rounded hover:bg-red-100 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>

              <!-- Task Progress -->
              <div v-if="task.progress" class="mt-3">
                <div class="w-full bg-gray-200 rounded-full h-2">
                  <div
                    class="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    :style="{ width: `${task.progress}%` }"
                  ></div>
                </div>
                <p class="text-xs text-gray-600 mt-1">{{ task.progress }}% complete</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Pending Tasks -->
        <div>
          <h4 class="font-medium text-gray-900 mb-3">Pending Tasks</h4>
          <div v-if="pendingTasks.length === 0" class="text-center py-8 text-gray-500">
            No pending tasks in the queue
          </div>
          <div v-else class="space-y-3">
            <div
              v-for="task in pendingTasks"
              :key="task.id"
              class="border rounded-lg p-4 border-gray-200 hover:bg-gray-50 transition-colors"
            >
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <h5 class="font-medium text-gray-900">{{ task.description }}</h5>
                  <p class="text-sm text-gray-600 mt-1">Type: {{ task.task_type }}</p>
                  <div class="flex items-center space-x-4 mt-2">
                    <span class="text-sm text-gray-600">
                      Priority: {{ task.priority }}
                    </span>
                    <span class="text-sm text-gray-600">
                      Created: {{ formatDate(task.created_at) }}
                    </span>
                  </div>
                </div>
                <div class="flex space-x-2">
                  <button
                    @click="editTask(task)"
                    class="px-2 py-1 text-sm text-gray-600 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
                  >
                    Edit
                  </button>
                  <button
                    @click="removeTask(task.id)"
                    class="px-2 py-1 text-sm text-red-600 bg-red-50 rounded hover:bg-red-100 transition-colors"
                  >
                    Remove
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Real-time Monitoring -->
    <div class="monitoring bg-white rounded-lg shadow-sm border border-gray-200">
      <div class="border-b border-gray-200 p-6">
        <h3 class="text-lg font-semibold text-gray-900">Real-time Monitoring</h3>
      </div>

      <div class="p-6">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="bg-blue-50 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-blue-600 font-medium">Active Agents</p>
                <p class="text-2xl font-bold text-blue-900">{{ activeAgentsCount }}</p>
              </div>
              <div class="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"></path>
                </svg>
              </div>
            </div>
          </div>

          <div class="bg-green-50 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-green-600 font-medium">Tasks Completed</p>
                <p class="text-2xl font-bold text-green-900">{{ totalTasksCompleted }}</p>
              </div>
              <div class="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
              </div>
            </div>
          </div>

          <div class="bg-yellow-50 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-yellow-600 font-medium">Success Rate</p>
                <p class="text-2xl font-bold text-yellow-900">{{ Math.round(overallSuccessRate * 100) }}%</p>
              </div>
              <div class="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center">
                <svg class="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
                </svg>
              </div>
            </div>
          </div>

          <div class="bg-purple-50 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-purple-600 font-medium">Avg Processing Time</p>
                <p class="text-2xl font-bold text-purple-900">{{ averageProcessingTime }}s</p>
              </div>
              <div class="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
              </div>
            </div>
          </div>
        </div>

        <!-- Performance Chart -->
        <div class="mt-6">
          <h4 class="font-medium text-gray-900 mb-3">Performance Timeline</h4>
          <div class="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
            <p class="text-gray-500">Performance chart would be rendered here</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Agent Details Modal -->
    <div v-if="showAgentDetails" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div class="border-b border-gray-200 p-6">
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold text-gray-900">Agent Details</h3>
            <button
              @click="showAgentDetails = false"
              class="text-gray-400 hover:text-gray-600"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
        </div>

        <div v-if="selectedAgent" class="p-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Agent Info -->
            <div>
              <h4 class="font-medium text-gray-900 mb-3">Information</h4>
              <dl class="space-y-2">
                <div class="flex justify-between">
                  <dt class="text-sm text-gray-600">ID:</dt>
                  <dd class="text-sm font-medium">{{ selectedAgent.id }}</dd>
                </div>
                <div class="flex justify-between">
                  <dt class="text-sm text-gray-600">Name:</dt>
                  <dd class="text-sm font-medium">{{ selectedAgent.name }}</dd>
                </div>
                <div class="flex justify-between">
                  <dt class="text-sm text-gray-600">Type:</dt>
                  <dd class="text-sm font-medium">{{ selectedAgent.type }}</dd>
                </div>
                <div class="flex justify-between">
                  <dt class="text-sm text-gray-600">Status:</dt>
                  <dd class="text-sm font-medium">{{ selectedAgent.status }}</dd>
                </div>
                <div class="flex justify-between">
                  <dt class="text-sm text-gray-600">Last Activity:</dt>
                  <dd class="text-sm font-medium">{{ formatDate(selectedAgent.last_activity) }}</dd>
                </div>
              </dl>
            </div>

            <!-- Performance Metrics -->
            <div>
              <h4 class="font-medium text-gray-900 mb-3">Performance</h4>
              <dl class="space-y-2">
                <div class="flex justify-between">
                  <dt class="text-sm text-gray-600">Tasks Completed:</dt>
                  <dd class="text-sm font-medium">{{ selectedAgent.tasks_completed }}</dd>
                </div>
                <div class="flex justify-between">
                  <dt class="text-sm text-gray-600">Tasks Failed:</dt>
                  <dd class="text-sm font-medium">{{ selectedAgent.tasks_failed }}</dd>
                </div>
                <div class="flex justify-between">
                  <dt class="text-sm text-gray-600">Success Rate:</dt>
                  <dd class="text-sm font-medium">{{ Math.round(selectedAgent.success_rate * 100) }}%</dd>
                </div>
                <div class="flex justify-between">
                  <dt class="text-sm text-gray-600">Avg Processing Time:</dt>
                  <dd class="text-sm font-medium">{{ selectedAgent.average_processing_time }}s</dd>
                </div>
                <div class="flex justify-between">
                  <dt class="text-sm text-gray-600">Total Processing Time:</dt>
                  <dd class="text-sm font-medium">{{ selectedAgent.total_processing_time }}s</dd>
                </div>
              </dl>
            </div>
          </div>

          <!-- Agent Capabilities -->
          <div class="mt-6">
            <h4 class="font-medium text-gray-900 mb-3">Capabilities</h4>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
              <span
                v-for="capability in selectedAgent.capabilities"
                :key="capability.name"
                class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium"
                :class="capability.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'"
              >
                {{ capability.name }}
              </span>
            </div>
          </div>

          <!-- Recent Tasks -->
          <div class="mt-6">
            <h4 class="font-medium text-gray-900 mb-3">Recent Tasks</h4>
            <div class="space-y-2">
              <div
                v-for="task in selectedAgent.recent_tasks"
                :key="task.task_id"
                class="p-3 bg-gray-50 rounded-md"
              >
                <div class="flex justify-between items-start">
                  <div>
                    <p class="text-sm font-medium text-gray-900">{{ task.description }}</p>
                    <p class="text-xs text-gray-600 mt-1">
                      {{ task.status }} • {{ formatDate(task.completed_at || task.started_at) }}
                    </p>
                  </div>
                  <span class="text-xs font-medium"
                        :class="task.status === 'completed' ? 'text-green-600' : 'text-red-600'">
                    {{ task.status }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useOrchestratorStore } from '@/stores/orchestrator'
import { useNotificationStore } from '@/stores/notification'

export default {
  name: 'MultiAgentOrchestrator',
  setup() {
    const orchestratorStore = useOrchestratorStore()
    const notificationStore = useNotificationStore()

    // Reactive data
    const isInitialized = ref(false)
    const isRunning = ref(false)
    const showAgentDetails = ref(false)
    const showAgentModal = ref(false)
    const showTaskModal = ref(false)
    const selectedAgent = ref(null)

    // Configuration
    const orchestrationConfig = ref({
      strategy: 'sequential',
      maxConcurrentAgents: 3,
      coordinationMode: 'centralized'
    })

    // Computed properties
    const agents = computed(() => orchestratorStore.agents)
    const tasks = computed(() => orchestratorStore.tasks)
    const runningTasks = computed(() => tasks.value.filter(task => task.status === 'running'))
    const pendingTasks = computed(() => tasks.value.filter(task => task.status === 'pending'))

    const activeAgentsCount = computed(() =>
      agents.value.filter(agent => agent.status === 'working').length
    )

    const totalTasksCompleted = computed(() =>
      agents.value.reduce((total, agent) => total + agent.tasks_completed, 0)
    )

    const overallSuccessRate = computed(() => {
      const totalCompleted = agents.value.reduce((total, agent) => total + agent.tasks_completed, 0)
      const totalFailed = agents.value.reduce((total, agent) => total + agent.tasks_failed, 0)
      const total = totalCompleted + totalFailed
      return total > 0 ? totalCompleted / total : 1.0
    })

    const averageProcessingTime = computed(() => {
      const totalTime = agents.value.reduce((total, agent) => total + agent.average_processing_time, 0)
      return agents.value.length > 0 ? Math.round(totalTime / agents.value.length) : 0
    })

    // Methods
    const initializeOrchestrator = async () => {
      try {
        await orchestratorStore.initialize(orchestrationConfig.value)
        isInitialized.value = true
        notificationStore.showSuccess('Orchestrator initialized successfully')
      } catch (error) {
        notificationStore.showError(`Failed to initialize: ${error.message}`)
      }
    }

    const startOrchestration = async () => {
      try {
        await orchestratorStore.start()
        isRunning.value = true
        notificationStore.showSuccess('Orchestration started')
      } catch (error) {
        notificationStore.showError(`Failed to start: ${error.message}`)
      }
    }

    const pauseOrchestration = async () => {
      try {
        await orchestratorStore.pause()
        isRunning.value = false
        notificationStore.showSuccess('Orchestration paused')
      } catch (error) {
        notificationStore.showError(`Failed to pause: ${error.message}`)
      }
    }

    const stopOrchestration = async () => {
      try {
        await orchestratorStore.stop()
        isRunning.value = false
        notificationStore.showSuccess('Orchestration stopped')
      } catch (error) {
        notificationStore.showError(`Failed to stop: ${error.message}`)
      }
    }

    const viewAgentDetails = (agent) => {
      selectedAgent.value = agent
      showAgentDetails.value = true
    }

    const configureAgent = (agent) => {
      // Open configuration modal for agent
      notificationStore.showInfo(`Configuration for ${agent.name} coming soon`)
    }

    const assignTask = (agent) => {
      // Open task assignment modal
      notificationStore.showInfo(`Task assignment for ${agent.name} coming soon`)
    }

    const cancelTask = async (taskId) => {
      try {
        await orchestratorStore.cancelTask(taskId)
        notificationStore.showSuccess('Task cancelled')
      } catch (error) {
        notificationStore.showError(`Failed to cancel task: ${error.message}`)
      }
    }

    const editTask = (task) => {
      // Open task editing modal
      notificationStore.showInfo('Task editing coming soon')
    }

    const removeTask = async (taskId) => {
      try {
        await orchestratorStore.removeTask(taskId)
        notificationStore.showSuccess('Task removed')
      } catch (error) {
        notificationStore.showError(`Failed to remove task: ${error.message}`)
      }
    }

    // Helper methods
    const getAgentCardClass = (agent) => {
      const classes = {
        'idle': 'border-gray-200 bg-white',
        'working': 'border-blue-200 bg-blue-50',
        'waiting': 'border-yellow-200 bg-yellow-50',
        'error': 'border-red-200 bg-red-50',
        'completed': 'border-green-200 bg-green-50'
      }
      return classes[agent.status] || 'border-gray-200 bg-white'
    }

    const getAgentIconClass = (agent) => {
      const classes = {
        'idle': 'bg-gray-400',
        'working': 'bg-blue-600',
        'waiting': 'bg-yellow-600',
        'error': 'bg-red-600',
        'completed': 'bg-green-600'
      }
      return classes[agent.status] || 'bg-gray-400'
    }

    const getAgentStatusClass = (status) => {
      const classes = {
        'idle': 'bg-gray-100 text-gray-800',
        'working': 'bg-blue-100 text-blue-800',
        'waiting': 'bg-yellow-100 text-yellow-800',
        'error': 'bg-red-100 text-red-800',
        'completed': 'bg-green-100 text-green-800'
      }
      return classes[status] || 'bg-gray-100 text-gray-800'
    }

    const getAgentProgressClass = (agent) => {
      const classes = {
        'idle': 'bg-gray-400',
        'working': 'bg-blue-600',
        'waiting': 'bg-yellow-600',
        'error': 'bg-red-600',
        'completed': 'bg-green-600'
      }
      return classes[agent.status] || 'bg-gray-400'
    }

    const getAgentIcon = (agentType) => {
      const icons = {
        'research_agent': 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
        'evidence_agent': 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253',
        'synthesis_agent': 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z'
      }
      return icons[agentType] || 'M13 10V3L4 14h7v7l9-11h-7z'
    }

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      return new Date(dateString).toLocaleDateString() + ' ' + new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }

    // WebSocket connection for real-time updates
    let wsConnection = null

    const connectWebSocket = () => {
      // This would connect to the orchestrator's WebSocket endpoint
      // For now, we'll use polling
      setInterval(async () => {
        if (isInitialized.value) {
          await orchestratorStore.refreshStatus()
        }
      }, 2000) // Update every 2 seconds
    }

    // Lifecycle
    onMounted(() => {
      connectWebSocket()
    })

    onUnmounted(() => {
      if (wsConnection) {
        wsConnection.close()
      }
    })

    return {
      // Data
      isInitialized,
      isRunning,
      showAgentDetails,
      showAgentModal,
      showTaskModal,
      selectedAgent,
      orchestrationConfig,

      // Computed
      agents,
      tasks,
      runningTasks,
      pendingTasks,
      activeAgentsCount,
      totalTasksCompleted,
      overallSuccessRate,
      averageProcessingTime,

      // Methods
      initializeOrchestrator,
      startOrchestration,
      pauseOrchestration,
      stopOrchestration,
      viewAgentDetails,
      configureAgent,
      assignTask,
      cancelTask,
      editTask,
      removeTask,
      getAgentCardClass,
      getAgentIconClass,
      getAgentStatusClass,
      getAgentProgressClass,
      getAgentIcon,
      formatDate
    }
  }
}
</script>

<style scoped>
.multi-agent-orchestrator {
  max-width: 7xl;
  margin: 0 auto;
  padding: 1rem;
}

.agent-card {
  transition: all 0.2s ease;
}

.agent-card:hover {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

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
</style>