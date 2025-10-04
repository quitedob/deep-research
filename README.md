# Deep Research - 多智能体深度研究平台

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)

**基于多智能体协作的智能研究平台**

[快速开始](#快速开始) • [功能特性](#功能特性) • [文档](#文档) • [API](#api接口) • [部署](#部署)

</div>

---

## 📖 简介

Deep Research 是一个先进的多智能体深度研究平台，集成了智能搜索、内容分析、报告生成等功能。通过多个专业Agent的协作，自动完成从信息收集到报告生成的完整研究流程。

### 核心特性

- 🤖 **5个专业Agent** - 规划师、搜索专家、分析师、撰写专家、审查员
- 🔍 **多源搜索** - Kimi联网搜索、arXiv学术、Wikipedia百科
- 📊 **智能分析** - 自动分析和洞察提取
- 📝 **专业报告** - 结构化Markdown报告生成
- 🔄 **质量保证** - 自动审查和迭代改进
- 🎯 **项目管理** - 完整的研究项目生命周期管理

## 🚀 快速开始

### 前置要求

- Python 3.9+
- PostgreSQL 12+
- Redis (可选)
- Kimi API密钥

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd deep-research

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必要配置

# 运行数据库迁移
python -m src.migrations.add_research_tables

# 启动服务
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 快速测试

```bash
# 1. 注册用户
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "email": "test@example.com", "password": "Test123!"}'

# 2. 登录
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test&password=Test123!"

# 3. 创建研究项目
curl -X POST "http://localhost:8000/api/research/projects/create" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "AI研究", "query": "AI最新进展", "description": "研究AI技术"}'

# 4. 执行研究
curl -X POST "http://localhost:8000/api/research/projects/1/execute" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 💡 功能特性

### 多智能体系统

```python
from src.service.agent_manager import get_agent_manager

manager = get_agent_manager()

# 调用单个Agent
result = await manager.call_agent(
    agent_id="research_planner",
    prompt="制定AI研究计划"
)

# 多Agent协作
result = await manager.collaborate_agents(
    task="研究量子计算",
    agent_ids=["research_planner", "information_searcher", "content_analyzer"]
)
```

### 研究项目管理

```python
from src.service.research_project import ResearchProjectService

service = ResearchProjectService(db)

# 创建项目
project = await service.create_project(
    user_id=1,
    title="深度学习研究",
    query="深度学习最新进展",
    description="全面研究深度学习技术"
)

# 执行研究
await execute_research_workflow(project.id, project.query, db)
```

### 智能搜索

```python
from src.tools.search.kimi_tool import get_kimi_tool
from src.tools.search.arxiv_tool import get_arxiv_service
from src.tools.search.wikipedia_tool import get_wikipedia_tool

# Kimi搜索
kimi = get_kimi_tool()
results = await kimi.search("人工智能", max_results=10)

# arXiv搜索
arxiv = get_arxiv_service()
papers = await arxiv.search_papers("machine learning", max_results=10)

# Wikipedia搜索
wiki = get_wikipedia_tool()
pages = await wiki.search("人工智能", limit=10)
```

## 📚 文档

- [快速开始指南](QUICKSTART.md) - 详细的安装和使用教程
- [系统架构](MULTI_AGENT_SYSTEM.md) - 多智能体系统详解
- [完整实现指南](FINAL_IMPLEMENTATION_GUIDE.md) - API和开发指南
- [项目完成报告](PROJECT_COMPLETION_SUMMARY.md) - 功能清单和统计
- [API文档](http://localhost:8000/docs) - 交互式API文档

## 🔌 API接口

### Agent管理

```http
# 列出所有Agents
GET /api/agents/list

# 调用Agent
POST /api/agents/call
{
  "agent_id": "research_planner",
  "prompt": "制定研究计划"
}

# 多Agent协作
POST /api/agents/collaborate
{
  "task": "研究AI",
  "agent_ids": ["planner", "searcher", "analyzer"]
}
```

### 研究项目

```http
# 创建项目
POST /api/research/projects/create
{
  "title": "AI研究",
  "query": "AI最新进展"
}

# 执行研究
POST /api/research/projects/{id}/execute

# 获取结果
GET /api/research/projects/{id}
```

## 🏗️ 架构

```
┌─────────────────────────────────────────┐
│           用户界面 / API                 │
└──────────────┬──────────────────────────┘
               │
┌──────────────┴──────────────────────────┐
│         Agent管理器                      │
│  ┌──────────┬──────────┬──────────┐    │
│  │ 规划师   │ 搜索专家 │ 分析师   │    │
│  └──────────┴──────────┴──────────┘    │
│  ┌──────────┬──────────────────────┐   │
│  │ 撰写专家 │ 审查员               │   │
│  └──────────┴──────────────────────┘   │
└──────────────┬──────────────────────────┘
               │
┌──────────────┴──────────────────────────┐
│         工具层                           │
│  ┌──────────┬──────────┬──────────┐    │
│  │ Kimi搜索 │ arXiv    │ Wikipedia│    │
│  └──────────┴──────────┴──────────┘    │
└──────────────┬──────────────────────────┘
               │
┌──────────────┴──────────────────────────┐
│         数据层                           │
│  ┌──────────┬──────────┬──────────┐    │
│  │ PostgreSQL│ Redis   │ 文件系统 │    │
│  └──────────┴──────────┴──────────┘    │
└─────────────────────────────────────────┘
```

## 🐳 部署

### Docker

```bash
docker build -t deep-research .
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e KIMI_API_KEY=your_key \
  deep-research
```

### Docker Compose

```bash
docker-compose up -d
```

### Kubernetes

```bash
kubectl apply -f k8s/deployment.yaml
```

## 🔧 配置

### 环境变量

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/deep_research

# Kimi API
KIMI_API_KEY=your_kimi_api_key
KIMI_BASE_URL=https://api.moonshot.cn/v1

# JWT
JWT_SECRET_KEY=your_secret_key

# Redis (可选)
REDIS_URL=redis://localhost:6379
```

### LLM配置

```yaml
llm:
  providers:
    kimi:
      enabled: true
      api_key: ${KIMI_API_KEY}
      models:
        - moonshot-v1-32k
```

## 📊 性能

- **搜索响应**: < 5秒
- **报告生成**: 30-60秒
- **完整研究**: 2-5分钟
- **并发支持**: 10+项目

## 🧪 测试

```bash
# 运行测试
pytest tests/

# 测试覆盖率
pytest --cov=src tests/

# 测试单个Agent
python -c "
import asyncio
from src.service.agent_manager import get_agent_manager

async def test():
    manager = get_agent_manager()
    result = await manager.call_agent('research_planner', '制定计划')
    print(result)

asyncio.run(test())
"
```

## 🤝 贡献

欢迎贡献！请查看 [贡献指南](CONTRIBUTING.md)。

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 📝 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [LangGraph](https://github.com/langchain-ai/langgraph) - 工作流编排
- [FastAPI](https://fastapi.tiangolo.com/) - Web框架
- [SQLModel](https://sqlmodel.tiangolo.com/) - ORM
- [Kimi API](https://platform.moonshot.cn/) - LLM服务

## 📞 联系

- 项目主页: [GitHub Repository]
- 问题反馈: [GitHub Issues]
- 文档: [Documentation]
- 邮箱: [Email]

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个Star！⭐**

Made with ❤️ by Deep Research Team

</div>
