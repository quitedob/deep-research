<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-header">
        <div class="logo-container">
          <div class="logo-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
          </div>
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
            placeholder="请输入账号"
            @blur="touched.username = true"
            :class="{ invalid: usernameError && touched.username }"
          />
          <p v-if="usernameError && touched.username" class="error">{{ usernameError }}</p>
        </div>

        <div class="input-group">
          <input
            v-model.trim="password"
            :type="passwordFieldType"
            id="password"
            autocomplete="current-password"
            required
            placeholder="请输入密码"
            @blur="touched.password = true"
            :class="{ invalid: passwordError && touched.password }"
          />
          <button type="button" @click="togglePasswordVisibility" class="password-toggle">
            {{ passwordFieldType === 'password' ? '显示' : '隐藏' }}
          </button>
          <p v-if="passwordError && touched.password" class="error">{{ passwordError }}</p>
        </div>

        <label class="remember">
          <input type="checkbox" v-model="rememberMe" />
          <span>记住我</span>
        </label>

        <div class="footer-actions">
          <router-link class="link" to="/register">创建帐户</router-link>
          <button type="submit" class="primary-btn" :disabled="submitting">
            {{ submitting ? '登录中...' : '下一步' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { login } from '@/api/user.js';

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

    const data = await login({
      username: username.value,
      password: password.value
    });
    console.log('[Login] 登录响应', { token: data.access_token?.substring(0, 20) + '...', user: data.user });

    const storage = rememberMe.value ? localStorage : sessionStorage;
    storage.setItem('auth_token', data.access_token);
    storage.setItem('user', JSON.stringify(data.user));
    console.log('[Login] Token和用户信息已保存到', rememberMe.value ? 'localStorage' : 'sessionStorage');

    const redirect = router.currentRoute.value.query?.redirect || '/';
    console.log('[Login] 重定向到', redirect);
    router.push(String(redirect));
  } catch (e) {
    console.error('[Login] 登录失败', e);
    alert(e.message || '登录失败');
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
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background-color: var(--primary-bg);
  padding: var(--spacing-lg);
  position: relative;
}

.auth-card {
  width: 100%;
  max-width: 400px;
  padding: var(--spacing-xl);
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xlarge);
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
  box-shadow: var(--shadow-elev-high);
  transition: all 0.3s ease;
}

.auth-card:hover {
  box-shadow: var(--shadow-elev-high);
}

.auth-header {
  text-align: center;
  margin-bottom: var(--spacing-xl);
}

.logo-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
}

.logo-icon {
  width: 24px;
  height: 24px;
  color: var(--accent-blue);
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-name {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.024em;
}

.title {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  margin-bottom: var(--spacing-sm);
}

.subtitle {
  font-size: 16px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin: 0;
}

.form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.input-group {
  position: relative;
}

.input-group input {
  width: 100%;
  padding: var(--spacing-md);
  border: 1px solid var(--input-border);
  border-radius: var(--radius-medium);
  background-color: var(--input-bg);
  color: var(--text-primary);
  font-size: 16px;
  transition: all 0.2s ease;
  height: 48px;
}

.input-group input::placeholder {
  color: var(--text-tertiary);
}

.input-group input:focus {
  outline: none;
  border-color: var(--input-focus-border);
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
}

.input-group input.invalid {
  border-color: var(--accent-red);
}

.input-group input.invalid:focus {
  box-shadow: 0 0 0 3px rgba(255, 59, 48, 0.1);
}

.error {
  color: var(--accent-red);
  font-size: 13px;
  margin-top: var(--spacing-xs);
  display: block;
  min-height: 20px;
}

.remember {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 14px;
  color: var(--text-secondary);
  user-select: none;
  cursor: pointer;
}

.remember input {
  width: 18px;
  height: 18px;
  border-radius: var(--radius-small);
  border: 1px solid var(--border-color);
  background-color: var(--input-bg);
  transition: all 0.2s ease;
  cursor: pointer;
}

.remember input:checked {
  background-color: var(--accent-blue);
  border-color: var(--accent-blue);
}

.footer-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: var(--spacing-md);
}

.link {
  color: var(--accent-blue);
  text-decoration: none;
  font-weight: 500;
  font-size: 14px;
  transition: color 0.2s ease;
}

.link:hover {
  color: var(--button-secondary-text);
}

.primary-btn {
  padding: var(--spacing-sm) var(--spacing-lg);
  border-radius: var(--radius-large);
  border: none;
  background: var(--gradient-blue);
  color: var(--button-text);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(0, 122, 255, 0.3);
}

.primary-btn:hover {
  transform: scale(1.02);
  box-shadow: 0 4px 12px rgba(0, 122, 255, 0.4);
}

.primary-btn:active {
  transform: scale(0.98);
}

.primary-btn:disabled {
  background: var(--secondary-bg);
  color: var(--text-quaternary);
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

.password-toggle {
  position: absolute;
  right: var(--spacing-md);
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 14px;
  padding: var(--spacing-xs);
  border-radius: var(--radius-small);
  transition: all 0.2s ease;
}

.password-toggle:hover {
  color: var(--text-primary);
  background-color: var(--hover-bg);
}

@media (max-width: 768px) {
  .auth-card {
    padding: var(--spacing-lg);
  }

  .footer-actions {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: stretch;
  }

  .primary-btn {
    width: 100%;
  }

  .link {
    text-align: center;
  }
}

@media (max-width: 480px) {
  .auth-card {
    padding: var(--spacing-md);
  }

  .title {
    font-size: 20px;
  }

  .subtitle {
    font-size: 14px;
  }
}
</style>