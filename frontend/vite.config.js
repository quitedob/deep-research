// vite.config.js

/**
 * Deep Research 前端配置
 * 1. 前端服务端口: 3000 (与项目设计一致)
 * 2. 后端API代理: 8000 (统一后端端口)
 * 3. HMR热更新: 本地开发环境
 * 4. API路径代理到Deep Research后端服务
 */
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';

export default defineConfig({
  plugins: [vue()],
  server: {
    host: 'localhost',
    port: 3000,            // 统一使用3000端口
    // API代理配置 - 代理到Deep Research后端
    proxy: {
      '/health': { target: 'http://localhost:8000', changeOrigin: true },
      // 代理所有 /api 请求到后端服务
      '/api': {
        target: 'http://localhost:8000',  // Deep Research后端服务地址
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path  // 保持 /api 前缀
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia']
        }
      }
    }
  }
});
