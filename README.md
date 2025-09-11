# DeerFlow Deep Research Platform

一个基于AI的深度研究平台，集成了智能对话、文档处理、向量搜索、证据链追踪等功能。

## 🚀 项目概述

DeerFlow是一个现代化的AI研究平台，支持多种LLM提供商，提供智能路由、文档管理、向量搜索等功能。项目采用前后端分离架构，后端基于FastAPI，前端使用Vue 3。

## 📋 目录结构

```
deep-research/
├── src/                    # 后端源码
│   ├── api/               # API路由层
│   ├── config/            # 配置管理
│   ├── dao/               # 数据访问层
│   ├── graph/             # 工作流图
│   ├── llms/              # LLM提供商
│   ├── rag/               # RAG向量搜索
│   ├── serve/             # 服务层
│   ├── tasks/             # 异步任务
│   └── utils/             # 工具函数
├── vue/                   # 前端源码
│   ├── src/               # Vue组件
│   ├── package.json       # 前端依赖
│   └── vite.config.js     # 构建配置
├── pkg/                   # 核心包
├── test/                  # 测试文件
├── app.py                 # 应用入口
├── conf.yaml              # 主配置文件
├── docker-compose.dev.yml # 开发环境
└── requirements.txt       # Python依赖
```

## 🔌 端口配置

### 主要服务端口
- **后端API服务**: `8000` (FastAPI)
- **前端开发服务**: `3000` (Vue + Vite)
- **MySQL数据库**: `3306`
- **Redis缓存**: `6379`

### 管理工具端口
- **phpMyAdmin**: `8080` (MySQL管理界面)
- **Redis Commander**: `8081` (Redis管理界面)

### 外部服务端口
- **Ollama本地LLM**: `11434`

## ✨ 已实现功能

### 🤖 AI对话系统
- ✅ 多LLM提供商支持 (DeepSeek, Ollama, Kimi)
- ✅ 智能路由系统，根据任务类型自动选择最佳模型
- ✅ 流式响应支持
- ✅ 对话记忆管理
- ✅ 上下文自动分块处理

### 📄 文档处理系统
- ✅ 多格式文档上传 (PDF, DOCX, TXT, MD)
- ✅ 异步文档处理队列
- ✅ 文档状态实时监控
- ✅ 批量文档管理

### 🔍 向量搜索系统
- ✅ pgvector向量数据库集成
- ✅ 语义搜索功能
- ✅ 搜索结果相关性评分
- ✅ 融合检索 (RAG + 网络搜索)

### 🔗 证据链系统
- ✅ 搜索证据追踪
- ✅ 证据可信度评分
- ✅ 证据使用状态管理
- ✅ 证据来源链接

### 🖥️ Web界面
- ✅ 现代化Vue 3前端
- ✅ 响应式设计 (支持移动端)
- ✅ 明暗主题切换
- ✅ 实时系统监控
- ✅ 文档管理界面
- ✅ 证据链可视化

### 🛠️ 系统功能
- ✅ 健康检查API
- ✅ 性能监控
- ✅ 请求日志记录
- ✅ 安全中间件
- ✅ CORS配置
- ✅ 异步任务队列

### 🔐 认证授权
- ✅ 用户认证系统
- ✅ JWT令牌管理
- ✅ 配额管理
- ✅ API使用统计

## 🚧 待办事项 (TODO)

### 高优先级
- [ ] **代码导入功能** - 支持代码文件分析
- [ ] **PPT生成功能** - 完善PPT导出器实现
- [ ] **TTS音频生成** - 完善语音合成功能
- [ ] **Stripe计费集成** - 完善付费功能
- [ ] **多模态路由** - 支持图像和视频处理
- [ ] **动态模型选择** - 基于负载和成本的智能选择
- [ ] **成本优化** - 自动选择最经济的模型
- [ ] **性能监控增强** - 更详细的性能指标
- [ ] **插件系统** - 支持第三方扩展
- [ ] **API文档生成** - 自动生成OpenAPI文档
- [ ] **单元测试覆盖** - 提高测试覆盖率

