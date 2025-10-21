# Deep Research Platform - Advanced Research Integration Guide

## 📋 Overview

This guide provides comprehensive documentation for the advanced research functionality integrated into the Deep Research Platform, inspired by AgentScope v1.0.0. The system includes intelligent research planning, multi-agent orchestration, evidence chain analysis, and real-time monitoring capabilities.

## 🎯 Table of Contents

1. [System Architecture](#system-architecture)
2. [Core Components](#core-components)
3. [Research Workflow](#research-workflow)
4. [API Integration](#api-integration)
5. [Frontend Components](#frontend-components)
6. [Database Schema](#database-schema)
7. [Error Handling](#error-handling)
8. [Performance Monitoring](#performance-monitoring)
9. [Testing Guide](#testing-guide)
10. [Deployment](#deployment)

---

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Layer     │    │   Backend       │
│   (Vue.js)      │◄──►│   (FastAPI)     │◄──►│   Services      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Research UI   │    │   Research API  │    │   Research      │
│   Components    │    │   Endpoints     │    │   Services      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────────────────────────────────────────────────┐
│                 Database Layer (SQLite)                     │
│  Projects | Research Plans | Evidence | Agents | Metrics   │
└─────────────────────────────────────────────────────────────┘
```

### Component Relationships

```
PlanNotebook ──► ResearchPlanner ──► MultiAgentOrchestrator
      │                   │                      │
      ▼                   ▼                      ▼
   Storage         EvidenceChainAnalyzer    SpecializedAgents
      │                   │                      │
      ▼                   ▼                      ▼
   Database        EvidenceAnalysis        AgentExecution
```

---

## 🔧 Core Components

### 1. Plan Management System

#### PlanNotebook (`src/core/plan/plan_notebook.py`)

Central repository for managing research plans with both manual and agent-managed capabilities.

**Key Features:**
- Plan CRUD operations
- Change notifications
- Tool integration
- Hook system for extensibility

**Usage Example:**
```python
from core.plan.plan_notebook import PlanNotebook

notebook = PlanNotebook()

# Add a plan
await notebook.add_plan(plan)

# Get a plan
plan = await notebook.get_plan(plan_id)

# List all plans
plans = await notebook.list_plans()

# Update a plan
await notebook.update_plan(plan)
```

#### ResearchPlanner (`src/core/plan/planner.py`)

Intelligent research planning system that generates comprehensive research workflows.

**Key Features:**
- Automatic step generation
- Research type analysis
- Working plan creation
- Progress evaluation

**Usage Example:**
```python
from core.plan.planner import ResearchPlanner

planner = ResearchPlanner()

# Create a research plan
plan = await planner.create_research_plan(
    title="AI Ethics Research",
    description="Analysis of AI ethics principles",
    domain="technology",
    research_type="analytical",
    research_query="What are the main ethical considerations in AI?"
)
```

### 2. Multi-Agent Orchestration

#### MultiAgentOrchestrator (`src/core/research/multi_agent_orchestrator.py`)

Coordinates multiple specialized agents for collaborative research workflows.

**Key Features:**
- Agent registration and management
- Task assignment and distribution
- Sequential and parallel execution
- Adaptive execution strategies
- Real-time progress monitoring

**Usage Example:**
```python
from core.research.multi_agent_orchestrator import MultiAgentOrchestrator
from core.research.agents.research_agent import ResearchAgent

orchestrator = MultiAgentOrchestrator()

# Register agents
await orchestrator.register_agent(ResearchAgent("researcher_1"))

# Execute research workflow
result = await orchestrator.execute_research_workflow(
    plan_id="plan_123",
    execution_strategy="parallel"
)
```

#### Specialized Agents

**ResearchAgent** (`src/core/research/agents/research_agent.py`)
- Literature review and information gathering
- Source validation and credibility assessment
- Research question formulation

**EvidenceAgent** (`src/core/research/agents/evidence_agent.py`)
- Evidence collection and organization
- Quality assessment and scoring
- Source verification and fact-checking

**SynthesisAgent** (`src/core/research/agents/synthesis_agent.py`)
- Research synthesis and integration
- Insight generation and pattern identification
- Report generation and formatting

### 3. Evidence Chain Analysis

#### EvidenceChainAnalyzer (`src/core/research/evidence_chain.py`)

Sophisticated evidence analysis system for building and evaluating evidence chains.

**Key Features:**
- Evidence quality assessment
- Relationship analysis
- Confidence scoring
- Chain validation

**Usage Example:**
```python
from core.research.evidence_chain import EvidenceChainAnalyzer

analyzer = EvidenceChainAnalyzer()

# Analyze evidence quality
quality_result = await analyzer.assess_evidence_quality(evidence_items)

# Analyze evidence relationships
relationship_result = await analyzer.analyze_evidence_relationships(evidence_items)
```

---

## 🔄 Research Workflow

### Complete Research Process

1. **Planning Phase**
   ```
   User Input → ResearchPlanner → Plan Generation → PlanNotebook Storage
   ```

2. **Execution Phase**
   ```
   Plan Selection → MultiAgentOrchestrator → Agent Coordination → Task Execution
   ```

3. **Evidence Collection**
   ```
   Task Results → EvidenceAgent → Quality Assessment → EvidenceChainAnalyzer
   ```

4. **Synthesis Phase**
   ```
   Evidence Chain → SynthesisAgent → Research Integration → Final Report
   ```

5. **Monitoring & Optimization**
   ```
   Real-time Tracking → PerformanceMonitor → Error Handling → Adaptive Adjustments
   ```

### Workflow Diagram

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   User      │    │  Planner    │    │ Orchestrator│    │   Agents    │
│  Request    │───►│  Analysis   │───►│ Assignment  │───►│ Execution   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                           │                   │                   │
                           ▼                   ▼                   ▼
                   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
                   │   Plan      │    │   Progress  │    │   Results   │
                   │  Storage    │    │  Monitoring │    │ Collection  │
                   └─────────────┘    └─────────────┘    └─────────────┘
                                                     │
                                                     ▼
                                            ┌─────────────┐
                                            │ Evidence    │
                                            │  Analysis   │
                                            └─────────────┘
                                                     │
                                                     ▼
                                            ┌─────────────┐
                                            │ Synthesis   │
                                            │   Report    │
                                            └─────────────┘
```

---

## 🌐 API Integration

### Research Planning API

#### Endpoints

**POST /api/research/planning/create**
```json
{
  "title": "Research Title",
  "description": "Research Description",
  "domain": "technology",
  "research_type": "analytical",
  "research_query": "Research question"
}
```

**GET /api/research/planning/plans/{plan_id}**
```json
{
  "id": "plan_123",
  "title": "Research Title",
  "status": "created",
  "subtasks": [...],
  "created_at": "2025-01-01T00:00:00Z"
}
```

**POST /api/research/planning/execute**
```json
{
  "plan_id": "plan_123",
  "execution_strategy": "parallel"
}
```

### Multi-Agent Orchestration API

#### Endpoints

**GET /api/research/orchestrator/status/{plan_id}**
```json
{
  "plan_id": "plan_123",
  "status": "in_progress",
  "agents": [...],
  "progress": 0.65,
  "estimated_completion": "2025-01-01T01:30:00Z"
}
```

**POST /api/research/orchestrator/assign-tasks**
```json
{
  "plan_id": "plan_123",
  "agent_assignments": {
    "research_agent_1": ["task_1", "task_2"],
    "evidence_agent_1": ["task_3"]
  }
}
```

### Evidence Chain API

#### Endpoints

**POST /api/research/evidence/analyze**
```json
{
  "evidence_items": [...],
  "analysis_type": "quality_assessment"
}
```

**GET /api/research/evidence/chains/{chain_id}**
```json
{
  "id": "chain_123",
  "evidence_items": [...],
  "confidence_level": 0.85,
  "quality_score": 0.78
}
```

### Real-time Monitoring API

#### WebSocket Endpoints

**WS /api/research/monitoring/realtime**
```javascript
// Real-time updates for research progress
const ws = new WebSocket('ws://localhost:8000/api/research/monitoring/realtime');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle real-time updates
};
```

**GET /api/research/monitoring/metrics**
```json
{
  "system_performance": {...},
  "agent_performance": {...},
  "active_plans": 5,
  "queue_length": 12
}
```

---

## 🎨 Frontend Components

### Research Planning Interface

#### ResearchPlanner.vue (`vue/src/components/research/ResearchPlanner.vue`)

Main interface for creating and managing research plans.

**Features:**
- Interactive plan creation wizard
- Real-time plan validation
- Progress visualization
- Plan history management

**Usage:**
```vue
<template>
  <div class="research-planner">
    <ResearchPlanWizard @plan-created="handlePlanCreated" />
    <PlanList :plans="plans" @plan-selected="handlePlanSelected" />
    <ProgressTracker :plan-id="selectedPlanId" />
  </div>
</template>
```

### Multi-Agent Orchestration UI

#### MultiAgentOrchestrator.vue (`vue/src/components/research/MultiAgentOrchestrator.vue`)

Dashboard for monitoring and controlling multi-agent workflows.

**Features:**
- Real-time agent status
- Task assignment interface
- Performance metrics
- Intervention controls

### Evidence Chain Visualization

#### EvidenceChainVisualization.vue (`vue/src/components/research/EvidenceChainVisualization.vue`)

Interactive visualization of evidence relationships and quality.

**Features:**
- Network graph visualization
- Evidence quality indicators
- Interactive filtering
- Export capabilities

### Real-time Monitoring

#### RealTimeMonitoring.vue (`vue/src/components/research/RealTimeMonitoring.vue`)

Live system monitoring and performance dashboard.

**Features:**
- Real-time metrics
- System alerts
- Performance graphs
- Resource usage tracking

---

## 🗄️ Database Schema

### Core Tables

#### research_plans
```sql
CREATE TABLE research_plans (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    project_id TEXT,
    title TEXT NOT NULL,
    description TEXT,
    domain TEXT,
    research_type TEXT,
    research_query TEXT,
    status TEXT DEFAULT 'created',
    progress_percentage REAL DEFAULT 0.0,
    key_findings TEXT, -- JSON
    insights TEXT, -- JSON
    metadata TEXT, -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### evidence_chains
```sql
CREATE TABLE evidence_chains (
    id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL,
    title TEXT,
    description TEXT,
    status TEXT DEFAULT 'active',
    confidence_level REAL DEFAULT 0.0,
    quality_score REAL DEFAULT 0.0,
    synthesis_result TEXT, -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### agents
```sql
CREATE TABLE agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    status TEXT DEFAULT 'idle',
    capabilities TEXT, -- JSON list
    current_task_id TEXT,
    success_rate REAL DEFAULT 0.0,
    total_tasks INTEGER DEFAULT 0,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### agent_tasks
```sql
CREATE TABLE agent_tasks (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    task_type TEXT NOT NULL,
    task_description TEXT,
    parameters TEXT, -- JSON
    status TEXT DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    progress REAL DEFAULT 0.0,
    result TEXT, -- JSON
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

### Performance Indexes

```sql
-- Research plan indexes
CREATE INDEX idx_research_plans_user_status ON research_plans(user_id, status);
CREATE INDEX idx_research_plans_created_at ON research_plans(created_at);

-- Agent performance indexes
CREATE INDEX idx_agents_type_status ON agents(agent_type, status);
CREATE INDEX idx_agent_tasks_agent_status ON agent_tasks(agent_id, status);

-- Evidence chain indexes
CREATE INDEX idx_evidence_chains_plan_status ON evidence_chains(plan_id, status);
CREATE INDEX idx_evidence_items_chain_type ON evidence_items(chain_id, evidence_type);
```

---

## ⚠️ Error Handling

### Comprehensive Error Management

#### Error Types
- **Agent Failure**: Agent execution failures
- **Network Error**: Communication failures
- **Database Error**: Data persistence issues
- **Validation Error**: Input validation failures
- **Timeout Error**: Operation timeouts
- **Resource Error**: Resource exhaustion
- **Task Execution Error**: Task-specific failures
- **Synthesis Error**: Research synthesis failures
- **Evidence Error**: Evidence processing failures
- **Plan Error**: Planning system failures

#### Recovery Strategies
- **Retry**: Automatic retry with exponential backoff
- **Restart Agent**: Agent restart and recovery
- **Fallback Provider**: Switch to alternative providers
- **Graceful Degradation**: Reduced functionality mode
- **Skip Task**: Continue without failed task
- **Escalate**: Notify administrators
- **Manual Intervention**: Require human intervention

#### Error Handling Implementation

```python
from core.research.error_handler import global_error_handler, ErrorType

try:
    result = await research_function()
except Exception as e:
    error_event = await global_error_handler.handle_error(
        error=e,
        error_type=ErrorType.AGENT_FAILURE,
        context={'agent_id': 'agent_123', 'task_id': 'task_456'},
        severity=ErrorSeverity.MEDIUM
    )
```

### Circuit Breaker Pattern

```python
from core.research.error_handler import CircuitBreaker

circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

async def protected_function():
    return await circuit_breaker.call(risky_function)
```

---

## 📊 Performance Monitoring

### Metrics Collection

#### System Metrics
- CPU usage
- Memory usage
- Disk usage
- Network I/O
- Active agents
- Active plans
- Queue length
- Response time
- Error rate
- Throughput

#### Agent Metrics
- Tasks completed
- Tasks failed
- Average task time
- Success rate
- Memory usage
- CPU usage
- Last activity

#### Custom Metrics

```python
from core.research.performance_monitor import global_monitor, monitor_performance

# Manual metric recording
global_monitor.increment_counter('research_plans_created')
global_monitor.set_gauge('active_agents', 5)
global_monitor.record_timer('task_execution_time', 2.5)

# Automatic monitoring with decorator
@monitor_performance('research_plan_creation')
async def create_research_plan(title, description):
    # Function implementation
    pass
```

### Performance Monitoring Dashboard

Real-time monitoring interface with:
- System resource usage
- Agent performance metrics
- Request/response patterns
- Error rate tracking
- Alert management

---

## 🧪 Testing Guide

### Running Tests

#### Unit Tests
```bash
# Run all unit tests
pytest test/unit/

# Run specific test file
pytest test/unit/test_research_planner.py

# Run with coverage
pytest test/unit/ --cov=src/core/research
```

#### Integration Tests
```bash
# Run comprehensive integration tests
python test/research_integration_test.py
```

#### Test Coverage Areas

1. **Plan Management**
   - Plan creation and validation
   - Storage operations
   - Plan notebook functionality

2. **Multi-Agent Orchestration**
   - Agent registration
   - Task assignment
   - Workflow execution
   - Error handling

3. **Evidence Chain Analysis**
   - Evidence quality assessment
   - Relationship analysis
   - Chain validation

4. **API Endpoints**
   - Request/response validation
   - Error handling
   - Authentication/authorization

5. **Database Operations**
   - CRUD operations
   - Transaction handling
   - Data integrity

6. **Performance**
   - Load testing
   - Stress testing
   - Memory usage

### Test Data Management

#### Test Fixtures
```python
@pytest.fixture
async def sample_research_plan():
    return ResearchPlan(
        id="test_plan_1",
        title="Test Research Plan",
        description="A test plan for unit testing",
        domain="technology",
        research_type="analytical",
        research_query="Test research question"
    )
```

#### Mock Services
```python
@pytest.fixture
async def mock_orchestrator():
    orchestrator = MultiAgentOrchestrator()
    # Setup mock agents and services
    return orchestrator
```

---

## 🚀 Deployment

### Environment Setup

#### Production Configuration

```python
# conf.yaml
research:
  enabled: true
  max_concurrent_plans: 10
  agent_timeout: 300
  evidence_quality_threshold: 0.7

performance:
  monitoring_enabled: true
  collection_interval: 5.0
  alert_thresholds:
    cpu_usage: 80.0
    memory_usage: 85.0
    error_rate: 0.05
```

#### Database Migration

```bash
# Run database migrations
python src/core/database/migrations/run_migration.py

# Verify migration
python -c "
import sqlite3
conn = sqlite3.connect('deep_research.db')
print('Tables:', conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall())
"
```

### Service Dependencies

#### Required Services
- **FastAPI**: Main application server
- **SQLite**: Database (configurable to PostgreSQL)
- **Redis**: Caching and session storage (optional)
- **LLM Providers**: External AI services (OpenAI, Ollama, etc.)

#### Optional Services
- **Monitoring**: Prometheus/Grafana for advanced monitoring
- **Logging**: ELK stack for log aggregation
- **Queue**: Redis/Celery for task queue management

### Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY vue/dist/ ./static/

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### docker-compose.yml
```yaml
version: '3.8'
services:
  deep-research:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./deep_research.db
      - RESEARCH_ENABLED=true
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
```

### Monitoring and Logging

#### Application Logging
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/research.log'),
        logging.StreamHandler()
    ]
)
```

#### Health Checks
```python
@app.get("/health/research")
async def research_health_check():
    return {
        "status": "healthy",
        "components": {
            "planner": await check_planner_health(),
            "orchestrator": await check_orchestrator_health(),
            "database": await check_database_health()
        }
    }
```

---

## 📚 Additional Resources

### API Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Configuration Reference
- **Main Config**: `conf.yaml`
- **Environment Variables**: `.env`
- **Security Rules**: `src/core/security/defensive_rules.txt`

### Troubleshooting

#### Common Issues

1. **Agent Timeout**
   - Check agent configuration
   - Verify LLM provider connectivity
   - Review timeout settings

2. **Database Connection Issues**
   - Verify database file permissions
   - Check connection string configuration
   - Run database migration

3. **Performance Issues**
   - Monitor system resources
   - Check agent workload distribution
   - Review evidence processing complexity

#### Debug Mode
```python
# Enable debug logging
import logging
logging.getLogger('core.research').setLevel(logging.DEBUG)
```

---

## 🎯 Best Practices

### Development
1. **Follow Async Patterns**: Use async/await for all I/O operations
2. **Error Handling**: Implement comprehensive error handling
3. **Resource Management**: Properly manage database connections and resources
4. **Testing**: Write comprehensive unit and integration tests
5. **Documentation**: Maintain up-to-date API documentation

### Operations
1. **Monitoring**: Enable performance monitoring and alerting
2. **Logging**: Implement structured logging with appropriate levels
3. **Backups**: Regular database backups and configuration versioning
4. **Security**: Follow security best practices and regular audits
5. **Scaling**: Monitor resource usage and plan for scale

### Research Workflow Design
1. **Modular Plans**: Break complex research into manageable subtasks
2. **Quality Thresholds**: Set appropriate evidence quality thresholds
3. **Agent Selection**: Choose appropriate agents for specific tasks
4. **Progress Tracking**: Implement clear progress indicators
5. **User Feedback**: Collect and incorporate user feedback

---

*Last Updated: January 2025*
*Version: 1.0.0*
*Platform: Deep Research Platform*