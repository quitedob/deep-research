<template>
  <div class="real-time-monitoring">
    <!-- Header -->
    <div class="monitoring-header">
      <h2 class="text-2xl font-bold text-gray-900 mb-2">Real-time Research Monitoring</h2>
      <p class="text-gray-600">Monitor research progress, agent activities, and system performance in real-time</p>
    </div>

    <!-- Monitoring Controls -->
    <div class="monitoring-controls bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
      <div class="flex justify-between items-center">
        <div class="flex items-center space-x-4">
          <h3 class="text-lg font-semibold text-gray-900">Live Monitoring</h3>
          <div class="flex items-center space-x-2">
            <div class="w-3 h-3 rounded-full"
                 :class="isConnected ? 'bg-green-500' : 'bg-red-500'"></div>
            <span class="text-sm text-gray-600">{{ isConnected ? 'Connected' : 'Disconnected' }}</span>
          </div>
        </div>
        <div class="flex space-x-2">
          <button
            @click="toggleMonitoring"
            :class="isMonitoring ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700'"
            class="px-4 py-2 text-white rounded-md transition-colors"
          >
            {{ isMonitoring ? 'Stop Monitoring' : 'Start Monitoring' }}
          </button>
          <button
            @click="refreshData"
            :disabled="isRefreshing"
            class="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            <span v-if="isRefreshing" class="flex items-center">
              <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Refreshing...
            </span>
            <span v-else>Refresh</span>
          </button>
          <button
            @click="exportLogs"
            :disabled="!monitoringLogs.length"
            class="px-4 py-2 text-white bg-purple-600 rounded-md hover:bg-purple-700 disabled:opacity-50 transition-colors"
          >
            Export Logs
          </button>
        </div>
      </div>

      <!-- Update Interval -->
      <div class="mt-4 flex items-center space-x-4">
        <label class="text-sm font-medium text-gray-700">Update Interval:</label>
        <select
          v-model="updateInterval"
          @change="updateMonitoringInterval"
          :disabled="isMonitoring"
          class="px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        >
          <option value="1000">1 second</option>
          <option value="2000">2 seconds</option>
          <option value="5000">5 seconds</option>
          <option value="10000">10 seconds</option>
        </select>
        <span class="text-sm text-gray-600">Last update: {{ lastUpdate || 'Never' }}</span>
      </div>
    </div>

    <!-- Main Dashboard Grid -->
    <div class="dashboard-grid grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
      <!-- System Overview -->
      <div class="lg:col-span-2 bg-white rounded-lg shadow-sm border border-gray-200">
        <div class="border-b border-gray-200 p-6">
          <h3 class="text-lg font-semibold text-gray-900">System Overview</h3>
        </div>
        <div class="p-6">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="text-center">
              <div class="text-3xl font-bold text-blue-600">{{ activeResearchPlans }}</div>
              <div class="text-sm text-gray-600 mt-1">Active Plans</div>
            </div>
            <div class="text-center">
              <div class="text-3xl font-bold text-green-600">{{ runningAgents }}</div>
              <div class="text-sm text-gray-600 mt-1">Running Agents</div>
            </div>
            <div class="text-center">
              <div class="text-3xl font-bold text-yellow-600">{{ tasksInProgress }}</div>
              <div class="text-sm text-gray-600 mt-1">Tasks in Progress</div>
            </div>
            <div class="text-center">
              <div class="text-3xl font-bold text-purple-600">{{ totalEvidenceCollected }}</div>
              <div class="text-sm text-gray-600 mt-1">Evidence Items</div>
            </div>
          </div>

          <!-- Performance Chart -->
          <div class="mt-6">
            <h4 class="font-medium text-gray-900 mb-3">Performance Trend</h4>
            <div class="h-48 bg-gray-50 rounded-lg flex items-center justify-center">
              <div class="text-center">
                <svg class="w-12 h-12 text-gray-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                </svg>
                <p class="text-gray-500">Performance chart visualization</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- System Health -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-200">
        <div class="border-b border-gray-200 p-6">
          <h3 class="text-lg font-semibold text-gray-900">System Health</h3>
        </div>
        <div class="p-6 space-y-4">
          <div>
            <div class="flex justify-between text-sm mb-1">
              <span class="text-gray-600">CPU Usage</span>
              <span class="font-medium">{{ systemHealth.cpu }}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div
                class="h-2 rounded-full transition-all duration-300"
                :class="getHealthClass(systemHealth.cpu)"
                :style="{ width: `${systemHealth.cpu}%` }"
              ></div>
            </div>
          </div>

          <div>
            <div class="flex justify-between text-sm mb-1">
              <span class="text-gray-600">Memory Usage</span>
              <span class="font-medium">{{ systemHealth.memory }}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div
                class="h-2 rounded-full transition-all duration-300"
                :class="getHealthClass(systemHealth.memory)"
                :style="{ width: `${systemHealth.memory}%` }"
              ></div>
            </div>
          </div>

          <div>
            <div class="flex justify-between text-sm mb-1">
              <span class="text-gray-600">Response Time</span>
              <span class="font-medium">{{ systemHealth.responseTime }}ms</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div
                class="h-2 rounded-full transition-all duration-300"
                :class="getResponseTimeClass(systemHealth.responseTime)"
                :style="{ width: `${Math.min(systemHealth.responseTime / 10, 100)}%` }"
              ></div>
            </div>
          </div>

          <div>
            <div class="flex justify-between text-sm mb-1">
              <span class="text-gray-600">Error Rate</span>
              <span class="font-medium">{{ systemHealth.errorRate }}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div
                class="h-2 rounded-full transition-all duration-300"
                :class="getErrorRateClass(systemHealth.errorRate)"
                :style="{ width: `${systemHealth.errorRate}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Agent Activities -->
    <div class="agent-activities bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
      <div class="border-b border-gray-200 p-6">
        <div class="flex justify-between items-center">
          <h3 class="text-lg font-semibold text-gray-900">Agent Activities</h3>
          <div class="flex space-x-2">
            <button
              @click="filterActivities('all')"
              :class="activityFilter === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'"
              class="px-3 py-1 text-sm rounded-md transition-colors"
            >
              All
            </button>
            <button
              @click="filterActivities('active')"
              :class="activityFilter === 'active' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'"
              class="px-3 py-1 text-sm rounded-md transition-colors"
            >
              Active
            </button>
            <button
              @click="filterActivities('completed')"
              :class="activityFilter === 'completed' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'"
              class="px-3 py-1 text-sm rounded-md transition-colors"
            >
              Completed
            </button>
            <button
              @click="filterActivities('errors')"
              :class="activityFilter === 'errors' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'"
              class="px-3 py-1 text-sm rounded-md transition-colors"
            >
              Errors
            </button>
          </div>
        </div>
      </div>

      <div class="p-6">
        <div v-if="filteredActivities.length === 0" class="text-center py-8">
          <svg class="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path>
          </svg>
          <p class="text-gray-500">No agent activities found</p>
        </div>

        <div v-else class="space-y-4">
          <div
            v-for="activity in filteredActivities.slice(0, 10)"
            :key="activity.id"
            class="activity-item flex items-start space-x-4 p-4 border rounded-lg hover:bg-gray-50 transition-colors"
            :class="getActivityClass(activity)"
          >
            <div class="activity-icon flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center"
                 :class="getActivityIconClass(activity)">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getActivityIcon(activity.type)"></path>
              </svg>
            </div>
            <div class="flex-1">
              <div class="flex items-start justify-between">
                <div>
                  <h4 class="font-medium text-gray-900">{{ activity.agentName }}</h4>
                  <p class="text-sm text-gray-600 mt-1">{{ activity.description }}</p>
                </div>
                <div class="text-right">
                  <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                        :class="getActivityStatusClass(activity.status)">
                    {{ activity.status }}
                  </span>
                  <p class="text-xs text-gray-500 mt-1">{{ formatTime(activity.timestamp) }}</p>
                </div>
              </div>

              <!-- Activity Progress -->
              <div v-if="activity.progress !== undefined" class="mt-3">
                <div class="flex justify-between text-xs text-gray-600 mb-1">
                  <span>Progress</span>
                  <span>{{ activity.progress }}%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-1">
                  <div
                    class="h-1 rounded-full transition-all duration-300"
                    :class="getActivityProgressClass(activity.status)"
                    :style="{ width: `${activity.progress}%` }"
                  ></div>
                </div>
              </div>

              <!-- Activity Details -->
              <div v-if="activity.details" class="mt-3">
                <button
                  @click="toggleActivityDetails(activity.id)"
                  class="text-xs text-blue-600 hover:text-blue-800 transition-colors"
                >
                  {{ expandedActivities.includes(activity.id) ? 'Hide' : 'Show' }} Details
                </button>
                <div v-if="expandedActivities.includes(activity.id)" class="mt-2 p-3 bg-gray-50 rounded text-sm text-gray-700">
                  {{ activity.details }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Live Event Log -->
    <div class="event-log bg-white rounded-lg shadow-sm border border-gray-200">
      <div class="border-b border-gray-200 p-6">
        <div class="flex justify-between items-center">
          <h3 class="text-lg font-semibold text-gray-900">Live Event Log</h3>
          <div class="flex items-center space-x-4">
            <div class="flex items-center space-x-2">
              <input
                v-model="logFilter"
                type="text"
                placeholder="Filter logs..."
                class="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div class="flex items-center space-x-2">
              <input
                v-model="autoScroll"
                type="checkbox"
                id="autoScroll"
                class="rounded"
              />
              <label for="autoScroll" class="text-sm text-gray-600">Auto-scroll</label>
            </div>
            <button
              @click="clearLogs"
              class="px-3 py-1 text-sm text-red-600 bg-red-50 rounded hover:bg-red-100 transition-colors"
            >
              Clear
            </button>
          </div>
        </div>
      </div>

      <div class="p-6">
        <div ref="logContainer" class="log-container h-64 overflow-y-auto bg-gray-900 rounded-lg p-4 font-mono text-sm">
          <div
            v-for="log in filteredLogs"
            :key="log.id"
            class="log-entry mb-2"
            :class="getLogClass(log.level)"
          >
            <span class="log-timestamp text-gray-400">[{{ formatLogTime(log.timestamp) }}]</span>
            <span class="log-level ml-2 font-bold" :class="getLogLevelClass(log.level)">[{{ log.level.toUpperCase() }}]</span>
            <span class="log-source ml-2 text-blue-400">{{ log.source }}:</span>
            <span class="log-message ml-2">{{ log.message }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Alert Notifications -->
    <div v-if="alerts.length > 0" class="fixed bottom-4 right-4 space-y-2 z-50">
      <div
        v-for="alert in alerts"
        :key="alert.id"
        class="alert-notification bg-white rounded-lg shadow-lg border-l-4 p-4 max-w-md"
        :class="getAlertClass(alert.level)"
      >
        <div class="flex items-start">
          <div class="flex-shrink-0">
            <svg class="w-5 h-5" :class="getAlertIconClass(alert.level)" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getAlertIcon(alert.level)"></path>
            </svg>
          </div>
          <div class="ml-3 flex-1">
            <h4 class="font-medium text-gray-900">{{ alert.title }}</h4>
            <p class="text-sm text-gray-600 mt-1">{{ alert.message }}</p>
          </div>
          <button
            @click="dismissAlert(alert.id)"
            class="ml-3 text-gray-400 hover:text-gray-600"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useOrchestratorStore } from '@/stores/orchestrator'
import { useResearchStore } from '@/stores/research'
import { useNotificationStore } from '@/stores/notification'

export default {
  name: 'RealTimeMonitoring',
  setup() {
    const orchestratorStore = useOrchestratorStore()
    const researchStore = useResearchStore()
    const notificationStore = useNotificationStore()

    // Reactive data
    const isMonitoring = ref(false)
    const isConnected = ref(false)
    const isRefreshing = ref(false)
    const updateInterval = ref(2000)
    const lastUpdate = ref('')
    const activityFilter = ref('all')
    const logFilter = ref('')
    const autoScroll = ref(true)
    const expandedActivities = ref([])
    const logContainer = ref(null)

    // Monitoring data
    const monitoringLogs = ref([])
    const agentActivities = ref([])
    const systemHealth = ref({
      cpu: 0,
      memory: 0,
      responseTime: 0,
      errorRate: 0
    })
    const alerts = ref([])

    // WebSocket connection
    let wsConnection = null
    let monitoringTimer = null

    // Computed properties
    const activeResearchPlans = computed(() => {
      return researchStore.currentPlan ? 1 : 0
    })

    const runningAgents = computed(() => {
      return orchestratorStore.activeAgents.length
    })

    const tasksInProgress = computed(() => {
      return orchestratorStore.runningTasks.length
    })

    const totalEvidenceCollected = computed(() => {
      if (researchStore.currentPlan) {
        const chain = researchStore.evidenceChains[researchStore.currentPlan.id]
        return chain ? chain.evidence_items.length : 0
      }
      return 0
    })

    const filteredActivities = computed(() => {
      let activities = agentActivities.value

      if (activityFilter.value === 'active') {
        activities = activities.filter(a => a.status === 'running')
      } else if (activityFilter.value === 'completed') {
        activities = activities.filter(a => a.status === 'completed')
      } else if (activityFilter.value === 'errors') {
        activities = activities.filter(a => a.status === 'error')
      }

      return activities.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
    })

    const filteredLogs = computed(() => {
      if (!logFilter.value) {
        return monitoringLogs.value
      }

      const filter = logFilter.value.toLowerCase()
      return monitoringLogs.value.filter(log =>
        log.message.toLowerCase().includes(filter) ||
        log.source.toLowerCase().includes(filter) ||
        log.level.toLowerCase().includes(filter)
      )
    })

    // Methods
    const startMonitoring = () => {
      isMonitoring.value = true
      connectWebSocket()
      startPeriodicUpdates()
      addLog('info', 'monitoring', 'Real-time monitoring started')
    }

    const stopMonitoring = () => {
      isMonitoring.value = false
      disconnectWebSocket()
      stopPeriodicUpdates()
      addLog('info', 'monitoring', 'Real-time monitoring stopped')
    }

    const toggleMonitoring = () => {
      if (isMonitoring.value) {
        stopMonitoring()
      } else {
        startMonitoring()
      }
    }

    const connectWebSocket = () => {
      try {
        // This would connect to the actual WebSocket endpoint
        // For now, we'll simulate the connection
        isConnected.value = true

        // Simulate receiving messages
        wsConnection = {
          close: () => {
            isConnected.value = false
          }
        }

        addLog('info', 'websocket', 'Connected to monitoring WebSocket')
      } catch (error) {
        console.error('Failed to connect WebSocket:', error)
        isConnected.value = false
        addLog('error', 'websocket', `Failed to connect: ${error.message}`)
      }
    }

    const disconnectWebSocket = () => {
      if (wsConnection) {
        wsConnection.close()
        wsConnection = null
      }
    }

    const startPeriodicUpdates = () => {
      if (monitoringTimer) {
        clearInterval(monitoringTimer)
      }

      monitoringTimer = setInterval(() => {
        if (isMonitoring.value) {
          refreshData()
        }
      }, updateInterval.value)
    }

    const stopPeriodicUpdates = () => {
      if (monitoringTimer) {
        clearInterval(monitoringTimer)
        monitoringTimer = null
      }
    }

    const updateMonitoringInterval = () => {
      if (isMonitoring.value) {
        stopPeriodicUpdates()
        startPeriodicUpdates()
      }
    }

    const refreshData = async () => {
      if (isRefreshing.value) return

      isRefreshing.value = true
      try {
        // Refresh orchestrator and research data
        await Promise.all([
          orchestratorStore.refreshStatus(),
          researchStore.loadCurrentPlan()
        ])

        // Update system health (simulated)
        updateSystemHealth()

        // Generate simulated agent activities
        generateAgentActivities()

        lastUpdate.value = new Date().toLocaleTimeString()
        addLog('debug', 'monitor', 'Data refreshed successfully')
      } catch (error) {
        console.error('Failed to refresh data:', error)
        addLog('error', 'monitor', `Failed to refresh data: ${error.message}`)
      } finally {
        isRefreshing.value = false
      }
    }

    const updateSystemHealth = () => {
      // Simulated system health metrics
      systemHealth.value = {
        cpu: Math.floor(Math.random() * 30) + 20, // 20-50%
        memory: Math.floor(Math.random() * 40) + 40, // 40-80%
        responseTime: Math.floor(Math.random() * 200) + 50, // 50-250ms
        errorRate: Math.floor(Math.random() * 5) // 0-5%
      }

      // Check for alerts
      checkSystemAlerts()
    }

    const generateAgentActivities = () => {
      // Generate simulated agent activities based on current agents
      const agents = orchestratorStore.agents
      const tasks = orchestratorStore.tasks

      agents.forEach(agent => {
        if (agent.status === 'working') {
          const existingActivity = agentActivities.value.find(
            a => a.agentId === agent.id && a.status === 'running'
          )

          if (!existingActivity) {
            agentActivities.value.push({
              id: `activity_${Date.now()}_${agent.id}`,
              agentId: agent.id,
              agentName: agent.name,
              type: 'task_execution',
              description: `Processing research task`,
              status: 'running',
              progress: Math.floor(Math.random() * 100),
              timestamp: new Date().toISOString(),
              details: `Agent is currently processing ${agent.current_tasks} tasks`
            })
          }
        }
      })

      // Limit activities to last 50
      agentActivities.value = agentActivities.value.slice(-50)
    }

    const checkSystemAlerts = () => {
      const health = systemHealth.value

      // CPU alert
      if (health.cpu > 80) {
        createAlert('warning', 'High CPU Usage', `CPU usage is at ${health.cpu}%`)
      }

      // Memory alert
      if (health.memory > 85) {
        createAlert('error', 'High Memory Usage', `Memory usage is at ${health.memory}%`)
      }

      // Response time alert
      if (health.responseTime > 500) {
        createAlert('warning', 'Slow Response Time', `Response time is ${health.responseTime}ms`)
      }

      // Error rate alert
      if (health.errorRate > 3) {
        createAlert('error', 'High Error Rate', `Error rate is ${health.errorRate}%`)
      }
    }

    const createAlert = (level, title, message) => {
      const existingAlert = alerts.value.find(
        a => a.title === title && a.level === level
      )

      if (!existingAlert) {
        alerts.value.push({
          id: `alert_${Date.now()}`,
          level,
          title,
          message,
          timestamp: new Date().toISOString()
        })

        addLog(level, 'alert', `${title}: ${message}`)

        // Auto-dismiss after 10 seconds
        setTimeout(() => {
          dismissAlert(`alert_${Date.now()}`)
        }, 10000)
      }
    }

    const dismissAlert = (alertId) => {
      const index = alerts.value.findIndex(a => a.id === alertId)
      if (index !== -1) {
        alerts.value.splice(index, 1)
      }
    }

    const addLog = (level, source, message) => {
      monitoringLogs.value.push({
        id: `log_${Date.now()}_${Math.random()}`,
        level,
        source,
        message,
        timestamp: new Date().toISOString()
      })

      // Keep only last 1000 logs
      if (monitoringLogs.value.length > 1000) {
        monitoringLogs.value = monitoringLogs.value.slice(-1000)
      }

      // Auto-scroll to bottom
      if (autoScroll.value) {
        nextTick(() => {
          if (logContainer.value) {
            logContainer.value.scrollTop = logContainer.value.scrollHeight
          }
        })
      }
    }

    const filterActivities = (filter) => {
      activityFilter.value = filter
    }

    const toggleActivityDetails = (activityId) => {
      const index = expandedActivities.value.indexOf(activityId)
      if (index === -1) {
        expandedActivities.value.push(activityId)
      } else {
        expandedActivities.value.splice(index, 1)
      }
    }

    const clearLogs = () => {
      monitoringLogs.value = []
      addLog('info', 'monitoring', 'Log cleared')
    }

    const exportLogs = () => {
      const data = {
        logs: monitoringLogs.value,
        activities: agentActivities.value,
        systemHealth: systemHealth.value,
        exportDate: new Date().toISOString()
      }

      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `monitoring-logs-${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      notificationStore.showSuccess('Monitoring logs exported successfully')
    }

    // Helper methods
    const getHealthClass = (value) => {
      if (value < 50) return 'bg-green-500'
      if (value < 80) return 'bg-yellow-500'
      return 'bg-red-500'
    }

    const getResponseTimeClass = (time) => {
      if (time < 100) return 'bg-green-500'
      if (time < 300) return 'bg-yellow-500'
      return 'bg-red-500'
    }

    const getErrorRateClass = (rate) => {
      if (rate < 1) return 'bg-green-500'
      if (rate < 3) return 'bg-yellow-500'
      return 'bg-red-500'
    }

    const getActivityClass = (activity) => {
      const classes = {
        'running': 'border-blue-200 bg-blue-50',
        'completed': 'border-green-200 bg-green-50',
        'error': 'border-red-200 bg-red-50'
      }
      return classes[activity.status] || 'border-gray-200 bg-gray-50'
    }

    const getActivityIconClass = (activity) => {
      const classes = {
        'running': 'bg-blue-600',
        'completed': 'bg-green-600',
        'error': 'bg-red-600'
      }
      return classes[activity.status] || 'bg-gray-600'
    }

    const getActivityStatusClass = (status) => {
      const classes = {
        'running': 'bg-blue-100 text-blue-800',
        'completed': 'bg-green-100 text-green-800',
        'error': 'bg-red-100 text-red-800'
      }
      return classes[status] || 'bg-gray-100 text-gray-800'
    }

    const getActivityProgressClass = (status) => {
      const classes = {
        'running': 'bg-blue-600',
        'completed': 'bg-green-600',
        'error': 'bg-red-600'
      }
      return classes[status] || 'bg-gray-600'
    }

    const getLogClass = (level) => {
      return {
        'error': 'text-red-400',
        'warning': 'text-yellow-400',
        'info': 'text-blue-400'
      }[level] || 'text-gray-400'
    }

    const getLogLevelClass = (level) => {
      return {
        'error': 'text-red-500',
        'warning': 'text-yellow-500',
        'info': 'text-blue-500'
      }[level] || 'text-gray-500'
    }

    const getAlertClass = (level) => {
      return {
        'error': 'border-red-500',
        'warning': 'border-yellow-500',
        'info': 'border-blue-500'
      }[level] || 'border-gray-500'
    }

    const getAlertIconClass = (level) => {
      return {
        'error': 'text-red-500',
        'warning': 'text-yellow-500',
        'info': 'text-blue-500'
      }[level] || 'text-gray-500'
    }

    const getActivityIcon = (type) => {
      const icons = {
        'task_execution': 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z',
        'evidence_collection': 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253',
        'synthesis': 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z'
      }
      return icons[type] || 'M13 10V3L4 14h7v7l9-11h-7z'
    }

    const getAlertIcon = (level) => {
      const icons = {
        'error': 'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
        'warning': 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.314 16.5c-.77.833.192 2.5 1.732 2.5z',
        'info': 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
      }
      return icons[level] || icons.info
    }

    const formatTime = (timestamp) => {
      return new Date(timestamp).toLocaleTimeString()
    }

    const formatLogTime = (timestamp) => {
      return new Date(timestamp).toLocaleTimeString()
    }

    // Auto-scroll monitoring
    watch(filteredLogs, () => {
      if (autoScroll.value && logContainer.value) {
        nextTick(() => {
          logContainer.value.scrollTop = logContainer.value.scrollHeight
        })
      }
    })

    // Lifecycle
    onMounted(() => {
      // Initialize with current data
      refreshData()
    })

    onUnmounted(() => {
      stopMonitoring()
    })

    return {
      // Data
      isMonitoring,
      isConnected,
      isRefreshing,
      updateInterval,
      lastUpdate,
      activityFilter,
      logFilter,
      autoScroll,
      expandedActivities,
      logContainer,
      monitoringLogs,
      agentActivities,
      systemHealth,
      alerts,

      // Computed
      activeResearchPlans,
      runningAgents,
      tasksInProgress,
      totalEvidenceCollected,
      filteredActivities,
      filteredLogs,

      // Methods
      toggleMonitoring,
      refreshData,
      updateMonitoringInterval,
      filterActivities,
      toggleActivityDetails,
      clearLogs,
      exportLogs,
      getHealthClass,
      getResponseTimeClass,
      getErrorRateClass,
      getActivityClass,
      getActivityIconClass,
      getActivityStatusClass,
      getActivityProgressClass,
      getLogClass,
      getLogLevelClass,
      getAlertClass,
      getAlertIconClass,
      getActivityIcon,
      getAlertIcon,
      formatTime,
      formatLogTime
    }
  }
}
</script>

<style scoped>
.real-time-monitoring {
  max-width: 7xl;
  margin: 0 auto;
  padding: 1rem;
}

.activity-item {
  transition: all 0.2s ease;
}

.log-container {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.log-entry {
  transition: background-color 0.1s ease;
}

.log-entry:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.alert-notification {
  animation: slideIn 0.3s ease;
  max-width: 20rem;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* Custom scrollbar for log container */
.log-container::-webkit-scrollbar {
  width: 8px;
}

.log-container::-webkit-scrollbar-track {
  background: #1f2937;
  border-radius: 4px;
}

.log-container::-webkit-scrollbar-thumb {
  background: #4b5563;
  border-radius: 4px;
}

.log-container::-webkit-scrollbar-thumb:hover {
  background: #6b7280;
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