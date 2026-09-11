/**
 * 用户API接口 - 对齐后端 /api/users
 */

import { userAPI } from './index';

/**
 * 用户注册
 */
export async function register(userData) {
  return await userAPI.register(userData);
}

/**
 * 用户登录
 */
export async function login(credentials) {
  return await userAPI.login(credentials);
}

/**
 * 获取当前用户信息
 */
export async function getCurrentUser() {
  return await userAPI.getCurrentUser();
}

/**
 * 更新用户资料
 */
export async function updateProfile(profileData) {
  return await userAPI.updateProfile(profileData);
}

/**
 * 获取用户偏好设置
 */
export async function getPreferences() {
  return await userAPI.getPreferences();
}

/**
 * 更新用户偏好设置
 */
export async function updatePreferences(preferences) {
  return await userAPI.updatePreferences(preferences);
}

/**
 * 刷新访问令牌
 */
export async function refreshToken(refreshToken) {
  return await userAPI.refreshToken(refreshToken);
}

/**
 * 用户登出
 */
export async function logout() {
  return await userAPI.logout();
}
