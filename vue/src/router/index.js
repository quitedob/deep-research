// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';
import Home from '@/views/Home.vue'; // 引入主页视图组件
import Homepage from '@/views/Homepage.vue'; // 引入酷炫主页组件
import HelpCenter from '@/views/HelpCenter.vue'; // 1. 引入帮助中心组件
import TermsAndPolicies from '@/views/TermsAndPolicies.vue'; // 2. 引入条款政策组件
import Login from '@/views/Login.vue'; // 3. 引入登录页面
import Register from '@/views/Register.vue'; // 4. 引入注册页面
import Admin from '@/views/Admin.vue'; // 5. 引入后台页面
import ResearchProjects from '@/views/ResearchProjects.vue'; // 6. 引入研究项目页面
import ProjectDetail from '@/views/ProjectDetail.vue'; // 7. 引入项目详情页面
import AgentManagement from '@/views/AgentManagement.vue'; // 8. 引入Agent管理页面
import AgentLLMConfig from '@/views/AgentLLMConfig.vue'; // 9. 引入智能体LLM配置页面
import AdminDashboard from '@/views/AdminDashboard.vue'; // 10. 引入管理员控制台

const routes = [
    {
        path: '/',
        name: 'Homepage',
        component: Homepage
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
    // 后台管理页面
    {
        path: '/admin',
        name: 'Admin',
        component: Admin
    },
    // 管理员控制台
    {
        path: '/admin/dashboard',
        name: 'AdminDashboard',
        component: AdminDashboard
    },
    // 研究项目页面
    {
        path: '/research/projects',
        name: 'ResearchProjects',
        component: ResearchProjects
    },
    // 项目详情页面
    {
        path: '/research/projects/:id',
        name: 'ProjectDetail',
        component: ProjectDetail
    },
    // Agent管理页面
    {
        path: '/agents',
        name: 'AgentManagement',
        component: AgentManagement
    },
    // 智能体LLM配置页面
    {
        path: '/agent-llm-config',
        name: 'AgentLLMConfig',
        component: AgentLLMConfig
    },
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
    console.log('[Router] Token状态', { hasToken: !!token, source: localStorage.getItem('auth_token') ? 'localStorage' : 'sessionStorage' || 'none' });

    // 公开页面 - 无需认证即可访问
    const publicPaths = ['/', '/homepage', '/login', '/register', '/help', '/policies'];
    if (publicPaths.includes(to.path)) {
        console.log('[Router] 公开页面，允许访问');

        // 如果用户已登录访问登录/注册页面，重定向到主页
        if (token && (to.path === '/login' || to.path === '/register')) {
            console.log('[Router] 已登录用户访问认证页面，重定向到主页');
            return { path: '/home' };
        }
        return true;
    }

    // 需要认证的页面
    if (!token) {
        console.log('[Router] 需要认证但未找到token，重定向到登录页');
        return { path: '/login', query: { redirect: to.fullPath } };
    }

    // 管理员专属页面
    const adminPaths = ['/admin', '/admin/dashboard', '/agent-llm-config'];
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