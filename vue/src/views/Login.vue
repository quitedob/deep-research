<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-header">
        <div class="logo-container">
          <img src="https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_92x30dp.png" alt="Google" class="logo">
          <div class="brand-name">Deep Research</div>
        </div>
        <h2 class="title">登录您的账户</h2>
        <p class="subtitle">使用您的 Deep Research 帐户继续</p>
      </div>
      <form @submit.prevent="doLogin" class="form" novalidate>
        <div class="input-group">
          <input
            v-model.trim="username"
            type="text"
            id="username"
            autocomplete="username"
            required
            placeholder=" "
            @blur="touched.username = true"
            :class="{ invalid: usernameError && touched.username }"
          />
          <label for="username">账号 / Account</label>
          <div class="animated-border"></div>
          <p v-if="usernameError && touched.username" class="error">{{ usernameError }}</p>
        </div>

        <div class="input-group">
          <input
            v-model.trim="password"
            :type="passwordFieldType"
            id="password"
            autocomplete="current-password"
            required
            placeholder=" "
            @blur="touched.password = true"
            :class="{ invalid: passwordError && touched.password }"
          />
          <button type="button" @click="togglePasswordVisibility" class="password-toggle">
            {{ passwordFieldType === 'password' ? '显示' : '隐藏' }}
          </button>
          <label for="password">密码 / Password</label>
          <div class="animated-border"></div>
          <p v-if="passwordError && touched.password" class="error">{{ passwordError }}</p>
        </div>

        <label class="remember">
          <input type="checkbox" v-model="rememberMe" />
          <span>记住我 / Remember me</span>
        </label>

        <div class="footer-actions">
          <router-link class="link" to="/register">创建帐户</router-link>
          <button type="submit" class="primary-btn" :disabled="submitting">
            {{ submitting ? '登录中...' : '下一步' }}
          </button>
        </div>
      </form>
      <p class="tip">默认管理员：用户名 admin，密码 root123456</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { loginUser, handleAPIError, authAPI } from '@/services/api.js';

const router = useRouter();
const username = ref('');
const password = ref('');
const rememberMe = ref(true);
const submitting = ref(false);
const passwordFieldType = ref('password');

const touched = reactive({
  username: false,
  password: false,
});

const usernameError = computed(() => {
  if (!username.value) return '请输入账号';
  return '';
});

const passwordError = computed(() => {
  if (!password.value) return '请输入密码';
  return '';
});

const togglePasswordVisibility = () => {
  passwordFieldType.value = passwordFieldType.value === 'password' ? 'text' : 'password';
};

const doLogin = async () => {
  touched.username = true;
  touched.password = true;

  if (usernameError.value || passwordError.value) return;

  try {
    submitting.value = true;
    console.log('[Login] 开始登录流程', { username: username.value, rememberMe: rememberMe.value });

    const data = await loginUser(username.value, password.value);
    console.log('[Login] 登录响应', { token: data.token?.substring(0, 20) + '...', username: data.username });

    const storage = rememberMe.value ? localStorage : sessionStorage;
    storage.setItem('auth_token', data.token);
    storage.setItem('auth_username', data.username);
    console.log('[Login] Token已保存到', rememberMe.value ? 'localStorage' : 'sessionStorage');

    // 获取用户详细信息（包括角色）
    console.log('[Login] 获取用户详细信息...');
    const userInfo = await authAPI.getCurrentUser();
    console.log('[Login] 用户信息', { id: userInfo.id, username: userInfo.username, role: userInfo.role, email: userInfo.email });

    storage.setItem('user', JSON.stringify(userInfo));

    // 根据角色自动分流
    const redirectPath = userInfo.role === 'admin' ? '/admin' : '/';
    const redirect = router.currentRoute.value.query?.redirect;
    console.log('[Login] 重定向路径计算', { redirectPath, redirect, userRole: userInfo.role });

    // 如果有指定重定向且是管理员，则优先使用重定向，否则使用角色分流
    const finalRedirect = (redirect && userInfo.role === 'admin') ? redirect : redirectPath;
    console.log('[Login] 最终重定向到', finalRedirect);
    router.push(String(finalRedirect));
  } catch (e) {
    console.error('[Login] 登录失败', e);
    alert(handleAPIError(e));
  } finally {
    submitting.value = false;
  }
};

