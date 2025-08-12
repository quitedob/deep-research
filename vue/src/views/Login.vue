<template>
  <div class="auth-page">
    <div class="card">
      <h2>登录</h2>
      <form @submit.prevent="doLogin">
        <input v-model="username" type="text" placeholder="用户名" />
        <input v-model="password" type="password" placeholder="密码" />
        <button type="submit">登录</button>
      </form>

      <div class="divider">或</div>

      <h3>注册</h3>
      <form @submit.prevent="doRegister">
        <input v-model="regUsername" type="text" placeholder="用户名" />
        <input v-model="regPassword" type="password" placeholder="密码" />
        <button type="submit">注册</button>
      </form>

      <p class="tip">默认管理员：用户名 admin，密码 root123456</p>
    </div>
  </div>
  
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { loginUser, registerUser, handleAPIError } from '@/services/api.js'

const router = useRouter();
const username = ref('');
const password = ref('');
const regUsername = ref('');
const regPassword = ref('');

const doLogin = async () => {
  try {
    const data = await loginUser(username.value, password.value);
    localStorage.setItem('auth_token', data.token);
    localStorage.setItem('auth_username', data.username);
    router.push('/');
  } catch (e) {
    alert(handleAPIError(e));
  }
}

const doRegister = async () => {
  try {
    const data = await registerUser(regUsername.value, regPassword.value);
    localStorage.setItem('auth_token', data.token);
    localStorage.setItem('auth_username', data.username);
    router.push('/');
  } catch (e) {
    alert(handleAPIError(e));
  }
}
</script>

<style scoped>
.auth-page { display: flex; align-items: center; justify-content: center; height: 100vh; }
.card { width: 360px; padding: 24px; border: 1px solid var(--border-color); border-radius: 12px; background: var(--primary-bg); }
input { display: block; width: 100%; padding: 10px 12px; margin: 8px 0; border: 1px solid var(--border-color); border-radius: 8px; background: var(--secondary-bg); color: var(--text-primary); }
button { width: 100%; padding: 10px 12px; border-radius: 8px; border: 1px solid var(--border-color); background: var(--button-bg); color: var(--button-text); cursor: pointer; }
.divider { text-align: center; margin: 16px 0; color: var(--text-secondary); }
.tip { margin-top: 8px; font-size: 12px; color: var(--text-secondary); }
</style>