## 🛠️ 技术栈

### 后端技术
- **Python 3.11+**
- **FastAPI** - 现代化Web框架
- **SQLAlchemy** - ORM数据库操作
- **PostgreSQL + pgvector** - 向量数据库
- **Redis** - 缓存和任务队列
- **Celery** - 异步任务处理

### 前端技术
- **Vue 3** - 现代化前端框架
- **Vite** - 快速构建工具
- **Pinia** - 状态管理
- **CSS Variables** - 主题系统

### AI/ML技术
- **DeepSeek API** - 主要LLM提供商
- **Ollama** - 本地LLM服务
- **pgvector** - 向量相似度搜索
- **Sentence Transformers** - 文本嵌入

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd deep-research

# 复制环境配置
cp .env.example .env
# 编辑 .env 文件，填入必要的API密钥
```

### 2. 启动数据库服务

```bash
# 启动PostgreSQL和Redis
docker-compose -f docker-compose.dev.yml up -d postgres redis
```

### 3. 安装Python依赖

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 4. 启动后端服务

```bash
# 方式1: 使用启动脚本
chmod +x start.sh
./start.sh

# 方式2: 直接启动
python app.py
```

### 5. 启动前端服务

```bash
# 进入前端目录
cd vue

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 或使用启动脚本
./start-frontend.sh  # Linux/macOS
start-frontend.bat   # Windows
```

### 6. 访问应用

- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **pgAdmin**: http://localhost:8080 (可选)

## 📝 配置说明

### 必需配置
```bash
# LLM API密钥 (至少配置一个)
DEEPSEEK_API_KEY=your-deepseek-api-key
MOONSHOT_API_KEY=your-moonshot-api-key
OPENAI_API_KEY=your-openai-api-key

# 搜索API密钥
TAVILY_API_KEY=your-tavily-api-key

# 数据库连接
DATABASE_URL=mysql+aiomysql://deerflow:deerflow123@localhost:3306/deerflow
REDIS_URL=redis://localhost:6379/0
```

### 可选配置
```bash
# Ollama本地服务
OLLAMA_BASE_URL=http://localhost:11434/v1

# 文件上传限制
MAX_FILE_SIZE=52428800  # 50MB
ALLOWED_FILE_TYPES=.pdf,.docx,.doc,.txt,.md

# 性能配置
MAX_CONCURRENT_REQUESTS=10
TASK_WORKER_COUNT=2
```

## 🧪 测试

```bash
# 运行测试
python -m pytest test/

# 特定测试
python test/test_llm.py
python test/test_pgvector_integration.py
python test/test_full_integration.py
```

## 📊 监控和日志

### 健康检查
- **基础检查**: `GET /api/health`
- **详细检查**: `GET /api/health/detailed`
- **性能指标**: `GET /api/health/metrics`

### 日志文件
- **应用日志**: `logs/deep-research.log`
- **访问日志**: 控制台输出
- **错误日志**: 自动记录到日志文件

## 🔧 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 检查端口占用
   lsof -i :8000  # Linux/macOS
   netstat -ano | findstr :8000  # Windows
   ```

2. **数据库连接失败**
   ```bash
   # 检查数据库服务
   docker-compose -f docker-compose.dev.yml ps
   ```

3. **前端API调用失败**
   - 确认后端服务运行在8000端口
   - 检查CORS配置
   - 查看浏览器控制台错误

4. **文档处理失败**
   - 检查文件格式是否支持
   - 确认文件大小未超限
   - 查看任务队列状态

## 🤝 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持

如果遇到问题，请：
1. 查看本文档的故障排除部分
2. 检查 [Issues](../../issues) 中是否有类似问题
3. 创建新的Issue描述问题

---

**版本**: 1.0.0  
**最后更新**: 2025-01-16  
**维护者**: DeerFlow Team