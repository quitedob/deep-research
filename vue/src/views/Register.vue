<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-header">
        <img src="https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_92x30dp.png" alt="Google" class="logo">
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
            @blur="touched.username = true"
            :class="{ invalid: usernameError && touched.username }"
          />
          <label for="username">账号 / Account</label>
          <p v-if="usernameError && touched.username" class="error">{{ usernameError }}</p>
        </div>

        <div class="input-group">
          <input
            v-model.trim="password"
            type="password"
            id="password"
            autocomplete="new-password"
            required
            @blur="touched.password = true"
            :class="{ invalid: passwordError && touched.password }"
          />
          <label for="password">密码 / Password</label>
          <p v-if="passwordError && touched.password" class="error">{{ passwordError }}</p>
        </div>

        <div class="input-group">
          <input
            v-model.trim="phone"
            type="tel"
            id="phone"
            autocomplete="tel"
            @blur="touched.phone = true"
            :class="{ invalid: phoneError && touched.phone }"
          />
          <label for="phone">手机号 / Phone (可选)</label>
          <p v-if="phoneError && touched.phone" class="error">{{ phoneError }}</p>
        </div>

        <div class="input-group">
          <input
            v-model.trim="email"
            type="email"
            id="email"
            autocomplete="email"
            @blur="touched.email = true"
            :class="{ invalid: emailError && touched.email }"
          />
          <label for="email">邮箱 / Email (可选)</label>
          <p v-if="emailError && touched.email" class="error">{{ emailError }}</p>
        </div>

        <label class="remember">
          <input type="checkbox" v-model="rememberMe" />
          <span>记住我 / Remember me</span>
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
import { registerUser, handleAPIError } from '@/services/api.js'

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
  if (email.value && !emailRe.test(email.value)) return '邮箱格式不正确';
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
      phone: phone.value,
      rememberMe: rememberMe.value
    });

    const userData = {
      username: username.value,
      password: password.value,
      email: email.value || null,
      phone: phone.value || null
    };

    const data = await registerUser(userData);
    console.log('[Register] 注册响应', {
      token: data.access_token?.substring(0, 20) + '...',
      username: data.username,
      userId: data.user_id,
      role: data.role
    });

    const storage = rememberMe.value ? localStorage : sessionStorage;
    storage.setItem('auth_token', data.access_token);
    storage.setItem('auth_username', data.username);
    storage.setItem('user', JSON.stringify({
      id: data.user_id,
      username: data.username,
      email: data.email,
      role: data.role
    }));
    console.log('[Register] 用户信息已保存到', rememberMe.value ? 'localStorage' : 'sessionStorage');

    const redirect = router.currentRoute.value.query?.redirect || '/';
    console.log('[Register] 重定向到', redirect);
    router.push(String(redirect));
  } catch (e) {
    console.error('[Register] 注册失败', e);
    alert(handleAPIError(e));
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
  padding: 20px 0;
  background-color: #f0f2f5;
  font-family: 'Google Sans', 'Noto Sans', 'Noto Sans JP', 'Noto Sans KR', 'Noto Sans SC', 'Noto Sans TC', 'Roboto', 'Arial', sans-serif;
}

.auth-card {
  width: 450px;
  padding: 48px 40px;
  border: 1px solid #dadce0;
  border-radius: 8px;
  background-color: #ffffff;
}

.auth-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo {
  height: 24px;
  margin-bottom: 16px;
}

.title {
  font-size: 24px;
  font-weight: 400;
  color: #202124;
  margin: 0;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.input-group {
  position: relative;
}

.input-group input {
  width: 100%;
  padding: 16px 12px;
  border: 1px solid #dadce0;
  border-radius: 4px;
  background-color: #ffffff;
  color: #202124;
  font-size: 16px;
  transition: border-color 0.2s ease;
}

.input-group input:focus {
  outline: none;
  border-color: #1a73e8;
  box-shadow: 0 0 0 1px #1a73e8;
}

.input-group label {
  position: absolute;
  top: 50%;
  left: 13px;
  transform: translateY(-50%);
  background: #fff;
  padding: 0 4px;
  color: #5f6368;
  font-size: 16px;
  pointer-events: none;
  transition: all 0.2s ease;
}

.input-group input:focus + label,
.input-group input:not(:placeholder-shown) + label {
  top: 0;
  font-size: 12px;
  color: #1a73e8;
}
/* Handle optional fields label positioning */
.input-group input:placeholder-shown:not(:focus) + label {
    font-size: 16px;
    top: 50%;
}
.input-group input:-webkit-autofill + label {
    top: 0;
    font-size: 12px;
    color: #1a73e8;
}


.input-group input.invalid {
  border-color: #d93025;
}

.input-group input.invalid:focus {
  box-shadow: 0 0 0 1px #d93025;
}

.input-group input.invalid + label,
.input-group input.invalid:focus + label {
  color: #d93025;
}

.error {
  color: #d93025;
  font-size: 12px;
  margin-top: 4px;
  padding-left: 12px;
}

.remember {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #5f6368;
  user-select: none;
  margin-top: -8px;
}

.remember input {
  width: 16px;
  height: 16px;
}

.footer-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
}

.link {
  color: #1a73e8;
  text-decoration: none;
  font-weight: 500;
  font-size: 14px;
}

.link:hover {
  text-decoration: underline;
}

.primary-btn {
  padding: 10px 24px;
  border-radius: 4px;
  border: none;
  background-color: #1a73e8;
  color: #ffffff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease, box-shadow 0.2s ease;
}

.primary-btn:hover {
  background-color: #185abc;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.primary-btn:disabled {
  background-color: #e0e0e0;
  cursor: not-allowed;
}
</style>


