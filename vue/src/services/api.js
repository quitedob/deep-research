// # src/services/api.js
// 简介：封装与后端交互的接口，包括获取模型列表

// --- API 地址配置 ---
// 简化注释：项目自身后端服务的API地址 (FastAPI)
const API_BASE_URL = 'http://localhost:8000/api';
// 简化注释：本地Ollama服务的API地址（若前端保留旧UI可继续使用）
const OLLAMA_API_BASE_URL = 'http://localhost:11434/api';


/**
 * API错误处理类
 * 简化注释：自定义API错误
 */
class APIError extends Error {
  constructor(message, status, details) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.details = details;
  }
}

// --- 【新增】直接与Ollama交互的函数 ---
/**
 * 获取本地 Ollama 可用模型列表
 * 使用官方 /tags 端点同步模型列表到前端
 * @returns {Promise<Array<string>>} 模型名称字符串数组
 * 简化注释：获取Ollama模型列表
 */
export async function fetchOllamaModelTags() {
  try {
    // 简化注释：向Ollama的/tags端点发起GET请求
    const response = await fetch(`${OLLAMA_API_BASE_URL}/tags`);
    if (!response.ok) {
      throw new APIError(`请求Ollama模型列表失败`, response.status);
    }
    const data = await response.json();
    // 简化注释：Ollama返回的数据结构为 { models: [...] }，提取其中的name
    return data.models.map(model => model.name) || [];
  } catch (error) {
    console.error('获取Ollama模型列表时出错:', error);
    // 简化注释：向上层抛出错误，以便UI可以处理
    throw error;
  }
}


// --- 与项目后端 (端口8000) 交互的函数 ---

/**
 * 检查系统状态
 * 简化注释：检查后端服务状态
 */
export async function getSystemStatus() {
  try {
    // 新后端健康检查端点
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      throw new APIError('无法获取系统状态', response.status);
    }
    return await response.json();
  } catch (error) {
    console.error('获取系统状态失败:', error);
    throw error;
  }
}

/**
 * 获取可用的LLM提供者
 * 简化注释：获取可用LLM提供者
 */
export async function getProviders() {
  try {
    const response = await fetch(`${API_BASE_URL}/providers`);
    if (!response.ok) {
      throw new APIError('无法获取提供者列表', response.status);
    }
    return await response.json();
  } catch (error) {
    console.error('获取提供者列表失败:', error);
    throw error;
  }
}

/**
 * 流式聊天
 * @param {string} message - 用户消息
 * @param {Array} chatHistory - 聊天历史
 * @param {string} preferredProvider - 首选提供者
 * @param {function} onChunk - 接收数据块的回调
 * @param {function} onDone - 完成时的回调
 * @param {function} onError - 错误处理回调
 * @param {AbortSignal} signal - 取消信号
 * 简化注释：流式聊天接口
 */
export function streamChat(message, sessionId = null, onChunk, onDone, onError, signal) {
  const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  fetch(`${API_BASE_URL}/chat/stream`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ message, session_id: sessionId }),
    signal,
  }).then(response => {
    if (!response.ok) {
      return response.json().then(err => { throw new APIError(err.detail || `HTTP ${response.status}`, response.status, err); });
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    function push() {
      reader.read().then(({ done, value }) => {
        if (done) {
          onDone();
          return;
        }
        const chunk = decoder.decode(value, { stream: true });
        // SSE format is data: {...}\n\n
        const lines = chunk.match(/data: .*\n\n/g) || [];
        for (const line of lines) {
          try {
            const jsonStr = line.replace(/^data: /, '').replace(/\n\n$/, '');
            const data = JSON.parse(jsonStr);
            if (data.type === 'content') {
              onChunk(data.content);
            } else if (data.type === 'done') {
              onDone();
            } else if (data.type === 'error') {
              onError(new APIError(data.error));
            } else if (data.type === 'start' && data.session_id) {
              // Optional: handle session_id from server if it was newly created
            }
          } catch (e) {
            console.error("SSE parse error", e);
          }
        }
        push();
      }).catch(error => {
        if (error.name !== 'AbortError') {
          onError(error);
        }
      });
    }
    push();
  }).catch(error => {
    if (error.name !== 'AbortError') {
      onError(error);
    }
  });
}

