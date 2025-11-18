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
        <h2 class="title">创建您的 Deep Research 帐户</h2>
      </div>
      <form @submit.prevent="doRegister" class="form" novalidate>
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
            type="password"
            id="password"
            autocomplete="new-password"
            required
            placeholder="请输入密码"
            @blur="touched.password = true"
            :class="{ invalid: passwordError && touched.password }"
          />
          <p v-if="passwordError && touched.password" class="error">{{ passwordError }}</p>
        </div>

        <div class="input-group">
          <input
            v-model.trim="phone"
            type="tel"
            id="phone"
            autocomplete="tel"
            placeholder="请输入手机号(可选)"
            @blur="touched.phone = true"
            :class="{ invalid: phoneError && touched.phone }"
          />
          <p v-if="phoneError && touched.phone" class="error">{{ phoneError }}</p>
        </div>

        <div class="input-group">
          <input
            v-model.trim="email"
            type="email"
            id="email"
            autocomplete="email"
            required
            placeholder="请输入邮箱"
            @blur="touched.email = true"
            :class="{ invalid: emailError && touched.email }"
          />
          <p v-if="emailError && touched.email" class="error">{{ emailError }}</p>
        </div>

        <label class="remember">
          <input type="checkbox" v-model="rememberMe" />
          <span>记住我</span>
        </label>

        <div class="footer-actions">
          <router-link class="link" to="/login">已有帐户？去登录</router-link>
          <button type="submit" class="primary-btn" :disabled="submitting">{{ submitting ? '创建中…' : '创建帐户' }}</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { register } from '@/api/user.js';

const router = useRouter();
const username = ref('');
const password = ref('');
const phone = ref('');
const email = ref('');
const submitting = ref(false);
const rememberMe = ref(true);

const touched = reactive({
  username: false,
  password: false,
  phone: false,
  email: false,
});

const alnum20 = /^[A-Za-z0-9]{1,20}$/;
const phoneRe = /^(\+?\d{6,20})$/;
const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const usernameError = computed(() => {
  if (!username.value) return '请输入账号';
  if (!alnum20.test(username.value)) return '账号仅限字母与数字，长度1-20';
  return '';
});

const passwordError = computed(() => {
  if (!password.value) return '请输入密码';
  if (!alnum20.test(password.value)) return '密码仅限字母与数字，长度1-20';
  return '';
});

const phoneError = computed(() => {
  if (phone.value && !phoneRe.test(phone.value)) return '手机号格式不正确';
  return '';
});

const emailError = computed(() => {
  if (!email.value) return '请输入邮箱';
  if (!emailRe.test(email.value)) return '邮箱格式不正确';
  return '';
});

const doRegister = async () => {
  Object.keys(touched).forEach(key => touched[key] = true);

  if (usernameError.value || passwordError.value || phoneError.value || emailError.value) return;

  try {
    submitting.value = true;
    console.log('[Register] 开始注册流程', {
      username: username.value,
      email: email.value,
      rememberMe: rememberMe.value
    });

    // 验证邮箱必填
    if (!email.value) {
      alert('请输入邮箱地址');
      return;
    }

    const userData = {
      username: username.value,
      password: password.value,
      email: email.value
    };

    const data = await register(userData);
    console.log('[Register] 注册响应', {
      token: data.access_token?.substring(0, 20) + '...',
      user: data.user
    });

    const storage = rememberMe.value ? localStorage : sessionStorage;
    storage.setItem('auth_token', data.access_token);
    storage.setItem('user', JSON.stringify(data.user));
    console.log('[Register] 用户信息已保存到', rememberMe.value ? 'localStorage' : 'sessionStorage');

    const redirect = router.currentRoute.value.query?.redirect || '/';
    console.log('[Register] 重定向到', redirect);
    router.push(String(redirect));
  } catch (e) {
    console.error('[Register] 注册失败', e);
    alert(e.message || '注册失败');
  } finally {
    submitting.value = false;
  }
}

onMounted(() => {
  const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
  console.log('[Register] 页面加载检查token', { hasToken: !!token, source: localStorage.getItem('auth_token') ? 'localStorage' : 'sessionStorage' });
  if (token) {
    console.log('[Register] 发现已存在token，重定向到首页');
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
}
</style>


