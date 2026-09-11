// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';
import Home from '@/views/Home.vue'; // 引入主页视图组件
import Homepage from '@/views/Homepage.vue'; // 引入酷炫主页组件
import Welcome from '@/views/Welcome.vue'; // 引入欢迎引导页面
import HelpCenter from '@/views/HelpCenter.vue'; // 1. 引入帮助中心组件
import TermsAndPolicies from '@/views/TermsAndPolicies.vue'; // 2. 引入条款政策组件
import Login from '@/views/Login.vue'; // 3. 引入登录页面
import Register from '@/views/Register.vue'; // 4. 引入注册页面
// 已删除无用的管理员和工具相关页面导入

const routes = [
    { path: '/share/:shareId', alias: '/public/conversation/:shareId', component: () => import('@/components/PublicConversation.vue'), meta: { public: true } },
    {
        path: '/',
        redirect: () => (localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')) ? '/home' : '/landing'
    },
    {
        path: '/landing',
        name: 'Homepage',
        component: Homepage
    },
    {
        path: '/welcome',
        name: 'Welcome',
        component: Welcome
    },
    {
        path: '/home',
        name: 'Home',
        component: Home
    },
    // 登录页面
    {
        path: '/login',
        name: 'Login',
        component: Login
    },
    // 注册页面
    {
        path: '/register',
        name: 'Register',
        component: Register
    },
    // 已删除无用的路由：代码沙盒、文档管理、管理员、研究项目、Agent管理等
    // 3. 添加帮助中心页面的路由规则
    {
        path: '/help',
        name: 'HelpCenter',
        component: HelpCenter
    },
    // 4. 添加条款与政策页面的路由规则
    {
        path: '/policies',
        name: 'TermsAndPolicies',
        component: TermsAndPolicies
    }
];

const router = createRouter({
    history: createWebHistory(),
    routes
});

// 路由守卫：配置JWT认证和公开页面
router.beforeEach((to) => {
    const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
    if (to.meta.public) return true;
    const publicPaths = ['/landing', '/welcome', '/login', '/register', '/help', '/policies'];
    if (publicPaths.includes(to.path)) {
        if (token && ['/login', '/register'].includes(to.path)) return '/home';
        return true;
    }
    if (!token) return { path: '/login', query: { redirect: to.fullPath } };
    return true;
});

export default router;
