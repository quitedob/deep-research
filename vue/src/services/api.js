// API 服务：统一管理所有后端API调用

// API基础URL配置 - 支持环境变量或默认值
const API_BASE_URL = (typeof import.meta.env !== 'undefined' && import.meta.env.VITE_APP_API_BASE_URL)
  ? import.meta.env.VITE_APP_API_BASE_URL
  : '/api'; // 使用相对路径，通过Vite代理到后端

// CSRF Token管理
let csrfToken = null;

// 获取CSRF token
async function getCSRFToken() {
  if (!csrfToken) {
    // 通过一个GET请求获取CSRF token
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      credentials: 'include'
    });
    if (response.ok) {
      csrfToken = response.headers.get('X-CSRF-Token');
    }
  }
  return csrfToken;
}

// 通用请求函数
async function apiRequest(endpoint, options = {}) {
  // 处理查询参数
  let url = `${API_BASE_URL}${endpoint}`;
  if (options.params) {
    const searchParams = new URLSearchParams();
    Object.entries(options.params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value);
      }
    });
    const paramString = searchParams.toString();
    if (paramString) {
      url += (endpoint.includes('?') ? '&' : '?') + paramString;
    }
    delete options.params; // 从options中移除params
  }

  console.log('[API] 请求开始', { endpoint, method: options.method || 'GET', url });

  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    credentials: 'include', // 包含cookies
  };

  const config = { ...defaultOptions, ...options };

  // 添加认证token
  const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
    console.log('[API] 已添加JWT token到请求头');
  } else {
    console.log('[API] 未找到JWT token，请求可能需要认证');
  }

  // 对于POST/PUT/PATCH/DELETE请求，添加CSRF token
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(config.method?.toUpperCase())) {
    const csrfToken = await getCSRFToken();
    if (csrfToken) {
      config.headers['X-CSRF-Token'] = csrfToken;
      console.log('[API] 已添加CSRF token到请求头');
    }
  }

  console.log('[API] 发送请求', { url, method: config.method, headers: { ...config.headers, Authorization: config.headers.Authorization ? 'Bearer [TOKEN]' : undefined } });

  try {
    const response = await fetch(url, config);
    console.log('[API] 收到响应', { url, status: response.status, ok: response.ok });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.log('[API] 请求失败', { status: response.status, errorData });

      // 如果是CSRF错误，清空token并重试
      if (response.status === 403 && errorData.detail?.includes('CSRF')) {
        console.log('[API] CSRF错误，尝试重新获取token并重试');
        csrfToken = null;
        const newToken = await getCSRFToken();
        if (newToken) {
          config.headers['X-CSRF-Token'] = newToken;
          console.log('[API] 使用新CSRF token重试请求');
          const retryResponse = await fetch(url, config);
          console.log('[API] 重试响应', { status: retryResponse.status, ok: retryResponse.ok });
          if (!retryResponse.ok) {
            const retryErrorData = await retryResponse.json().catch(() => ({}));
            throw new Error(retryErrorData.detail || `HTTP ${retryResponse.status}: ${retryResponse.statusText}`);
          }
          return await retryResponse.json();
        }
      }

      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    const responseData = await response.json();
    console.log('[API] 请求成功', { url, hasData: !!responseData, dataKeys: Object.keys(responseData) });
    return responseData;
  } catch (error) {
    console.error('[API] 请求异常', { url, error: error.message, stack: error.stack });
    throw error;
  }
}

// 研究相关API
export const researchAPI = {
  // 开始研究任务
  startResearch: async (query, sessionId = null) => {
    try {
      console.log('[ResearchAPI] 开始研究任务:', { query, sessionId });
      const result = await apiRequest('/research', {
        method: 'POST',
        body: JSON.stringify({
          query: query,
          session_id: sessionId
        })
      });
      console.log('[ResearchAPI] 研究任务创建成功:', { sessionId: result.session_id, status: result.status });
      return result;
    } catch (error) {
      console.error('[ResearchAPI] 研究任务创建失败:', error);
      throw error;
    }
  },

  // 获取研究报告
  getReport: async (sessionId) => {
    return await apiRequest(`/research/${sessionId}`);
  },

  // 获取研究流进度
  getStream: async (sessionId) => {
    const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
    const url = `${API_BASE_URL}/research/stream/${sessionId}`;

    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      },
      credentials: 'include'
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response;
  }
};

