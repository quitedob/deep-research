#!/bin/bash

# Deep Research 前端启动脚本

echo "🚀 启动 Deep Research 前端..."

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装，请先安装 Node.js 16+"
    exit 1
fi

# 检查 npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm 未安装，请先安装 npm"
    exit 1
fi

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装依赖..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
fi

# 创建环境变量文件（如果不存在）
if [ ! -f ".env" ]; then
    echo "📝 创建环境配置文件..."
    cat > .env << EOF
# Deep Research 前端环境配置
VUE_APP_API_BASE_URL=http://localhost:8000/api
VUE_APP_DEBUG=true
VUE_APP_ENABLE_HEALTH_CHECK=true
VUE_APP_ENABLE_SYSTEM_MONITOR=true
VUE_APP_ENABLE_DOCUMENT_SEARCH=true
VUE_APP_ENABLE_EVIDENCE_CHAIN=true
VUE_APP_DEFAULT_THEME=dark
VUE_APP_MAX_UPLOAD_SIZE=52428800
VUE_APP_SUPPORTED_FILE_TYPES=.pdf,.docx,.doc,.txt,.md
VUE_APP_HEALTH_CHECK_INTERVAL=30000
VUE_APP_AUTO_REFRESH_ENABLED=true
EOF
    echo "✅ 环境配置文件已创建"
fi

# 检查后端服务
echo "🔍 检查后端服务连接..."
if nc -z localhost 8000 2>/dev/null; then
    echo "✅ 后端服务运行正常 (localhost:8000)"
else
    echo "⚠️  后端服务未运行，请先启动后端服务"
    echo "   运行: python app.py"
fi

echo ""
echo "🎯 启动前端开发服务器..."
echo "   前端地址: http://localhost:3000"
echo "   后端代理: http://localhost:8000/api"
echo ""

# 启动开发服务器
npm run dev
