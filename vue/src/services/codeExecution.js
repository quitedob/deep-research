// 代码执行API服务

const API_BASE_URL = import.meta.env.VITE_APP_API_BASE_URL || '/api'

// 代码执行相关API
export const codeExecutionAPI = {
  // 执行Python代码
  executeCode: async (code, options = {}) => {
    try {
      const response = await fetch(`${API_BASE_URL}/code-sandbox/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')}`,
        },
        body: JSON.stringify({
          code,
          timeout: options.timeout || 30,
          memory_limit_mb: options.memory_limit_mb || 100,
          context: options.context || {}
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('代码执行失败:', error)
      throw error
    }
  },

  // 验证代码安全性
  validateCode: async (code, options = {}) => {
    try {
      const response = await fetch(`${API_BASE_URL}/code-sandbox/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')}`,
        },
        body: JSON.stringify({
          code,
          timeout: options.timeout || 30,
          memory_limit_mb: options.memory_limit_mb || 100
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('代码验证失败:', error)
      throw error
    }
  },

  // 获取代码执行历史
  getHistory: async (params = {}) => {
    try {
      const queryString = new URLSearchParams(params).toString()
      const response = await fetch(`${API_BASE_URL}/code-sandbox/history?${queryString}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')}`,
        },
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('获取历史记录失败:', error)
      throw error
    }
  },

  // 删除历史记录
  deleteHistoryItem: async (itemId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/code-sandbox/history/${itemId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')}`,
        },
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('删除历史记录失败:', error)
      throw error
    }
  },

  // 清空历史记录
  clearHistory: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/code-sandbox/history`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')}`,
        },
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('清空历史记录失败:', error)
      throw error
    }
  },

  // 获取可用的模块列表
  getAvailableModules: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/code-sandbox/modules`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')}`,
        },
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('获取模块列表失败:', error)
      throw error
    }
  }
}

// 兼容性函数 - 向后兼容
export async function executePythonCode(code, options = {}) {
  try {
    const result = await codeExecutionAPI.executeCode(code, options)

    // 转换为统一的响应格式
    return {
      success: result.success || true,
      output: result.output || '',
      error: result.error || '',
      execution_time: result.execution_time || 0,
      variables: result.variables || {}
    }
  } catch (error) {
    return {
      success: false,
      output: '',
      error: error.message,
      execution_time: 0,
      variables: {}
    }
  }
}

export async function validatePythonCode(code, options = {}) {
  try {
    const result = await codeExecutionAPI.validateCode(code, options)
    return result
  } catch (error) {
    return {
      is_safe: false,
      errors: [error.message],
      warnings: [],
      stats: null
    }
  }
}

// 导出默认API
export default codeExecutionAPI