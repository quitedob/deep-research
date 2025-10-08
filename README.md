# Deep Research Platform (深度研究平台)

<div align="center">

![Platform Logo](https://img.shields.io/badge/Deep%20Research%20Platform-v1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![Vue](https://img.shields.io/badge/Vue-3.3+-brightgreen)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

**AI驱动的智能研究与文档生成平台**

[功能特性](#功能特性) • [快速开始](#快速开始) • [项目结构](#项目结构) • [配置说明](#配置说明) • [API文档](#api文档) • [部署指南](#部署指南)

</div>

## 📖 项目简介

Deep Research Platform 是一个基于人工智能的综合性研究平台，集成了多模态AI模型、智能搜索、文档生成等功能。平台采用前后端分离架构，支持多种LLM提供商（豆包、DeepSeek、Kimi、Ollama等），提供智能对话、深度研究、PPT生成、OCR识别等核心功能。

### 🎯 核心价值

- **智能路由系统**：根据任务类型自动选择最佳AI模型
- **多模态支持**：文本、图像、语音等多种输入格式
- **深度研究能力**：基于LangGraph的工作流引擎
- **实时协作**：WebSocket流式响应，支持实时交互
- **企业级安全**：JWT认证、配额管理、安全中间件

## ✨ 功能特性

### 🤖 AI对话与推理
- **智能聊天**：支持多轮对话，上下文记忆
- **多模型支持**：DeepSeek、豆包、Kimi、Ollama本地模型
- **智能路由**：根据任务复杂度自动选择最优模型
- **代码生成**：支持多种编程语言的代码生成与解释

### 🔍 智能搜索与检索
- **联网搜索**：集成多个搜索引擎，实时获取最新信息
- **RAG知识库**：基于向量数据库的文档检索与问答
- **融合检索**：结合多种搜索引擎，提高搜索准确性
- **文档理解**：支持PDF、Word、PPT等多种文档格式

### 📊 文档生成与处理
- **智能PPT生成**：基于研究内容自动生成专业演示文稿
- **研究报告**：生成结构化的深度研究报告
- **OCR识别**：高精度图像文字识别
- **多格式导出**：支持Markdown、PDF、Word等格式

### 👥 用户管理
- **用户认证**：JWT令牌认证，安全的用户会话管理
- **配额管理**：灵活的使用配额控制系统
- **订阅服务**：集成Stripe支付系统
- **权限控制**：基于角色的访问控制

## 🚀 快速开始

### 环境要求

- **Python**: 3.8+
- **Node.js**: 16+
- **PostgreSQL**: 12+ (可选，SQLite也可用)
- **Redis**: 6+ (可选，用于缓存和任务队列)

### 1. 克隆项目

```bash
git clone https://github.com/quitedob/deep-research.git
cd deep-research
```

### 2. 后端设置

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置API密钥和数据库连接
```

### 3. 前端设置

```bash
cd vue

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 4. 启动服务

```bash
# 启动后端服务 (项目根目录)
python app.py

# 前端服务默认运行在 http://localhost:3000
# 后端API服务默认运行在 http://localhost:8000
```

### 5. 首次访问

1. 打开浏览器访问 `http://localhost:3000`
2. 注册新用户或使用管理员账户登录
3. 在设置中配置您的AI模型API密钥
4. 开始使用平台的各种功能

## 📁 项目结构

```
deep-research/
├── app.py                          # FastAPI应用入口
├── requirements.txt                # Python依赖包
├── conf.yaml                       # 主配置文件
├── .env.example                    # 环境变量示例
├── src/                            # 后端源代码
│   ├── api/                        # API路由
│   │   ├── admin.py               # 管理员API
│   │   ├── agents.py              # 智能体管理
│   │   ├── auth.py                # 用户认证
│   │   ├── conversation.py        # 对话管理
│   │   ├── llm_provider.py        # LLM提供商
│   │   ├── rag.py                 # RAG检索
│   │   └── ...
│   ├── agents/                     # AI智能体
│   │   ├── base_agent.py          # 智能体基类
│   │   ├── research_agent.py      # 研究智能体
│   │   └── ...
│   ├── core/                       # 核心功能
│   │   ├── db.py                  # 数据库连接
│   │   ├── cache.py               # 缓存管理
│   │   └── ppt/                   # PPT生成模块
│   ├── llms/                       # LLM集成
│   │   ├── base_llm.py            # LLM基类
│   │   └── providers/             # 各LLM提供商
│   │       ├── deepseek_llm.py    # DeepSeek集成
│   │       ├── doubao_llm.py      # 豆包集成
│   │       └── ollama_llm.py      # Ollama集成
│   ├── middleware/                 # 中间件
│   ├── services/                   # 业务服务
│   └── sqlmodel/                   # 数据模型
├── vue/                            # 前端源代码
│   ├── src/
│   │   ├── components/            # Vue组件
│   │   │   ├── ChatContainer.vue  # 聊天容器
│   │   │   ├── InputBox.vue       # 输入框
│   │   │   ├── Sidebar.vue        # 侧边栏
│   │   │   └── ...
│   │   ├── views/                 # 页面视图
│   │   │   ├── Home.vue           # 主页
│   │   │   ├── Admin.vue          # 管理页面
│   │   │   └── ...
│   │   ├── services/              # API服务
│   │   └── store/                 # 状态管理
│   ├── package.json               # 前端依赖
│   └── vite.config.js             # Vite配置
├── uploads/                       # 文件上传目录
├── outputs/                       # 输出文件目录
└── logs/                          # 日志文件目录
```

## ⚙️ 配置说明

### 主配置文件 (conf.yaml)

配置文件采用YAML格式，支持环境变量替换：

```yaml
# LLM后端配置
PRIMARY_LLM_BACKEND: "DOUBAO"
FALLBACK_LLM_BACKEND: "KIMI"

# 数据库配置
DATABASE_URL: "${DATABASE_URL:postgresql+asyncpg://user:pass@localhost/db}"

# API密钥 (通过环境变量设置)
# DEEPSEEK_API_KEY: "your-deepseek-api-key"
# DOUBAO_API_KEY: "your-doubao-api-key"
```

### 环境变量

创建 `.env` 文件配置敏感信息：

```bash
# 数据库连接
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/deep_research

# Redis连接 (可选)
REDIS_URL=redis://localhost:6379

# JWT密钥
SECRET_KEY=your-super-secret-jwt-key
JWT_SECRET_KEY=your-jwt-secret-key

# AI服务API密钥
DEEPSEEK_API_KEY=your-deepseek-api-key
DOUBAO_API_KEY=your-doubao-api-key
KIMI_API_KEY=your-kimi-api-key

# Stripe支付 (可选)
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret
```

### LLM提供商配置

#### DeepSeek
```yaml
DEEPSEEK_BASE_URL: "https://api.deepseek.com/v1"
DEEPSEEK_MODELS:
  chat: "deepseek-chat"
  reasoner: "deepseek-reasoner"
```

#### 豆包 (Doubao)
```yaml
DOUBAO_BASE_URL: "https://ark.cn-beijing.volces.com/api/v3"
DOUBAO_MODEL: "doubao-seed-1-6-flash-250615"
```

#### Ollama (本地)
```yaml
OLLAMA_BASE_URL: "http://localhost:11434/v1"
OLLAMA_SMALL_MODEL: "gemma3:4b"
OLLAMA_LARGE_MODEL: "qwen3:32b"
```

## 🔧 API文档

### 认证API

```http
POST /api/auth/register
POST /api/auth/login
POST /api/auth/refresh
```

### 对话API

```http
POST /api/conversation/chat      # 发送消息
GET  /api/conversation/history   # 获取历史记录
DELETE /api/conversation/{id}    # 删除对话
```

### 研究API

```http
POST /api/research/start         # 开始研究
GET  /api/research/status/{id}   # 获取研究状态
GET  /api/research/report/{id}   # 获取研究报告
```

### PPT生成API

```http
POST /api/ppt/generate           # 生成PPT
GET  /api/ppt/status/{id}        # 获取生成状态
GET  /api/ppt/download/{id}      # 下载PPT
```

### 完整API文档

启动服务后访问：`http://localhost:8000/docs`

## 🚀 部署指南

### Docker部署

```bash
# 构建镜像
docker build -t deep-research .

# 运行容器
docker run -p 8000:8000 deep-research
```

### 生产环境部署

1. **使用Gunicorn**：
```bash
pip install gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker
```

2. **使用Nginx反向代理**：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        root /path/to/vue/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

3. **使用PM2管理进程**：
```bash
npm install -g pm2
pm2 start ecosystem.config.js
```

## 🛠️ 开发指南

### 添加新的LLM提供商

1. 在 `src/llms/providers/` 目录下创建新的提供商文件
2. 继承 `BaseLLM` 类并实现必要方法
3. 在配置文件中添加相应配置
4. 在路由中注册新的提供商

### 创建新的工作流

1. 在 `src/graph/workflow/` 目录下创建工作流文件
2. 使用LangGraph定义工作流节点和边
3. 在 `src/graph/builder.py` 中注册工作流

### 前端开发

```bash
# 开发模式
npm run dev

# 构建生产版本
npm run build

# 代码检查
npm run lint
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- [Vue.js](https://vuejs.org/) - 渐进式JavaScript框架
- [LangGraph](https://python.langchain.com/docs/langgraph) - 构建有状态的AI应用
- [DeepSeek](https://www.deepseek.com/) - 强大的AI推理模型
- [Ollama](https://ollama.com/) - 本地LLM运行环境

## 📞 支持

- 📧 Email: support@deep-research.com
- 💬 Discord: [加入社区](https://discord.gg/deep-research)
- 📖 文档: [在线文档](https://docs.deep-research.com)
- 🐛 问题反馈: [GitHub Issues](https://github.com/quitedob/deep-research/issues)

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给我们一个Star！**

Made with ❤️ by Deep Research Team

</div>