/**
 * 简单聊天（使用Kimi模型）
 * @param {string} message - 用户消息
 * @param {string|null} sessionId - 当前会话ID
 */
export async function simpleChat(message, sessionId = null) {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId })
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new APIError(errorData.detail || `HTTP ${response.status}`, response.status, errorData);
    }
    return await response.json();
  } catch (error) {
    console.error('简单聊天请求失败:', error);
    throw error;
  }
}

/**
 * 启动研究任务
 * @param {string} query - 研究查询
 * @param {string|null} sessionId - 当前会话ID
 */
export async function startResearch(query, sessionId = null) {
  try {
    const response = await fetch(`${API_BASE_URL}/research`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, session_id: sessionId })
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new APIError(errorData.detail || `HTTP ${response.status}`, response.status, errorData);
    }
    return await response.json();
  } catch (error) {
    console.error('启动研究任务失败:', error);
    throw error;
  }
}

/**
 * 订阅研究任务的 SSE 事件
 * @param {string} sessionId 会话ID
 * @param {(evt:any)=>void} onEvent 事件回调（已做统一映射）
 * @param {(err:Error)=>void} onError 错误回调
 * @returns {EventSource} 事件源对象，可调用 close() 取消
 */
export function subscribeToResearchEvents(sessionId, onEvent, onError) {
  try {
    const url = `${API_BASE_URL}/research/stream/${encodeURIComponent(sessionId)}`;
    const es = new EventSource(url);

    es.onmessage = async (e) => {
      try {
        const data = JSON.parse(e.data);
        // 终止事件：包含 status
        if (data && data.status) {
          if (data.status === 'completed') {
            try {
              const final = await getFinalResearchReport(sessionId);
              onEvent && onEvent({ event_type: 'final_report', payload: { content: final.report } });
            } catch (err) {
              onError && onError(err);
            } finally {
              es.close();
            }
          } else if (data.status === 'failed') {
            onError && onError(new APIError(data.error || '研究失败'));
            es.close();
          }
          return;
        }
        // 进度事件：透传为“思考”类型，供前端渲染
        onEvent && onEvent({ event_type: 'agent_thought', payload: { thought: JSON.stringify(data) } });
      } catch (err) {
        console.error('解析研究事件失败:', err);
      }
    };

    es.onerror = (e) => {
      onError && onError(new APIError('SSE 连接错误'));
      es.close();
    };

    return es;
  } catch (error) {
    onError && onError(error);
    throw error;
  }
}

/**
 * 获取研究最终报告
 * @param {string} sessionId 会话ID
 * @returns {Promise<{session_id:string, query:string, report:string}>}
 */
export async function getFinalResearchReport(sessionId) {
  try {
    const response = await fetch(`${API_BASE_URL}/research/${encodeURIComponent(sessionId)}`);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new APIError(errorData.detail || `HTTP ${response.status}`, response.status, errorData);
    }
    return await response.json();
  } catch (error) {
    console.error('获取最终报告失败:', error);
    throw error;
  }
}

/**
 * 用户与认证：登录/注册/获取当前用户
 */
export async function registerUser(username, password, phone, email) {
  const payload = { username, password };
  if (phone) payload.phone = phone;
  if (email) payload.email = email;
  const res = await fetch(`${API_BASE_URL}/register`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  });
  if (!res.ok) throw new APIError('注册失败', res.status, await res.json().catch(() => ({})));
  return res.json();
}

export async function loginUser(username, password) {
  const res = await fetch(`${API_BASE_URL}/login`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password })
  });
  if (!res.ok) throw new APIError('登录失败', res.status, await res.json().catch(() => ({})));
  return res.json();
}

export async function getCurrentUser(token) {
  const res = await fetch(`${API_BASE_URL}/me`, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) throw new APIError('获取当前用户失败', res.status, await res.json().catch(() => ({})));
  return res.json();
}

/**
 * 后台管理：需要管理员Token
 */
export async function adminFetchChatLogs(token) {
  const res = await fetch(`${API_BASE_URL}/admin/chat_logs`, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) throw new APIError('获取聊天日志失败', res.status, await res.json().catch(() => ({})));
  return res.json();
}

