# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Deep Research Platform is an AI-powered research platform with intelligent routing, multi-modal support, and enterprise-grade security. It uses a FastAPI backend with Vue.js frontend, supporting multiple LLM providers (Doubao, DeepSeek, Kimi, Ollama) and features like document processing, PPT generation, and agent-based research workflows.

## Development Commands

### Backend Development
```bash
# Start the development server
python app.py

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest test/
pytest test/test_llm.py  # Run specific test file

# Code formatting
black src/
isort src/

# LLM model testing
python test/test_llm.py  # Tests Ollama and Kimi connectivity
python test/testollama.py  # Ollama-specific tests
python test/test_tavily.py  # Search functionality tests
```

### Frontend Development
```bash
cd vue

# Start development server
npm run dev

# Build for production
npm run build

# Linting
npm run lint
npm run lint:check

# Clean dependencies
npm run clean  # Unix
npm run clean:win  # Windows
```

### Database Operations
```bash
# Initialize database (auto-runs on startup if AUTO_CREATE_TABLES=true)
python -c "from src.core.db_init import initialize_database; import asyncio; asyncio.run(initialize_database())"
```

## Architecture Overview

### Intelligent Routing System
The platform uses a sophisticated routing system in `src/llms/router.py` that automatically selects the best LLM provider based on:
- Task type (code, reasoning, research, vision, chat)
- Model capabilities (function calling, vision support)
- Cost and performance optimization
- Provider availability and health status

**Key Components:**
- `SmartModelRouter`: Capability-aware routing logic
- Model configuration files: `deepseek-rule.txt`, `doubao_rule.txt`, `ollama-rule.txt`
- Priority-based provider selection with automatic fallback

### Configuration Management
Uses Pydantic-based type-safe configuration system in `src/config/config_loader.py`:
- Hierarchical configuration: `.env` > environment variables > `conf.yaml` > defaults
- Automatic validation and type checking
- Environment-specific settings (development/production)

### Security Architecture
Multi-layered security approach:
- **Process Isolation**: Code execution in sandboxed subprocesses (`src/tools/code_exec.py`)
- **Input Validation**: Comprehensive validation for all user inputs
- **Resource Limits**: Memory, CPU, and execution time restrictions
- **AST Security**: Static code analysis before execution

### Agent System
LangGraph-based intelligent agents in `src/graph/agents.py`:
- **LLM-Driven Planning**: Dynamic research plan generation
- **Reflection Loops**: Quality assessment and plan adjustment
- **Multi-Agent Collaboration**: Specialized agents for different tasks

### Document Processing
Advanced document understanding in `src/tasks/document_processor.py`:
- **Table Detection**: Vision model-based table extraction
- **Multi-format Support**: PDF, DOCX, PPT, etc.
- **OCR Integration**: Doubao vision model for image processing

## Key Security Rules

### Critical Restrictions (see `defensive_rules.txt`)
1. **Never use `exec()` or `eval()`** - Use `SecurePythonExecutor` instead
2. **Never concatenate SQL strings** - Use parameterized queries
3. **Never trust file paths** - Always validate and normalize paths
4. **Never hardcode API keys** - Use environment variables through config system

### Safe Code Execution Pattern
```python
from src.tools.code_exec import SecurePythonExecutor

executor = SecurePythonExecutor()
result = await executor.execute(user_code)  # Automatically sandboxed
```

## Configuration Priority System

1. **Environment Variables** (highest priority)
   - `DEEP_RESEARCH_SECURITY_SECRET_KEY`
   - `DEEP_RESEARCH_LLMS_DEEPSEEK_API_KEY`
   - `DEEP_RESEARCH_CODE_EXEC_MAX_MEMORY`

2. **.env file**
   - Database URLs, API keys, service configurations

3. **conf.yaml** (structured configuration)
   - Provider priorities, model capabilities, feature flags

4. **Code defaults** (lowest priority)

## Model Capabilities System

The router maintains detailed model capabilities in `src/llms/router.py`:

```python
# Critical: deepseek-reasoner doesn't support function calling
"deepseek:deepseek-reasoner": ModelCapability(
    supports_function_calling=False  # Automatically routes to deepseek-chat when tools needed
)
```

## Testing Strategy

### LLM Testing
- `test/test_llm.py`: Comprehensive provider connectivity tests
- `test/testollama.py`: Local model validation
- `test/test_tavily.py`: Search functionality verification

### Security Testing
- Code injection prevention tests
- SQL injection validation
- Path traversal attack prevention

### Integration Testing
- `test/test_full_integration.py`: End-to-end workflow testing
- Database integration tests

## Development Workflow

1. **Backend Changes**:
   - Modify relevant modules in `src/`
   - Run `black src/ && isort src/` for formatting
   - Test with `pytest test/`
   - Verify configuration changes work with new settings system

2. **Frontend Changes**:
   - Work in `vue/src/`
   - Run `npm run lint` before committing
   - Test API integration with running backend

3. **Security Changes**:
   - Always review against `defensive_rules.txt`
   - Test security controls with security test suite
   - Verify no hardcoded secrets or unsafe patterns

## Common Patterns

### Adding New LLM Provider
1. Create provider in `src/llms/providers/`
2. Add capability definition in `src/llms/router.py`
3. Update provider priority in `conf.yaml`
4. Add configuration to environment variables

### Adding New Agent Workflow
1. Define workflow in `src/graph/workflow/`
2. Register in `src/graph/builder.py`
3. Add workflow configuration to `conf.yaml`
4. Test with integration tests

### Configuration Changes
1. Update `src/config/config_loader.py` for new settings
2. Add defaults to Pydantic models
3. Update `conf.yaml` with new sections
4. Test configuration validation on startup

## Important Notes

- The system uses intelligent routing - don't hardcode model choices
- Always use the configuration system rather than direct environment variable access
- Security is paramount - all code execution must be sandboxed
- The platform supports both local (Ollama) and cloud LLM providers
- Database initialization is automatic in development with `AUTO_CREATE_TABLES=true`