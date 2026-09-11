// All HTTP traffic uses an origin/base prefix; /api remains part of each route.
export const API_BASE_URL = (import.meta.env?.VITE_API_BASE_URL || '').replace(/\/$/, '');
export const apiUrl = (endpoint) => `${API_BASE_URL}${endpoint}`;
export const getAccessToken = () => localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
let refreshPromise = null;
let authGeneration = 0;
export const getAuthGeneration = () => authGeneration;

export function clearCredentials() {
  authGeneration += 1;
  for (const storage of [localStorage, sessionStorage]) {
    for (const key of ['auth_token', 'refresh_token', 'auth_username', 'user']) storage.removeItem(key);
  }
  if (typeof window !== 'undefined') window.dispatchEvent(new Event('auth-cleared'));
}

export function saveCredentials(data, remember = true) {
  clearCredentials();
  const storage = remember ? localStorage : sessionStorage;
  storage.setItem('auth_token', data.access_token);
  if (data.refresh_token) storage.setItem('refresh_token', data.refresh_token);
  if (data.user) storage.setItem('user', JSON.stringify(data.user));
}

export function errorMessage(payload, fallback) {
  const detail = payload?.detail || payload?.error;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map(item => item.msg || '输入无效').join('；');
  return fallback;
}

async function responseError(response) {
  const payload = await response.json().catch(() => ({}));
  const error = new Error(errorMessage(payload, `HTTP ${response.status}: ${response.statusText}`));
  error.status = response.status;
  return error;
}

async function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const generation = authGeneration;
      const storage = localStorage.getItem('auth_token') ? localStorage : sessionStorage;
      const refreshToken = storage.getItem('refresh_token');
      if (!refreshToken) throw new Error('登录已过期，请重新登录');
      const response = await fetch(apiUrl('/api/users/refresh'), {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken })
      });
      if (!response.ok) throw await responseError(response);
      const data = await response.json();
      if (generation !== authGeneration) throw new Error('登录状态已改变');
      if (!data.access_token) throw new Error('刷新登录失败，请重新登录');
      storage.setItem('auth_token', data.access_token);
      if (data.refresh_token) storage.setItem('refresh_token', data.refresh_token);
      return data.access_token;
    })().finally(() => { refreshPromise = null; });
  }
  return refreshPromise;
}

export async function authenticatedFetch(endpoint, options = {}) {
  const { auth = true, ...fetchOptions } = options;
  const generation = authGeneration;
  const token = auth ? getAccessToken() : null;
  const headers = new Headers(fetchOptions.headers);
  if (fetchOptions.body && !(fetchOptions.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  if (token) headers.set('Authorization', `Bearer ${token}`);
  let response = await fetch(apiUrl(endpoint), { ...fetchOptions, headers });
  if (response.status === 401 && auth && token && !endpoint.startsWith('/api/users/refresh')) {
    try {
      // Another concurrent response may have refreshed the same expired token already.
      const current = getAccessToken();
      const refreshed = current && current !== token ? current : await refreshAccessToken();
      if (generation !== authGeneration) throw new Error('登录状态已改变');
      headers.set('Authorization', `Bearer ${refreshed}`);
      response = await fetch(apiUrl(endpoint), { ...fetchOptions, headers });
    } catch (error) {
      if (generation === authGeneration) clearCredentials();
      throw error;
    }
  }
  if (!response.ok) {
    if (response.status === 401 && auth && generation === authGeneration) clearCredentials();
    throw await responseError(response);
  }
  return response;
}

export async function request(endpoint, options = {}) {
  const { params, ...config } = options;
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params || {})) {
    if (value !== null && value !== undefined) query.set(key, String(value));
  }
  const path = query.size ? `${endpoint}${endpoint.includes('?') ? '&' : '?'}${query}` : endpoint;
  const response = await authenticatedFetch(path, config);
  return response.status === 204 ? null : response.json();
}
