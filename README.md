# Deep Research Platform

An AI-powered research platform with intelligent routing, multi-modal support, and enterprise-grade security.

## 🚀 Features

### Core Capabilities
- **Intelligent LLM Routing**: Automatically selects the best model based on task type
- **Multi-Provider Support**: DeepSeek, Doubao, Kimi, ZhipuAI, Ollama
- **Agent-Based Research**: LangGraph-powered multi-agent workflows
- **Document Processing**: Advanced PDF, DOCX, PPT analysis with OCR
- **RAG System**: Two-stage retrieval with cross-encoder re-ranking

### Advanced Features
- **🔍 Conversation Search**: Full-text search with filtering and relevance scoring
- **🔗 Public Sharing**: Share conversations with customizable links
- **👍 Feedback System**: User feedback collection for AI responses
- **🛡️ Content Moderation**: Reporting and review workflow
- **📊 System Monitoring**: Health checks and cost tracking
- **🔒 Security Audit**: Comprehensive admin operation logging

## 📁 Project Structure

### Backend (`src/`)

```
src/
├── agents/                          # AI Agent System
│   ├── base_agent.py               # Base agent class
│   ├── react_agent.py              # ReAct pattern implementation
│   ├── research_agent.py           # Research workflow agent
│   ├── task_decomposition.py       # Task decomposition logic
│   └── prompt_templates.py         # Agent prompt templates
├── api/                            # REST API Endpoints
│   ├── auth.py                     # Authentication & authorization
│   ├── admin.py                    # Admin management functions
│   ├── feedback.py                 # User feedback collection
│   ├── moderation.py               # Content moderation workflow
│   ├── monitoring.py               # System health monitoring
│   ├── conversation.py             # Chat management
│   ├── billing.py                  # Payment integration
│   ├── file_upload.py             # Document upload processing
│   ├── llm_config.py              # LLM provider configuration
│   └── deps.py                     # API dependencies
├── config/                         # Configuration Management
│   ├── config_loader.py            # Type-safe configuration system
│   └── defensive_rules.txt         # Security guidelines
├── core/                           # Core Business Logic
│   ├── rag/                        # RAG (Retrieval-Augmented Generation)
│   │   ├── reranker.py            # Two-stage retrieval with re-ranking
│   │   └── ...                    # RAG components
│   ├── db/                        # Database Layer
│   │   └── ...                    # Database utilities
│   └── ...                        # Core modules
├── export/                         # Export Functionality
│   ├── markdown.py                 # Markdown export
│   ├── ppt.py                      # PPT generation
│   ├── pptx.py                     # Enhanced PPT export
│   ├── tts.py                      # Text-to-speech
│   └── tts_edge.py                 # Edge TTS integration
├── graph/                          # LangGraph Workflow System
│   ├── agents.py                   # Graph agent definitions
│   ├── builder.py                  # Workflow builder
│   └── workflow/                   # Workflow implementations
├── llms/                           # LLM Provider Layer
│   ├── router.py                   # Intelligent model routing
│   └── providers/                  # LLM provider implementations
│       ├── deepseek_llm.py         # DeepSeek integration
│       ├── doubao_llm.py           # Doubao integration
│       ├── kimi_llm.py             # Kimi integration
│       ├── ollama_llm.py           # Ollama local models
│       └── zhipuai_llm.py          # ZhipuAI integration
├── serve/                          # API Server
│   ├── api.py                      # Main API routes
│   ├── chat_stream.py              # Streaming chat endpoint
│   ├── session_store.py            # Session management
│   └── sanitizer.py                # Input sanitization
├── services/                       # Service Layer
│   ├── audit_service.py            # Admin audit logging
│   └── unified_search.py           # Search service integration
├── sqlmodel/                       # Database Models
│   └── models.py                   # SQLAlchemy models
├── tasks/                          # Task Processing
│   ├── document_processor.py       # Document analysis
│   └── ...                        # Task handlers
└── tools/                          # Utility Tools
    ├── code_exec.py                # Secure code execution
    └── ...                        # Utility functions
```

### Frontend (`vue/src/`)

```
vue/src/
├── components/                     # Vue Components
│   ├── ChatContainer.vue           # Main chat interface
│   ├── MessageItem.vue             # Chat message with feedback/sharing
│   ├── DocumentManager.vue         # File upload & management
│   ├── ResearchActivities.vue      # Research workflow UI
│   ├── PublicConversation.vue      # Shared conversation viewer
│   ├── Dashboard.vue               # Admin dashboard
│   ├── ModelSelector.vue           # LLM model selection
│   ├── EvidenceChain.vue           # Source evidence display
│   ├── FileUpload.vue              # Drag-drop file upload
│   ├── PPTGenerator.vue            # PPT generation interface
│   ├── HistoryList.vue             # Conversation history
│   └── ...                         # Additional components
├── services/                       # API Services
│   ├── api.js                      # API client configuration
│   ├── ollama.js                   # Ollama service integration
│   └── ...                         # Service modules
├── views/                          # Page Views
│   ├── Admin.vue                   # Admin interface
│   ├── Chat.vue                    # Main chat page
│   ├── Dashboard.vue               # User dashboard
│   ├── Login.vue                   # Authentication
│   ├── Register.vue                # User registration
│   └── ...                         # Additional views
├── assets/                         # Static Assets
│   └── ...                         # Images, styles, etc.
├── router/                         # Vue Router
│   └── index.js                    # Route definitions
├── stores/                         # State Management
│   └── ...                         # Pinia stores
├── App.vue                         # Root component
└── main.js                         # Application entry point
```

## 🛠️ Technology Stack

