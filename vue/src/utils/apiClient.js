/**
 * API客户端工具
 * 支持自动Token刷新和错误处理
 */

const BASE_URL = 'http://localhost:8000';

/**
 * 获取存储的Token
 */
function getTokens() {
  const accessToken = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
  const refreshToken = localStorage.getItem('refresh_token') || sessionStorage.getItem('refresh_token');
  return { accessToken, refreshToken };
}

/**
 * 保存Token
 */
function saveTokens(accessToken, refreshToken, remember = true) {
  const storage = remember ? localStorage : sessionStorage;
  storage.setItem('access_token', accessToken);
  if (refreshToken) {
    storage.setItem('refresh_token', refreshToken);
  }
}

/**
 * 清除Token
 */
function clearTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  sessionStorage.removeItem('access_token');
  sessionStorage.removeItem('refresh_token');
  sessionStorage.removeItem('user');
}

/**
 * 刷新访问令牌
 */
async function refreshAccessToken() {
  const { refreshToken } = getTokens();
  
  if (!refreshToken) {
    throw new Error('没有刷新令牌');
  }
  
  const response = await fetch(`${BASE_URL}/api/users/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  
  if (!response.ok) {
    clearTokens();
    throw new Error('刷新令牌失败，请重新登录');
  }
  
  const data = await response.json();
  saveTokens(data.access_token, data.refresh_token);
  
  return data.access_token;
}

/**
 * 通用API请求函数
 * 支持自动Token刷新
 */
export async function apiRequest(url, options = {}) {
  const { accessToken } = getTokens();
  
  // 添加认证头
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  if (accessToken && !options.skipAuth) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }
  
  // 第一次请求
  let response = await fetch(`${BASE_URL}${url}`, {
    ...options,
    headers,
  });
  
  // 如果是401错误，尝试刷新Token
  if (response.status === 401 && !options._retry) {
    try {
      console.log('[API] Token可能过期，尝试刷新...');
      const newAccessToken = await refreshAccessToken();
      
      // 使用新Token重试请求
      headers['Authorization'] = `Bearer ${newAccessToken}`;
      response = await fetch(`${BASE_URL}${url}`, {
        ...options,
        headers,
        _retry: true,
      });
      
      console.log('[API] Token刷新成功，请求已重试');
    } catch (error) {
      console.error('[API] Token刷新失败:', error);
      clearTokens();
      window.location.href = '/login';
      throw error;
    }
  }
  
  // 处理响应
  if (!response.ok) {
    const error = await response.json();
    console.error('[API] 请求失败:', error);
    
    // 处理验证错误
    if (error.detail && Array.isArray(error.detail)) {
      const messages = error.detail.map(err => {
        const field = err.loc ? err.loc[err.loc.length - 1] : '';
        const msg = err.msg || err.message || '';
        return field ? `${field}: ${msg}` : msg;
      }).join('\n');
      throw new Error(messages);
    }
    
    throw new Error(error.detail || JSON.stringify(error) || '请求失败');
  }
  
  return await response.json();
}

/**
 * GET请求
 */
export async function get(url, options = {}) {
  return apiRequest(url, { ...options, method: 'GET' });
}

/**
 * POST请求
 */
export async function post(url, data, options = {}) {
  return apiRequest(url, {
    ...options,
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * PUT请求
 */
export async function put(url, data, options = {}) {
  return apiRequest(url, {
    ...options,
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

/**
 * DELETE请求
 */
export async function del(url, options = {}) {
  return apiRequest(url, { ...options, method: 'DELETE' });
}

export { getTokens, saveTokens, clearTokens, refreshAccessToken };
