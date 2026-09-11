import { request, authenticatedFetch } from './client.js';

export const userAPI = {
  // 注册
  register: (userData) => request('/api/users/register', {
    auth: false,
    method: 'POST',
    body: JSON.stringify(userData),
  }),

  // 登录
  login: (loginData) => request('/api/users/login', {
    auth: false,
    method: 'POST',
    body: JSON.stringify(loginData),
  }),

  // 获取当前用户信息
  getCurrentUser: () => request('/api/users/me'),

  // 更新用户资料
  updateProfile: (updateData) => request('/api/users/me', {
    method: 'PUT',
    body: JSON.stringify(updateData),
  }),

  // 获取用户偏好
  getPreferences: () => request('/api/users/preferences'),

  // 更新用户偏好
  updatePreferences: (preferences) => request('/api/users/preferences', {
    method: 'PUT',
    body: JSON.stringify(preferences),
  }),

  // 刷新token
  refreshToken: (refreshToken) => request('/api/users/refresh', {
    auth: false,
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshToken }),
  }),

  // 登出
  logout: (options = {}) => request('/api/users/logout', {
    method: 'POST', ...options,
  }),
};

// 聊天API - 对应 /api/chat
export const chatAPI = {
  branchSession: (sessionId, beforeMessageId, options = {}) => request(`/api/chat/sessions/${sessionId}/branch`, {
    method: 'POST', body: JSON.stringify({ before_message_id: beforeMessageId }), ...options,
  }),
  // 创建会话
  createSession: (sessionData) => request('/api/chat/sessions', {
    method: 'POST',
    body: JSON.stringify(sessionData),
  }),

  // 获取会话列表
  getSessions: (limit = 50, offset = 0) => 
    request(`/api/chat/sessions?limit=${limit}&offset=${offset}`),

  // 获取会话详情
  getSession: (sessionId) => request(`/api/chat/sessions/${sessionId}`),

  // 更新会话
  updateSession: (sessionId, updateData) => request(`/api/chat/sessions/${sessionId}`, {
    method: 'PUT',
    body: JSON.stringify(updateData),
  }),

  // 删除会话
  deleteSession: (sessionId) => request(`/api/chat/sessions/${sessionId}`, {
    method: 'DELETE',
  }),

  // 获取会话消息
  getMessages: (sessionId, limit = null, options = {}) => {
    const url = limit 
      ? `/api/chat/sessions/${sessionId}/messages?limit=${limit}`
      : `/api/chat/sessions/${sessionId}/messages`;
    return request(url, options);
  },

  // 清空会话消息
  clearMessages: (sessionId) => request(`/api/chat/sessions/${sessionId}/messages`, {
    method: 'DELETE',
  }),

  // 发送消息（非流式）
  chat: (chatRequest, options = {}) => request('/api/chat/chat', {
    method: 'POST',
    body: JSON.stringify(chatRequest), ...options
  }),

  // 发送消息（流式）
  chatStream: (chatRequest, options = {}) => authenticatedFetch('/api/chat/chat/stream', {
    method: 'POST', body: JSON.stringify(chatRequest), ...options
  }),

  webSearch: (chatRequest, options = {}) => request('/api/chat/chat/web-search', {
    method: 'POST', body: JSON.stringify(chatRequest), ...options
  }),

  getModels: () => request('/api/chat/models'),
};

// 研究API - 对应 /api/research
export const researchAPI = {
  // 启动研究
  startResearch: (researchRequest, options = {}) => request('/api/research/start', {
    method: 'POST',
    body: JSON.stringify(researchRequest), ...options,
  }),

  // 获取研究状态
  getStream: (sessionId, options = {}) => authenticatedFetch(`/api/research/stream/${sessionId}`, options),

  getStatus: (sessionId) => request(`/api/research/status/${sessionId}`),

  // 中断研究
  interrupt: (sessionId) => request(`/api/research/interrupt/${sessionId}`, {
    method: 'POST',
  }),

  // 恢复研究
  resume: (sessionId, stateData = null) => request(`/api/research/resume/${sessionId}`, {
    method: 'POST',
    body: JSON.stringify(stateData || {}),
  }),

  // 获取会话列表
  getSessions: (status = null, limit = 20, userId = null) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('limit', limit);
    if (userId) params.append('user_id', userId);
    
    return request(`/api/research/sessions?${params.toString()}`);
  },

  // 导出会话数据
  exportSession: (sessionId) => request(`/api/research/export/${sessionId}`),

  // 删除会话
  deleteSession: (sessionId) => request(`/api/research/${sessionId}`, {
    method: 'DELETE',
  }),

  // 搜索研究内容
  search: (query, limit = 20, userId = null) => {
    const params = new URLSearchParams({ query, limit: limit.toString() });
    if (userId) params.append('user_id', userId);
    
    return request(`/api/research/search?${params.toString()}`);
  },

  // 获取统计信息
  getStatistics: (userId = null) => {
    const params = userId ? `?user_id=${userId}` : '';
    return request(`/api/research/statistics${params}`);
  },

  // 清理非活跃会话（管理员）
  cleanup: (inactiveHours = 24) => request(`/api/research/cleanup?inactive_hours=${inactiveHours}`, {
    method: 'POST',
  }),
};

// 健康检查
export const healthAPI = {
  check: () => request('/health'),
};

// 默认导出
export default {
  userAPI,
  chatAPI,
  researchAPI,
  healthAPI,
};
