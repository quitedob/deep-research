/**
 * 聊天API接口 - 对齐后端 /api/chat
 */

import { chatAPI } from './index';

/**
 * 创建会话
 */
export async function createSession(sessionData) {
  return await chatAPI.createSession(sessionData);
}

/**
 * 获取会话列表
 */
export async function getSessions(limit = 50, offset = 0) {
  return await chatAPI.getSessions(limit, offset);
}

/**
 * 获取会话详情
 */
export async function getSession(sessionId) {
  return await chatAPI.getSession(sessionId);
}

/**
 * 更新会话
 */
export async function updateSession(sessionId, updateData) {
  return await chatAPI.updateSession(sessionId, updateData);
}

/**
 * 删除会话
 */
export async function deleteSession(sessionId) {
  return await chatAPI.deleteSession(sessionId);
}

/**
 * 获取会话消息
 */
export async function getMessages(sessionId, limit = null) {
  return await chatAPI.getMessages(sessionId, limit);
}

/**
 * 清空会话消息
 */
export async function clearMessages(sessionId) {
  return await chatAPI.clearMessages(sessionId);
}

/**
 * 发送消息（非流式）
 */
export async function chat(chatRequest) {
  return await chatAPI.chat(chatRequest);
}

/**
 * 发送消息（流式）
 */
export async function chatStream(chatRequest) {
  return await chatAPI.chatStream(chatRequest);
}

/**
 * 获取可用模型列表
 */
export async function getModels() {
  return await chatAPI.getModels();
}
