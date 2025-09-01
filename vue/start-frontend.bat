@echo off
REM Deep Research 前端启动脚本 (Windows)

echo 🚀 启动 Deep Research 前端...

REM 检查 Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js 未安装，请先安装 Node.js 16+
    pause
    exit /b 1
)

REM 检查 npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ npm 未安装，请先安装 npm
    pause
    exit /b 1
)

REM 检查依赖
if not exist "node_modules" (
    echo 📦 安装依赖...
    npm install
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
)

REM 创建环境变量文件（如果不存在）
if not exist ".env" (
    echo 📝 创建环境配置文件...
    echo # Deep Research 前端环境配置 > .env
    echo VUE_APP_API_BASE_URL=http://localhost:8000/api >> .env
    echo VUE_APP_DEBUG=true >> .env
    echo VUE_APP_ENABLE_HEALTH_CHECK=true >> .env
    echo VUE_APP_ENABLE_SYSTEM_MONITOR=true >> .env
    echo VUE_APP_ENABLE_DOCUMENT_SEARCH=true >> .env
    echo VUE_APP_ENABLE_EVIDENCE_CHAIN=true >> .env
    echo VUE_APP_DEFAULT_THEME=dark >> .env
    echo VUE_APP_MAX_UPLOAD_SIZE=52428800 >> .env
    echo VUE_APP_SUPPORTED_FILE_TYPES=.pdf,.docx,.doc,.txt,.md >> .env
    echo VUE_APP_HEALTH_CHECK_INTERVAL=30000 >> .env
    echo VUE_APP_AUTO_REFRESH_ENABLED=true >> .env
    echo ✅ 环境配置文件已创建
)

REM 检查后端服务
echo 🔍 检查后端服务连接...
powershell -Command "Test-NetConnection -ComputerName localhost -Port 8000 -InformationLevel Quiet" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 后端服务运行正常 (localhost:8000)
) else (
    echo ⚠️  后端服务未运行，请先启动后端服务
    echo    运行: python app.py
)

echo.
echo 🎯 启动前端开发服务器...
echo    前端地址: http://localhost:3000
echo    后端代理: http://localhost:8000/api
echo.

REM 启动开发服务器
npm run dev

pause
