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
    {
        path: '/',
        redirect: '/home'
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
    console.log('[Router] 路由守卫检查', { to: to.path, name: to.name });

    const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
    const isFirstVisit = !localStorage.getItem('has_visited_before');
    const hasCompletedWelcome = localStorage.getItem('welcome_completed') === 'true';

    console.log('[Router] 用户状态', {
        hasToken: !!token,
        isFirstVisit,
        hasCompletedWelcome,
        source: localStorage.getItem('auth_token') ? 'localStorage' : 'sessionStorage' || 'none'
    });

    // 根地址重定向处理
    if (to.path === '/') {
        console.log('[Router] 处理根地址访问');

        // 如果用户未登录，重定向到着陆页
        if (!token) {
            console.log('[Router] 未登录用户，重定向到着陆页');
            return { path: '/landing' };
        }

        // 如果用户已登录但未完成欢迎流程，重定向到欢迎页面
        if (!hasCompletedWelcome) {
            console.log('[Router] 新用户重定向到欢迎页面');
            return { path: '/welcome' };
        }

        // 已登录且完成欢迎流程，重定向到AI聊天页面
        console.log('[Router] 已登录用户，重定向到AI聊天页面');
        return { path: '/home' };
    }

    // 公开页面 - 无需认证即可访问
    const publicPaths = ['/landing', '/welcome', '/login', '/register', '/help', '/policies'];
    if (publicPaths.includes(to.path)) {
        console.log('[Router] 公开页面，允许访问');

        // 如果用户已登录访问登录/注册页面，重定向到主页
        if (token && (to.path === '/login' || to.path === '/register')) {
            console.log('[Router] 已登录用户访问认证页面，重定向到主页');
            return { path: '/home' };
        }

        // 如果已登录用户访问欢迎页面且已完成欢迎流程，重定向到主页
        if (token && to.path === '/welcome' && hasCompletedWelcome) {
            console.log('[Router] 已完成欢迎流程，重定向到主页');
            return { path: '/home' };
        }

        return true;
    }

    // 需要认证的页面
    if (!token) {
        console.log('[Router] 需要认证但未找到token，重定向到登录页');
        return { path: '/login', query: { redirect: to.fullPath } };
    }

    // 欢迎流程检查：新用户首次登录后应先完成欢迎流程
    if (token && !hasCompletedWelcome && to.path !== '/welcome') {
        console.log('[Router] 新用户未完成欢迎流程，重定向到欢迎页面');
        return { path: '/welcome' };
    }

    // 主页特殊处理：确保欢迎流程逻辑正确执行
    if (to.path === '/home' && token && !hasCompletedWelcome) {
        console.log('[Router] 访问主页但未完成欢迎流程，重定向到欢迎页面');
        return { path: '/welcome' };
    }

    // 管理员专属页面（已删除管理员功能）
    const adminPaths = []; // 已删除所有管理员页面
    if (adminPaths.some(path => to.path.startsWith(path))) {
        console.log('[Router] 检查管理员权限');
        try {
            const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');
            if (userStr) {
                const user = JSON.parse(userStr);
                console.log('[Router] 用户角色检查', { userRole: user.role, requiredRole: 'admin' });

                if (user.role !== 'admin') {
                    console.log('[Router] 权限不足，重定向到主页');
                    return { path: '/home', query: { error: 'access_denied' } };
                }
            } else {
                console.log('[Router] 未找到用户信息，重定向到登录页');
                return { path: '/login', query: { redirect: to.fullPath } };
            }
        } catch (error) {
            console.error('[Router] 检查管理员权限失败:', error);
            return { path: '/login' };
        }
    }

    console.log('[Router] 路由检查通过，允许访问');
    return true;
});

export default router;