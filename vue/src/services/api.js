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
  const url = `${API_BASE_URL}${endpoint}`;
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

// 认证相关API
export const authAPI = {
  // 用户登录
  login: (credentials) => {
    console.log('[AuthAPI] 用户登录请求', { username: credentials.username });
    return apiRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
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
export const loginUser = (credentials) =>
  apiRequest('/auth/login', {
    method: 'POST',
    body: JSON.stringify(credentials),
  });

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

export const subscribeToResearchEvents = (researchId) =>
  // 这里应该返回一个EventSource或WebSocket连接
  // 暂时返回一个基本的API调用
  apiRequest(`/research/${researchId}/events`);

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
};

// 注意：所有兼容性函数已经在上面单独导出了，这里不需要重复导出