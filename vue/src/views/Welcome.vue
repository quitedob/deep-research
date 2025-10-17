<template>
  <div class="welcome-page">
    <Welcome @tour-complete="handleTourComplete" />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Welcome from '@/components/Welcome.vue'

const router = useRouter()

const handleTourComplete = () => {
  // 标记欢迎流程已完成
  localStorage.setItem('welcome_completed', 'true')
  console.log('[Welcome] 欢迎流程完成，标记为已完成')

  // 检查用户是否已登录，决定跳转目标
  const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')

  if (token) {
    console.log('[Welcome] 用户已登录，跳转到主页')
    router.push('/home')
  } else {
    console.log('[Welcome] 用户未登录，引导到登录页面')
    router.push('/login')
  }
}

const skipTour = () => {
  console.log('[Welcome] 用户跳过欢迎流程')
  localStorage.setItem('welcome_completed', 'true')

  const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')
  if (token) {
    router.push('/home')
  } else {
    router.push('/')
  }
}

onMounted(() => {
  console.log('[Welcome] 欢迎页面加载完成')

  // 如果用户已经完成了欢迎流程且已登录，自动重定向
  const hasCompletedWelcome = localStorage.getItem('welcome_completed') === 'true'
  const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')

  if (hasCompletedWelcome && token) {
    console.log('[Welcome] 检测到用户已完成欢迎流程，自动重定向到主页')
    router.push('/home')
  } else if (hasCompletedWelcome) {
    console.log('[Welcome] 检测到用户已完成欢迎流程，重定向到主页页')
    router.push('/')
  }
})
</script>

<style scoped>
.welcome-page {
  min-height: 100vh;
}
</style>