export async function adminFetchUsage(token) {
  const res = await fetch(`${API_BASE_URL}/admin/usage`, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) throw new APIError('获取使用统计失败', res.status, await res.json().catch(() => ({})));
  return res.json();
}

/**
 * 聊天记录
 */
export async function fetchHistories(token) {
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers.Authorization = `Bearer ${token}`;
    const res = await fetch(`${API_BASE_URL}/histories`, { headers });
    if (!res.ok) throw new APIError('获取历史列表失败', res.status, await res.json().catch(() => ({})));
    return res.json();
}

export async function fetchHistoryMessages(sessionId, token) {
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers.Authorization = `Bearer ${token}`;
    const res = await fetch(`${API_BASE_URL}/histories/${sessionId}`, { headers });
    if (!res.ok) throw new APIError('获取历史消息失败', res.status, await res.json().catch(() => ({})));
    return res.json();
}

export async function deleteAllHistories(token) {
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers.Authorization = `Bearer ${token}`;
    const res = await fetch(`${API_BASE_URL}/histories`, { method: 'DELETE', headers });
    if (!res.ok) throw new APIError('删除全部历史失败', res.status, await res.json().catch(() => ({})));
    return res.json();
}

/**
 * 文件上传相关API
 */

/**
 * 单文件上传
 * @param {FormData} formData - 包含文件和其他参数的FormData
 * @returns {Promise<Object>} 上传结果
 */
export async function uploadSingleFile(formData) {
  try {
    const response = await fetch(`${API_BASE_URL}/upload/file`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new APIError(errorData.detail || `HTTP ${response.status}`, response.status, errorData);
    }

    return await response.json();
  } catch (error) {
    console.error('单文件上传失败:', error);
    throw error;
  }
}

/**
 * 多文件上传
 * @param {FormData} formData - 包含多个文件和其他参数的FormData
 * @returns {Promise<Object>} 批量上传结果
 */
export async function uploadMultipleFiles(formData) {
  try {
    const response = await fetch(`${API_BASE_URL}/upload/multiple`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new APIError(errorData.detail || `HTTP ${response.status}`, response.status, errorData);
    }

    return await response.json();
  } catch (error) {
    console.error('多文件上传失败:', error);
    throw error;
  }
}

/**
 * 获取文件上传支持信息
 * @returns {Promise<Object>} 支持的文件格式和限制信息
 */
export async function getUploadInfo() {
  try {
    const response = await fetch(`${API_BASE_URL}/upload/info`);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new APIError(errorData.detail || `HTTP ${response.status}`, response.status, errorData);
    }

    return await response.json();
  } catch (error) {
    console.error('获取上传信息失败:', error);
    throw error;
  }
}

/**
 * 带文件的聊天
 * @param {string} message - 用户消息
 * @param {FileList} files - 文件列表
 * @param {boolean} stream - 是否使用流式响应
 * @param {string} modelName - 模型名称
 * @returns {Promise<Object>} 聊天响应
 */
export async function chatWithFiles(message, files = [], stream = false, modelName = 'default') {
  try {
    const formData = new FormData();
    formData.append('message', message);
    formData.append('stream', stream.toString());
    formData.append('model_name', modelName);

    // 添加文件
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    const response = await fetch(`${API_BASE_URL}/chat/with-files`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new APIError(errorData.detail || `HTTP ${response.status}`, response.status, errorData);
    }

    if (stream) {
      // 处理流式响应
      return response; // 返回response对象供调用者处理流
    } else {
      return await response.json();
    }
  } catch (error) {
    console.error('带文件聊天失败:', error);
    throw error;
  }
}

/**
 * 错误处理工具函数
 * 简化注释：通用API错误处理
 */
export function handleAPIError(error) {
  if (error instanceof APIError) {
    switch (error.status) {
      case 503: return '服务暂时不可用，请稍后重试';
      case 500: return '服务器内部错误，请联系管理员';
      case 401: return 'API密钥无效或已过期';
      case 402: return 'API余额不足，请充值后重试';
      case 429: return '请求过于频繁，请稍后重试';
      default: return error.message || '发生未知错误';
    }
  }
  if (error.name === 'AbortError') return '请求已取消';
  if (!navigator.onLine) return '网络连接断开，请检查网络';
  return '网络错误，请检查连接';
}