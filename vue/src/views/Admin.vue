<template>
  <div class="admin-page">
    <div class="toolbar">
      <button @click="reload">刷新</button>
      <span class="spacer"></span>
      <router-link to="/">返回首页</router-link>
    </div>

    <div class="panels">
      <div class="panel">
        <h3>使用统计</h3>
        <pre>{{ usage }}</pre>
      </div>
      <div class="panel">
        <h3>最近聊天日志</h3>
        <ul class="logs">
          <li v-for="item in logs" :key="item.id">
            <div class="meta">{{ item.created_at }} · {{ item.username || '匿名' }} · {{ item.role }} · {{ item.session_id }}</div>
            <div class="content">{{ item.content }}</div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { adminFetchChatLogs, adminFetchUsage, handleAPIError } from '@/services/api.js'

const logs = ref([]);
const usage = ref({});

const reload = async () => {
  try {
    const token = localStorage.getItem('auth_token');
    if (!token) { alert('请先登录管理员'); return; }
    usage.value = await adminFetchUsage(token);
    const resp = await adminFetchChatLogs(token);
    logs.value = resp.items || [];
  } catch (e) {
    alert(handleAPIError(e));
  }
}

onMounted(reload);
</script>

<style scoped>
.admin-page { padding: 16px; }
.toolbar { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.spacer { flex: 1; }
.panels { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.panel { border: 1px solid var(--border-color); border-radius: 12px; background: var(--primary-bg); padding: 12px; }
.logs { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; max-height: 70vh; overflow: auto; }
.meta { font-size: 12px; color: var(--text-secondary); }
.content { white-space: pre-wrap; }
pre { white-space: pre-wrap; word-break: break-word; }
button { padding: 8px 12px; border-radius: 8px; border: 1px solid var(--border-color); background: var(--button-bg); color: var(--button-text); cursor: pointer; }
</style>