### Backend
- **FastAPI**: High-performance async web framework
- **SQLAlchemy**: ORM with async support
- **PostgreSQL**: Primary database with pgvector
- **Redis**: Caching and session storage
- **LangGraph**: Agent workflow orchestration
- **Pydantic**: Type-safe configuration and validation

### Frontend
- **Vue.js 3**: Modern frontend framework
- **Vite**: Fast build tool
- **Pinia**: State management
- **Vue Router**: Client-side routing
- **TailwindCSS**: Utility-first CSS framework

### AI/ML Integration
- **OpenAI SDK**: LLM API integration
- **Multiple Providers**: DeepSeek, Doubao, Kimi, ZhipuAI, Ollama
- **RAG Pipeline**: Advanced retrieval system
- **Vector Search**: Semantic document retrieval

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 13+
- Redis 6+

### Backend Setup

1. **Clone and Install Dependencies**
```bash
git clone <repository-url>
cd deep-research
pip install -r requirements.txt
```

2. **Environment Configuration**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

3. **Database Setup**
```bash
# PostgreSQL database setup
createdb deerflow

# Tables are created automatically with AUTO_CREATE_TABLES=true
```

4. **Start Backend Server**
```bash
python app.py
```

### Frontend Setup

1. **Install Dependencies**
```bash
cd vue
npm install
```

2. **Start Development Server**
```bash
npm run dev
```

## 🔧 Configuration

### Environment Variables

Key environment variables (see `.env.example` for complete list):

```bash
# Security (Required)
DEEP_RESEARCH_SECURITY_SECRET_KEY=your-secret-key-here

# LLM Providers (Configure as needed)
DEEP_RESEARCH_DEEPSEEK_API_KEY=sk-your-deepseek-key
DEEP_RESEARCH_DOUBAO_API_KEY=your-doubao-key
DEEP_RESEARCH_KIMI_API_KEY=sk-your-kimi-key
DEEP_RESEARCH_ZHIPUAI_API_KEY=your-zhipuai-key

# Database
DEEP_RESEARCH_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db

# Redis
DEEP_RESEARCH_REDIS_URL=redis://localhost:6379
```

### Model Configuration

The platform uses intelligent routing to automatically select the best model:

- **Code Tasks**: DeepSeek (strongest reasoning)
- **Research**: ZhipuAI (with web search)
- **General Chat**: Ollama (local, cost-effective)
- **Vision Tasks**: ZhipuAI or Doubao (multi-modal support)

## 📊 API Documentation

### Core Endpoints

#### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/auth/me` - Get current user

#### Chat & Research
- `POST /api/chat` - Simple chat
- `POST /api/llm/chat` - Advanced chat with routing
- `POST /api/research` - Multi-agent research workflow

#### Features
- `POST /api/search/conversations` - Search conversation history
- `POST /api/share/conversation` - Create share link
- `GET /api/public/conversation/{id}` - View shared conversation
- `POST /api/feedback/submit` - Submit feedback
- `POST /api/moderation/report` - Report content

#### Admin
- `GET /api/admin/audit-logs` - Admin audit trail
- `GET /api/monitoring/health` - System health
- `GET /api/moderation/admin/queue` - Content moderation queue

## 🔒 Security Features

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- API rate limiting and quotas

### Content Safety
- Input validation and sanitization
- Content moderation workflow
- User reporting system

### Audit & Compliance
- Comprehensive admin operation logging
- Security event tracking
- Compliance-ready audit trails

## 🤖 AI Agent System

### Agent Types
- **Research Agent**: Multi-step research workflow
- **Triage Agent**: Task classification and routing
- **User Agent**: User intent analysis

### Workflow Features
- Dynamic plan generation
- Reflection and quality assessment
- Multi-agent collaboration
- Human-in-the-loop feedback

## 📈 Monitoring & Analytics

### System Health
- Real-time health checks
- Performance metrics
- Error tracking and alerts

### Usage Analytics
- Token usage tracking
- Cost analysis
- Provider performance comparison

### User Analytics
- Feedback analysis
- Search patterns
- Feature usage statistics

## 🚀 Deployment

### Production Deployment

1. **Environment Preparation**
```bash
# Set production environment
export DEEP_RESEARCH_ENVIRONMENT=production
export DEEP_RESEARCH_DEBUG=false

# Configure production database
export DEEP_RESEARCH_DATABASE_URL=postgresql+asyncpg://prod_user:pass@prod_host/prod_db
```

2. **Build Frontend**
```bash
cd vue
npm run build
```

3. **Run Backend**
```bash
# Use production server
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Deployment

```dockerfile
# Dockerfile example
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🧪 Testing

### Backend Tests
```bash
# Run all tests
pytest test/

# Run specific test file
pytest test/test_llm.py

# Run with coverage
pytest --cov=src test/
```

### Frontend Tests
```bash
cd vue
npm run test
npm run lint
```

## 📝 Development Guide

### Code Style
- **Backend**: Black, isort, flake8
- **Frontend**: ESLint, Prettier
- **Type Hints**: Required for all Python functions

### Adding New LLM Providers
1. Create provider in `src/llms/providers/`
2. Add capability definition in `src/llms/router.py`
3. Update configuration in `conf.yaml`
4. Add tests in `test/`

### Adding New Agent Workflows
1. Define workflow in `src/graph/workflow/`
2. Register in `src/graph/builder.py`
3. Add configuration to `conf.yaml`
4. Create UI components if needed

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: See `/docs` directory
- **Issues**: Create an issue on GitHub
- **Discussions**: Join our community discussions

## 🗺️ Roadmap

### Upcoming Features
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Plugin system
- [ ] Advanced RAG features
- [ ] Real-time collaboration
- [ ] Mobile applications

### Current Focus
- Performance optimization
- Enhanced security features
- Improved user experience
- Extended provider support

---

**Built with ❤️ by the Deep Research Platform team**