// 文档相关API
export const documentAPI = {
  // 上传文件
  uploadFile: async (file) => {
    try {
      const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
      const formData = new FormData();
      formData.append('file', file);

      console.log('[DocumentAPI] 开始上传文件:', { filename: file.name, size: file.size });

      const response = await fetch(`${API_BASE_URL}/files/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData,
        credentials: 'include'
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.detail || `HTTP ${response.status}: ${response.statusText}`;
        console.error('[DocumentAPI] 文件上传失败:', { status: response.status, error: errorMessage });
        throw new Error(errorMessage);
      }

      const result = await response.json();
      console.log('[DocumentAPI] 文件上传成功:', { fileId: result.file_id, status: result.status });
      return result;
    } catch (error) {
      console.error('[DocumentAPI] 文件上传异常:', error);
      throw error;
    }
  },

  // 获取文件状态
  getFileStatus: async (fileId) => {
    return await apiRequest(`/files/${fileId}/status`);
  },

  // 获取文件列表
  getFiles: async (skip = 0, limit = 50) => {
    return await apiRequest('/files/list', {
      params: { skip, limit }
    });
  },

  // 删除文件
  deleteFile: async (fileId) => {
    return await apiRequest(`/files/${fileId}`, {
      method: 'DELETE'
    });
  }
};

// 反馈相关API
export const feedbackAPI = {
  // 提交反馈
  submitFeedback: async (messageId, rating, comment = null, feedbackType = null, context = null) => {
    return await apiRequest('/feedback/submit', {
      method: 'POST',
      body: JSON.stringify({
        message_id: messageId,
        rating: rating,
        comment: comment,
        feedback_type: feedbackType,
        context: context
      })
    });
  },

  // 获取消息反馈
  getMessageFeedback: async (messageId) => {
    return await apiRequest(`/feedback/message/${messageId}`);
  },

  // 获取用户反馈统计
  getUserStats: async () => {
    return await apiRequest('/feedback/user/stats');
  },

  // 获取全局反馈统计（管理员）
  getGlobalStats: async () => {
    return await apiRequest('/feedback/global/stats');
  },

  // 删除反馈
  deleteFeedback: async (messageId) => {
    return await apiRequest(`/feedback/message/${messageId}`, {
      method: 'DELETE'
    });
  }
};

// 认证相关API
export const authAPI = {
  // 用户登录
  login: (credentials) => {
    console.log('[AuthAPI] 用户登录请求', { username: credentials.username });
    // OAuth2PasswordRequestForm 需要使用 URL编码的表单数据，不是JSON
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    return apiRequest('/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });
  },

  // 用户注册
  register: (userData) => {
    console.log('[AuthAPI] 用户注册请求', { username: userData.username, email: userData.email });
    return apiRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  },

  // 获取当前用户信息
  getCurrentUser: () => {
    console.log('[AuthAPI] 获取当前用户信息');
    return apiRequest('/auth/me');
  },

  // 刷新令牌
  refreshToken: () => {
    console.log('[AuthAPI] 刷新令牌请求');
    return apiRequest('/auth/refresh');
  },
};

// 聊天相关API
export const chatAPI = {
  // 发送消息
  sendMessage: (message) => apiRequest('/chat', {
    method: 'POST',
    body: JSON.stringify(message),
  }),

  // 获取聊天历史
  getChatHistory: (sessionId) => apiRequest(`/chat/history/${sessionId}`),

  // 创建新会话
  createSession: (title) => apiRequest('/chat/sessions', {
    method: 'POST',
    body: JSON.stringify({ title }),
  }),
};

// 内容审核相关API
export const moderationAPI = {
  // 获取审核队列
  getModerationQueue: (status = 'pending', page = 1, pageSize = 20) => {
    return apiRequest('/admin/moderation/queue', {
      params: { status, page, page_size: pageSize }
    });
  },

  // 审核内容（批准/拒绝）
  moderateContent: (queueId, action, reason = '') => {
    return apiRequest(`/admin/moderation/${queueId}/review`, {
      method: 'POST',
      body: JSON.stringify({
        action: action, // 'approve' or 'reject'
        reason: reason
      })
    });
  },

  // 批量审核
  batchModerate: (queueIds, action, reason = '') => {
    return apiRequest('/admin/moderation/batch-review', {
      method: 'POST',
      body: JSON.stringify({
        queue_ids: queueIds,
        action: action,
        reason: reason
      })
    });
  },

  // 获取审核统计
  getModerationStats: () => {
    return apiRequest('/admin/moderation/stats');
  },

  // 获取审核历史
  getModerationHistory: (page = 1, pageSize = 20) => {
    return apiRequest('/admin/moderation/history', {
      params: { page, page_size: pageSize }
    });
  }
};

// 智能体配置相关API
export const agentConfigAPI = {
  // 获取所有智能体配置
  getAgentConfigs: () => {
    return apiRequest('/agent-llm-config/all');
  },

  // 获取特定智能体配置
  getAgentConfig: (agentId) => {
    return apiRequest(`/agent-llm-config/${agentId}`);
  },

  // 更新智能体配置
  updateAgentConfig: (agentId, config) => {
    return apiRequest(`/agent-llm-config/${agentId}`, {
      method: 'PUT',
      body: JSON.stringify(config)
    });
  },

  // 批量更新智能体配置
  batchUpdateConfigs: (configs) => {
    return apiRequest('/agent-llm-config/batch-update', {
      method: 'PUT',
      body: JSON.stringify({ configs })
    });
  },

  // 重置为默认配置
  resetToDefaults: () => {
    return apiRequest('/agent-llm-config/reset-to-defaults', {
      method: 'POST'
    });
  },

  // 测试智能体配置
  testAgentConfig: (agentId, prompt) => {
    return apiRequest(`/agent-llm-config/${agentId}/test`, {
      method: 'POST',
      body: JSON.stringify({ prompt })
    });
  },

  // 获取可用的LLM提供商和模型
  getAvailableModels: () => {
    return apiRequest('/agent-llm-config/available-models');
  }
};

// LLM配置相关API
export const llmConfigAPI = {
  // 获取当前LLM配置
  getCurrentConfig: () => apiRequest('/llm-config/current'),

  // 更新LLM配置
  updateConfig: (config) => apiRequest('/llm-config/update', {
    method: 'PUT',
    body: JSON.stringify(config),
  }),

  // 测试连接
  testConnection: () => apiRequest('/llm-config/test-connection'),
};

// 对话记忆相关API
export const conversationAPI = {
  // 获取对话会话列表
  getSessions: (page = 1, pageSize = 20) => 
    apiRequest(`/conversation/sessions?page=${page}&page_size=${pageSize}`),

  // 创建新对话会话
  createSession: (request) => apiRequest('/conversation/sessions', {
    method: 'POST',
    body: JSON.stringify(request),
  }),

  // 获取对话详情
  getSessionDetail: (sessionId) => apiRequest(`/conversation/sessions/${sessionId}`),

  // 向对话添加消息
  addMessage: (sessionId, message) => apiRequest(`/conversation/sessions/${sessionId}/messages`, {
    method: 'POST',
    body: JSON.stringify(message),
  }),

  // 删除对话会话
  deleteSession: (sessionId) => apiRequest(`/conversation/sessions/${sessionId}`, {
    method: 'DELETE',
  }),

  // 获取记忆摘要
  getMemorySummary: () => apiRequest('/conversation/memory/summary'),
};

// 计费相关API
export const billingAPI = {
  // 创建结账会话
  createCheckoutSession: () => apiRequest('/billing/create-checkout-session', {
    method: 'POST',
  }),

  // 创建客户门户会话
  createPortalSession: () => apiRequest('/billing/create-portal-session', {
    method: 'POST',
  }),

  // 获取订阅状态
  getSubscriptionStatus: () => apiRequest('/billing/subscription-status'),
};

// RAG文档处理相关API
export const ragAPI = {
  // 上传文档
  uploadDocument: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    return apiRequest('/rag/upload-document', {
      method: 'POST',
      headers: {}, // 让浏览器自动设置Content-Type
      body: formData,
    });
  },

  // 获取文档状态
  getDocumentStatus: (jobId) => apiRequest(`/rag/document/${jobId}`),

  // 获取文档列表
  getDocuments: (page = 1, pageSize = 20) => 
    apiRequest(`/rag/documents?page=${page}&page_size=${pageSize}`),

  // 删除文档
  deleteDocument: (jobId) => apiRequest(`/rag/document/${jobId}`, {
    method: 'DELETE',
  }),

  // 重试文档处理
  retryDocument: (jobId) => apiRequest(`/rag/document/${jobId}/retry`, {
    method: 'POST',
  }),

  // 搜索文档
  searchDocuments: (query, limit = 10) => 
    apiRequest(`/rag/search?query=${encodeURIComponent(query)}&limit=${limit}`),
};

// 配额相关API
export const quotaAPI = {
  // 获取用户配额信息
  getQuotaInfo: () => apiRequest('/quota/info'),

  // 获取使用统计
  getUsageStats: () => apiRequest('/quota/usage-stats'),
};

// 健康检查API
export const healthAPI = {
  // 检查服务健康状态
  checkHealth: () => apiRequest('/health'),

  // 详细健康检查
  getDetailedHealth: () => apiRequest('/health/detailed'),

  // 获取性能指标
  getMetrics: () => apiRequest('/health/metrics'),

  // 获取性能统计
  getPerformanceStats: () => apiRequest('/health/performance'),

  // 获取数据库统计
  getDatabaseStats: () => apiRequest('/health/database'),

  // 获取系统信息
  getSystemInfo: () => apiRequest('/health/system'),
};

// 证据链相关API
export const evidenceAPI = {
  // 获取对话的证据链
  getConversationEvidence: (conversationId, limit = 50, offset = 0) =>
    apiRequest(`/evidence/conversation/${conversationId}?limit=${limit}&offset=${offset}`),

  // 获取研究会的证据链
  getResearchEvidence: (researchSessionId, limit = 50, offset = 0) =>
    apiRequest(`/evidence/research/${researchSessionId}?limit=${limit}&offset=${offset}`),

  // 标记证据使用状态
  markEvidenceUsed: (evidenceId, used) =>
    apiRequest(`/evidence/${evidenceId}/mark_used`, {
      method: 'PUT',
      body: JSON.stringify({ used })
    }),

  // 获取证据统计
  getEvidenceStats: (days = 7) =>
    apiRequest(`/evidence/stats?days=${days}`),
};

// PPT生成相关API
export const pptAPI = {
  // 创建PPT
  createPresentation: (request) => apiRequest('/ppt/presentation/create', {
    method: 'POST',
    body: JSON.stringify(request),
  }),

  // 上传文件用于PPT生成
  uploadFile: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    return apiRequest('/ppt/files/upload', {
      method: 'POST',
      headers: {}, // 让浏览器自动设置Content-Type
      body: formData,
    });
  },

  // 分解文件内容
  decomposeFile: (fileId) => apiRequest('/ppt/files/decompose', {
    method: 'POST',
    body: JSON.stringify({ file_id: fileId }),
  }),

  // 编辑单个幻灯片
  editSlide: (slideId, prompt) => apiRequest('/ppt/slide/edit', {
    method: 'POST',
    body: JSON.stringify({ slide_id: slideId, prompt }),
  }),

  // 获取PPT信息
  getPresentation: (presentationId) => apiRequest(`/ppt/presentation/${presentationId}`),

  // 健康检查
  checkHealth: () => apiRequest('/ppt/health'),
};

// 向后兼容的独立函数导出
// 这些是为了兼容现有组件的导入

// 文件上传相关API (兼容性)
export const uploadSingleFile = (file) => {
  const formData = new FormData();
  formData.append('file', file);

  return apiRequest('/rag/upload-document', {
    method: 'POST',
    headers: {}, // 让浏览器自动设置Content-Type
    body: formData,
  });
};

export const uploadMultipleFiles = (files) => {
  const formData = new FormData();
  files.forEach((file, index) => {
    formData.append(`file_${index}`, file);
  });

  return apiRequest('/rag/upload-multiple', {
    method: 'POST',
    headers: {},
    body: formData,
  });
};

// Ollama相关API (兼容性)
export const fetchOllamaModelTags = () =>
  apiRequest('/ollama/tags');

// 用户认证API (兼容性)
export const loginUser = (credentials) => {
  // OAuth2PasswordRequestForm 需要使用 URL编码的表单数据，不是JSON
  const formData = new URLSearchParams();
  formData.append('username', credentials.username);
  formData.append('password', credentials.password);

  return apiRequest('/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData.toString(),
  });
};

export const registerUser = (userData) =>
  apiRequest('/auth/register', {
    method: 'POST',
    body: JSON.stringify(userData),
  });

// 聊天功能API (兼容性)
export const simpleChat = (message) =>
  apiRequest('/chat', {
    method: 'POST',
    body: JSON.stringify(message),
  });

export const startResearch = (query, config = {}) =>
  apiRequest('/research/start', {
    method: 'POST',
    body: JSON.stringify({ query, ...config }),
  });

/**
 * 订阅研究事件流（SSE）
 * @param {string} sessionId - 研究会话ID
 * @param {function} onMessage - 消息处理回调
 * @param {function} onError - 错误处理回调
 * @returns {EventSource} EventSource 实例
 */
export const subscribeToResearchEvents = (sessionId, onMessage, onError) => {
  const eventSource = new EventSource(
    `${API_BASE_URL}/api/research/stream/${sessionId}`
  );

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (onMessage) {
        onMessage(data);
      }
    } catch (error) {
      console.error('解析 SSE 消息失败:', error);
      if (onError) {
        onError(error);
      }
    }
  };

  eventSource.onerror = (error) => {
    console.error('SSE 连接错误:', error);
    if (onError) {
      onError(error);
    }
  };

  return eventSource;
};

export const getFinalResearchReport = (researchId) =>
  apiRequest(`/research/${researchId}/report`);

// 历史记录API (兼容性)
export const fetchHistories = (token) => {
  // 这里应该使用token进行认证
  // 暂时使用基本的API调用
  return apiRequest('/conversation/sessions');
};

export const fetchHistoryMessages = (sessionId, token) =>
  apiRequest(`/conversation/sessions/${sessionId}`);

export const deleteAllHistories = (token) =>
  apiRequest('/conversation/sessions', {
    method: 'DELETE',
  });

// 管理员功能API (兼容性)
export const adminFetchChatLogs = (params = {}) =>
  apiRequest('/admin/chat-logs', {
    method: 'GET',
    body: params ? new URLSearchParams(params).toString() : undefined,
  });

export const adminFetchUsage = (params = {}) =>
  apiRequest('/admin/usage', {
    method: 'GET',
    body: params ? new URLSearchParams(params).toString() : undefined,
  });

// 错误处理函数 (兼容性)
export const handleAPIError = (error) => {
  console.error('API Error:', error);

  if (error.message) {
    // 解析错误信息
    if (error.message.includes('401')) {
      return '认证失败，请重新登录';
    } else if (error.message.includes('403')) {
      return '权限不足';
    } else if (error.message.includes('404')) {
      return '请求的资源不存在';
    } else if (error.message.includes('500')) {
      return '服务器内部错误';
    } else if (error.message.includes('网络')) {
      return '网络连接错误';
    }
  }

  return error.message || '未知错误';
};

// 注意：default导出将在所有API定义完成后添加

// 代码沙盒相关API
export const codeSandboxAPI = {
  // 执行代码
  executeCode: (code, options = {}) => apiRequest('/code-sandbox/execute', {
    method: 'POST',
    body: JSON.stringify({
      code,
      timeout: options.timeout || 30,
      memory_limit_mb: options.memory_limit_mb || 100,
      context: options.context || {}
    }),
  }),

  // 验证代码安全性
  validateCode: (code, options = {}) => apiRequest('/code-sandbox/validate', {
    method: 'POST',
    body: JSON.stringify({
      code,
      timeout: options.timeout || 30,
      memory_limit_mb: options.memory_limit_mb || 100
    }),
  }),

  // 获取代码执行历史
  getHistory: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return apiRequest(`/code-sandbox/history?${queryString}`);
  },

  // 删除历史记录项
  deleteHistoryItem: (itemId) => apiRequest(`/code-sandbox/history/${itemId}`, {
    method: 'DELETE',
  }),

  // 清空历史记录
  clearHistory: () => apiRequest('/code-sandbox/history', {
    method: 'DELETE',
  }),

  // 获取可用模块列表
  getAvailableModules: () => apiRequest('/code-sandbox/modules'),
};

// 深度研究相关API功能已合并到上面的 researchAPI 对象中

// 知识库管理相关API
export const knowledgeBaseAPI = {
  // 获取知识库列表
  getKnowledgeBases: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return apiRequest(`/knowledge-base/list?${queryString}`);
  },

  // 创建知识库
  createKnowledgeBase: (kbData) => apiRequest('/knowledge-base/create', {
    method: 'POST',
    body: JSON.stringify(kbData),
  }),

  // 获取知识库详情
  getKnowledgeBase: (kbId) => apiRequest(`/knowledge-base/${kbId}`),

  // 更新知识库
  updateKnowledgeBase: (kbId, kbData) => apiRequest(`/knowledge-base/${kbId}`, {
    method: 'PUT',
    body: JSON.stringify(kbData),
  }),

  // 删除知识库
  deleteKnowledgeBase: (kbId) => apiRequest(`/knowledge-base/${kbId}`, {
    method: 'DELETE',
  }),

  // 上传文档到知识库
  uploadDocument: (kbId, file) => {
    const formData = new FormData();
    formData.append('file', file);

    return apiRequest(`/knowledge-base/${kbId}/documents`, {
      method: 'POST',
      headers: {},
      body: formData,
    });
  },

  // 搜索知识库
  searchKnowledgeBase: (kbId, query, options = {}) => {
    const params = new URLSearchParams({ query, ...options });
    return apiRequest(`/knowledge-base/${kbId}/search?${params.toString()}`);
  },

  // 导入知识库
  importKnowledgeBase: (importData) => apiRequest('/knowledge-base/import', {
    method: 'POST',
    body: JSON.stringify(importData),
  }),

  // 导出知识库
  exportKnowledgeBase: (kbId, format = 'json') =>
    apiRequest(`/knowledge-base/${kbId}/export?format=${format}`),
};

// 文档分析相关API
export const documentAnalysisAPI = {
  // 上传文档进行分析
  uploadDocument: (file, options = {}) => {
    const formData = new FormData();
    formData.append('file', file);
    Object.keys(options).forEach(key => {
      formData.append(key, options[key]);
    });

    return apiRequest('/document-analysis/upload', {
      method: 'POST',
      headers: {},
      body: formData,
    });
  },

  // 获取文档分析状态
  getAnalysisStatus: (documentId) => apiRequest(`/document-analysis/${documentId}/status`),

  // 获取文档分析结果
  getAnalysisResult: (documentId) => apiRequest(`/document-analysis/${documentId}/result`),

  // 获取文档列表
  getDocuments: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return apiRequest(`/document-analysis/documents?${queryString}`);
  },

  // 删除文档
  deleteDocument: (documentId) => apiRequest(`/document-analysis/${documentId}`, {
    method: 'DELETE',
  }),

  // 下载文档
  downloadDocument: (documentId) => {
    const url = `${API_BASE_URL}/document-analysis/${documentId}/download`;
    const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');

    return fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      credentials: 'include',
    });
  },

  // 批量分析文档
  batchAnalyze: (documentIds, options = {}) => apiRequest('/document-analysis/batch-analyze', {
    method: 'POST',
    body: JSON.stringify({ document_ids: documentIds, ...options }),
  }),

  // 从URL导入文档
  importFromUrl: (url, options = {}) => apiRequest('/document-analysis/import-url', {
    method: 'POST',
    body: JSON.stringify({ url, ...options }),
  }),
};

// LLM提供商相关API
export const llmProviderAPI = {
  // 获取当前搜索提供商
  getCurrentProvider: () => apiRequest('/llm-provider/current'),

  // 设置默认搜索提供商
  setDefaultProvider: (providerId) => apiRequest('/llm-provider/set-default', {
    method: 'POST',
    body: JSON.stringify({ provider_id: providerId }),
  }),
};

// 监控面板相关API
export const monitoringAPI = {
  // 获取系统概览
  getSystemOverview: () => apiRequest('/monitoring/overview'),

  // 获取性能指标
  getPerformanceMetrics: (timeRange = '1h') =>
    apiRequest(`/monitoring/performance?time_range=${timeRange}`),

  // 获取资源使用情况
  getResourceUsage: () => apiRequest('/monitoring/resources'),

  // 获取错误日志
  getErrorLogs: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return apiRequest(`/monitoring/errors?${queryString}`);
  },

  // 获取访问日志
  getAccessLogs: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return apiRequest(`/monitoring/access?${queryString}`);
  },

  // 获取告警信息
  getAlerts: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return apiRequest(`/monitoring/alerts?${queryString}`);
  },

  // 创建告警规则
  createAlertRule: (ruleData) => apiRequest('/monitoring/alert-rules', {
    method: 'POST',
    body: JSON.stringify(ruleData),
  }),

  // 获取实时指标 (返回WebSocket URL)
  getRealTimeMetrics: () => `${API_BASE_URL.replace('http', 'ws')}/monitoring/realtime`,
};

// 内容审核相关API
export const contentModerationAPI = {
  // 审核文本内容
  moderateText: (text, options = {}) => apiRequest('/moderation/text', {
    method: 'POST',
    body: JSON.stringify({ text, ...options }),
  }),

  // 审核图片内容
  moderateImage: (imageFile, options = {}) => {
    const formData = new FormData();
    formData.append('image', imageFile);
    Object.keys(options).forEach(key => {
      formData.append(key, options[key]);
    });

    return apiRequest('/moderation/image', {
      method: 'POST',
      headers: {},
      body: formData,
    });
  },

  // 获取审核记录
  getModerationHistory: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return apiRequest(`/moderation/history?${queryString}`);
  },

  // 批量审核
  batchModerate: (items, options = {}) => apiRequest('/moderation/batch', {
    method: 'POST',
    body: JSON.stringify({ items, ...options }),
  }),

  // 更新审核结果
  updateModerationResult: (moderationId, result) => apiRequest(`/moderation/${moderationId}/result`, {
    method: 'PUT',
    body: JSON.stringify(result),
  }),

  // 获取审核统计
  getModerationStats: (timeRange = '7d') =>
    apiRequest(`/moderation/stats?time_range=${timeRange}`),

  // 设置审核规则
  setModerationRules: (rules) => apiRequest('/moderation/rules', {
    method: 'PUT',
    body: JSON.stringify(rules),
  }),

  // 获取审核规则
  getModerationRules: () => apiRequest('/moderation/rules'),
};

// 搜索相关API
export const searchAPI = {
  // 通用搜索
  search: (query, options = {}) => {
    const params = new URLSearchParams({ query, ...options });
    return apiRequest(`/search?${params.toString()}`);
  },

  // 智能搜索
  smartSearch: (query, context = {}) => apiRequest('/search/smart', {
    method: 'POST',
    body: JSON.stringify({ query, context }),
  }),

  // 搜索建议
  getSuggestions: (query, limit = 10) =>
    apiRequest(`/search/suggestions?q=${encodeURIComponent(query)}&limit=${limit}`),

  // 搜索历史
  getSearchHistory: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return apiRequest(`/search/history?${queryString}`);
  },

  // 清除搜索历史
  clearSearchHistory: () => apiRequest('/search/history', {
    method: 'DELETE',
  }),

  // 保存搜索
  saveSearch: (query, filters = {}) => apiRequest('/search/saved', {
    method: 'POST',
    body: JSON.stringify({ query, filters }),
  }),

  // 获取保存的搜索
  getSavedSearches: () => apiRequest('/search/saved'),

  // 删除保存的搜索
  deleteSavedSearch: (searchId) => apiRequest(`/search/saved/${searchId}`, {
    method: 'DELETE',
  }),

  // 搜索分析
  getSearchAnalytics: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return apiRequest(`/search/analytics?${queryString}`);
  },
};

// OCR相关API
export const ocrAPI = {
  // 图片OCR识别
  recognizeImage: (imageFile, options = {}) => {
    const formData = new FormData();
    formData.append('image', imageFile);
    Object.keys(options).forEach(key => {
      formData.append(key, options[key]);
    });

    return apiRequest('/ocr/recognize', {
      method: 'POST',
      headers: {},
      body: formData,
    });
  },

  // PDF OCR识别
  recognizePDF: (pdfFile, options = {}) => {
    const formData = new FormData();
    formData.append('pdf', pdfFile);
    Object.keys(options).forEach(key => {
      formData.append(key, options[key]);
    });

    return apiRequest('/ocr/pdf', {
      method: 'POST',
      headers: {},
      body: formData,
    });
  },

  // 批量OCR识别
  batchRecognize: (files, options = {}) => {
    const formData = new FormData();
    files.forEach((file, index) => {
      formData.append(`file_${index}`, file);
    });
    Object.keys(options).forEach(key => {
      formData.append(key, options[key]);
    });

    return apiRequest('/ocr/batch', {
      method: 'POST',
      headers: {},
      body: formData,
    });
  },

  // 获取OCR任务状态
  getTaskStatus: (taskId) => apiRequest(`/ocr/tasks/${taskId}`),

  // 获取OCR结果
  getOCRResult: (taskId) => apiRequest(`/ocr/results/${taskId}`),

  // 获取OCR历史
  getOCRHistory: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return apiRequest(`/ocr/history?${queryString}`);
  },

  // 下载OCR结果
  downloadResult: (taskId, format = 'txt') => {
    const url = `${API_BASE_URL}/ocr/results/${taskId}/download?format=${format}`;
    const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');

    return fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      credentials: 'include',
    });
  },

  // 删除OCR任务
  deleteTask: (taskId) => apiRequest(`/ocr/tasks/${taskId}`, {
    method: 'DELETE',
  }),
};

// 注意：所有兼容性函数已经在上面单独导出了，这里不需要重复导出

// 导出所有API
export default {
  auth: authAPI,
  chat: chatAPI,
  llmConfig: llmConfigAPI,
  conversation: conversationAPI,
  billing: billingAPI,
  rag: ragAPI,
  quota: quotaAPI,
  health: healthAPI,
  evidence: evidenceAPI,
  ppt: pptAPI,
  codeSandbox: codeSandboxAPI,
  research: researchAPI,
  knowledgeBase: knowledgeBaseAPI,
  documentAnalysis: documentAnalysisAPI,
  monitoring: monitoringAPI,
  contentModeration: contentModerationAPI,
  search: searchAPI,
  ocr: ocrAPI,
  llmProvider: llmProviderAPI,
};