onMounted(() => {
  const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
  console.log('[Login] 页面加载检查token', { hasToken: !!token, source: localStorage.getItem('auth_token') ? 'localStorage' : 'sessionStorage' });
  if (token) {
    console.log('[Login] 发现已存在token，重定向到首页');
    router.replace('/');
  }
});
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #f0f7ff 0%, #e3eeff 100%);
  font-family: 'Google Sans', 'Noto Sans', 'Noto Sans SC', 'Roboto', 'Arial', sans-serif;
  padding: 20px;
}

.auth-card {
  width: 100%;
  max-width: 450px;
  padding: 48px 40px;
  border: 1px solid #dadce0;
  border-radius: 12px;
  background-color: #ffffff;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.auth-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.auth-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 20px;
}

.logo {
  height: 32px;
}

.brand-name {
  font-size: 20px;
  font-weight: 500;
  color: #1a73e8;
}

.title {
  font-size: 24px;
  font-weight: 500;
  color: #202124;
  margin: 0;
}

.subtitle {
  font-size: 16px;
  color: #5f6368;
  margin-top: 12px;
  line-height: 1.5;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.input-group {
  position: relative;
  margin-bottom: 8px;
}

.input-group input {
  width: 100%;
  padding: 18px 14px 10px;
  border: 1px solid #dadce0;
  border-radius: 6px;
  background-color: #ffffff;
  color: #202124;
  font-size: 16px;
  transition: all 0.3s ease;
  height: 56px;
}

.input-group input:focus {
  outline: none;
  border-color: #1a73e8;
  box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.2);
}

.input-group label {
  position: absolute;
  top: 18px;
  left: 14px;
  background: transparent;
  color: #5f6368;
  font-size: 16px;
  pointer-events: none;
  transition: all 0.3s ease;
}

.input-group input:focus + label,
.input-group input:not(:placeholder-shown) + label {
  top: 8px;
  font-size: 12px;
  color: #1a73e8;
  transform: translateY(-10px);
}

.input-group input.invalid {
  border-color: #d93025;
}

.input-group input.invalid:focus {
  box-shadow: 0 0 0 2px rgba(217, 48, 37, 0.2);
}

.input-group input.invalid + button + label,
.input-group input.invalid + label {
  color: #d93025;
}

.error {
  color: #d93025;
  font-size: 13px;
  margin-top: 6px;
  padding-left: 14px;
  display: block;
  min-height: 20px;
}

.remember {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #5f6368;
  user-select: none;
  margin-top: -6px;
}

.remember input {
  width: 18px;
  height: 18px;
  border-radius: 4px;
  border: 1px solid #dadce0;
  transition: all 0.2s ease;
}

.remember input:checked {
  background-color: #1a73e8;
  border-color: #1a73e8;
}

.footer-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 24px;
}

.link {
  color: #1a73e8;
  text-decoration: none;
  font-weight: 500;
  font-size: 14px;
  transition: color 0.2s ease;
}

.link:hover {
  color: #1557b0;
  text-decoration: underline;
}

.primary-btn {
  padding: 12px 28px;
  border-radius: 6px;
  border: none;
  background: linear-gradient(to right, #1a73e8, #0d5abf);
  color: #ffffff;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 6px rgba(26, 115, 232, 0.3);
}

.primary-btn:hover {
  background: linear-gradient(to right, #0d5abf, #0a4ba7);
  box-shadow: 0 4px 10px rgba(26, 115, 232, 0.4);
}

.primary-btn:disabled {
  background: #e0e0e0;
  cursor: not-allowed;
  box-shadow: none;
}

.tip {
  margin-top: 28px;
  font-size: 13px;
  color: #5f6368;
  text-align: center;
  padding: 12px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #1a73e8;
}

.password-toggle {
  position: absolute;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #5f6368;
  cursor: pointer;
  font-size: 14px;
}

.password-toggle:hover {
  color: #1a73e8;
}

.animated-border {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 0;
  height: 2px;
  background-color: #1a73e8;
  transition: width 0.3s ease;
}

.input-group input:focus ~ .animated-border {
  width: 100%;
}

@media (max-width: 480px) {
  .auth-card {
    padding: 36px 24px;
  }

  .footer-actions {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .primary-btn {
    width: 100%;
  }
}
</style>