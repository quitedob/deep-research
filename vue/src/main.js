// src/main.js

import { createApp } from 'vue'
import { createPinia } from 'pinia' // 1. 从 pinia 导入 createPinia
import App from './App.vue'
import router from './router'
// 2. 不再直接导入 store，因为 Pinia 的使用方式不同
import './assets/theme.css' // 导入新的主题样式文件

// (新增) 导入代码高亮样式表
import 'highlight.js/styles/atom-one-dark.css'

const app = createApp(App) // 创建 Vue 应用实例

const pinia = createPinia() // 3. 创建 Pinia 实例

app.use(pinia) // 4. 让 Vue 应用使用 Pinia
app.use(router) // 使用路由

app.mount('#app') // 挂载应用

// 简化注释：创建并挂载Vue应用，并集成Pinia和Vue Router。