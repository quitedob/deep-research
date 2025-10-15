// src/services/ollama.js

const OLLAMA_API_URL = 'http://localhost:11434/api/chat';

/**
 * 与 Ollama API 进行流式通信
 * @param {string} model - 要使用的模型名称
 * @param {Array<object>} messages - 消息历史记录，仅包含 role 和 content
 * @param {function(string): void} onStream - 处理流式数据的回调函数
 * @param {function(): void} onDone - 流结束时的回调函数
 * @param {AbortSignal} signal - 用于中止 fetch 请求的 AbortSignal
 * @returns {Promise<void>}
 */
/**
 * 检查 Ollama 服务连接状态
 * @returns {Promise<{connected: boolean, models: Array, error: string|null}>}
 */
export async function checkOllamaStatus() {
  try {
    const response = await fetch('http://localhost:11434/api/tags', {
      method: 'GET',
      signal: AbortSignal.timeout(5000) // 5秒超时
    });

    if (response.ok) {
      const data = await response.json();
      return {
        connected: true,
        models: data.models || [],
        error: null
      };
    } else {
      return {
        connected: false,
        models: [],
        error: `HTTP ${response.status}: ${response.statusText}`
      };
    }
  } catch (error) {
    return {
      connected: false,
      models: [],
      error: error.name === 'AbortError' ? '连接超时' : error.message
    };
  }
}

/**
 * 与 Ollama API 进行流式通信
 * @param {string} model - 要使用的模型名称
 * @param {Array<object>} messages - 消息历史记录，仅包含 role 和 content
 * @param {function(string): void} onStream - 处理流式数据的回调函数
 * @param {function(): void} onDone - 流结束时的回调函数
 * @param {AbortSignal} signal - 用于中止 fetch 请求的 AbortSignal
 * @returns {Promise<void>}
 */
export async function streamChat(model, messages, onStream, onDone, signal) {
  try {
    const response = await fetch(OLLAMA_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: model,
        messages: messages,
        stream: true,
      }),
      signal: signal, // 关键：传入 signal
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        if (onDone) onDone();
        break;
      }
      const chunk = decoder.decode(value, { stream: true });
      // Ollama 的流式响应是每行一个 JSON 对象
      const lines = chunk.split('\n').filter(line => line.trim() !== '');
      for (const line of lines) {
        try {
          const parsed = JSON.parse(line);
          if (parsed.message && parsed.message.content) {
            onStream(parsed.message.content);
          }
          if (parsed.done) {
            if (onDone) onDone();
            return; // 对话结束
          }
        } catch (e) {
          console.error('Failed to parse stream line:', line, e);
        }
      }
    }
  } catch (error) {
    console.error('Error streaming chat from Ollama:', error);
    let errorMsg = '\n\n**错误:** 无法连接到 Ollama 服务。';

    if (error.name === 'AbortError') {
      errorMsg = '\n\n**已停止:** 请求已被中止。';
    } else if (error.message.includes('Failed to fetch')) {
      errorMsg += `\n\n请检查：\n1. Ollama 是否正在运行\n2. 服务地址是否正确 (${OLLAMA_API_URL})\n3. 网络连接是否正常`;
    } else {
      errorMsg += `\n\n详细错误: ${error.message}`;
    }

    onStream(errorMsg);
    if (onDone) onDone();
  }
}