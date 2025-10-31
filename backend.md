# Deep Research Platform - Backend API Documentation

## Overview

The Deep Research Platform provides a comprehensive RESTful API for AI-powered research, document processing, and knowledge management. This document describes all available API endpoints, authentication methods, request/response models, and usage guidelines.

## Table of Contents

1. [Base URL](#base-url)
2. [Authentication](#authentication)
3. [Common Response Formats](#common-response-formats)
4. [Error Handling](#error-handling)
5. [API Endpoints](#api-endpoints)
   - [Authentication](#authentication-endpoints)
   - [User Management](#user-management-endpoints)
   - [Health & Monitoring](#health--monitoring-endpoints)
   - [Chat & Conversation](#chat--conversation-endpoints)
   - [Research](#research-endpoints)
   - [Document & RAG](#document--rag-endpoints)
   - [File Upload](#file-upload-endpoints)
   - [OCR](#ocr-endpoints)
   - [Search](#search-endpoints)
   - [Evidence Chain](#evidence-chain-endpoints)
   - [Billing & Subscription](#billing--subscription-endpoints)
   - [Moderation](#moderation-endpoints)
   - [Admin Management](#admin-management-endpoints)
6. [Rate Limiting & Quotas](#rate-limiting--quotas)
7. [SDK & Integration Examples](#sdk--integration-examples)

## Base URL

```
http://localhost:8000/api
```

## API Statistics

- **Total API Files**: 32
- **Total Endpoints**: 80+
- **Authentication Method**: OAuth2 with JWT tokens
- **Content Type**: JSON (except file uploads: multipart/form-data)
- **Architecture**: RESTful with proper HTTP methods
- **Rate Limiting**: Role-based quotas
- **Error Handling**: Standardized JSON error responses

## Endpoint Categories & Parameter Count

### Authentication (3 endpoints)
- `POST /auth/register` - 3 parameters (username, email, password)
- `POST /auth/login` - 2 parameters (username, password)
- `GET /auth/me` - 0 parameters (token-based)

### User Management (6 endpoints)
- `POST /user/onboarding` - 3 parameters (action, step, data)
- `GET /user/onboarding/status` - 0 parameters
- `POST /user/preferences` - 1 parameter (preferences object)
- `GET /user/preferences` - 0 parameters
- `GET /system/info` - 0 parameters
- Average: 1.2 parameters per endpoint

### Health & Monitoring (3 endpoints)
- `GET /health/` - 0 parameters
- `GET /health/detailed` - 0 parameters (admin-only)
- `GET /health/performance` - 0 parameters (admin-only)

### Chat & Conversation (8 endpoints)
- `POST /llm/chat` - 5 parameters (messages, task, size, temperature, max_tokens)
- `POST /chat` - 2 parameters (message, session_id)
- `GET /conversation/sessions` - 2 parameters (page, page_size)
- `POST /conversation/sessions` - 2 parameters (title, initial_message)
- `GET /conversation/sessions/{session_id}` - 1 parameter (session_id)
- `POST /conversation/sessions/{session_id}/messages` - 2 parameters (role, content)
- `DELETE /conversation/sessions/{session_id}` - 1 parameter (session_id)
- `GET /conversation/memory/summary` - 0 parameters
- Average: 1.9 parameters per endpoint

### Research Workflows (3 endpoints)
- `POST /research` - 6 parameters (query, session_id, depth, sources, language, options)
- `GET /research/{session_id}` - 1 parameter (session_id)
- `GET /research/stream/{session_id}` - 1 parameter (session_id)
- Average: 2.7 parameters per endpoint

### Document & RAG (10 endpoints)
- `POST /rag/upload-document` - 1 parameter (file)
- `GET /rag/document/{job_id}` - 1 parameter (job_id)
- `GET /rag/documents` - 2 parameters (page, page_size)
- `DELETE /rag/document/{job_id}` - 1 parameter (job_id)
- `POST /rag/document/{job_id}/retry` - 1 parameter (job_id)
- `GET /rag/search` - 4 parameters (query, limit, score_threshold, use_reranking)
- `GET /rag/knowledge-bases` - 0 parameters
- `POST /rag/knowledge-bases` - 2 parameters (name, description)
- `DELETE /rag/knowledge-bases/{kb_name}` - 1 parameter (kb_name)
- `POST /rag/knowledge-bases/{kb_name}/upload` - 1 parameter (file)
- `POST /rag/knowledge-bases/{kb_name}/search` - 2 parameters (query, top_k)
- Average: 1.4 parameters per endpoint

### File Management (4 endpoints)
- `POST /files/upload` - 1 parameter (file)
- `GET /files/{file_id}/status` - 1 parameter (file_id)
- `GET /files/list` - 2 parameters (skip, limit)
- `DELETE /files/{file_id}` - 1 parameter (file_id)
- Average: 1.3 parameters per endpoint

### OCR Services (3 endpoints)
- `POST /ocr/recognize` - 1 parameter (file)
- `GET /ocr/status` - 0 parameters
- `POST /ocr/batch` - 1 parameter (files)
- Average: 0.7 parameters per endpoint

### Search Services (4 endpoints)
- `GET /search/providers` - 0 parameters
- `POST /search/providers/set` - 1 parameter (provider)
- `POST /search/` - 4 parameters (query, provider, system_prompt, search_limit)
- `GET /search/test/{provider}` - 1 parameter (provider)
- Average: 1.5 parameters per endpoint

### Evidence Chain (4 endpoints)
- `GET /evidence/conversation/{conversation_id}` - 3 parameters (conversation_id, limit, offset)
- `GET /evidence/research/{research_session_id}` - 3 parameters (research_session_id, limit, offset)
- `PUT /evidence/evidence/{evidence_id}/mark_used` - 2 parameters (evidence_id, used)
- `GET /evidence/stats` - 1 parameter (days)
- Average: 2.3 parameters per endpoint

### Billing & Subscription (4 endpoints)
- `POST /billing/create-checkout-session` - 0 parameters
- `POST /billing/create-portal-session` - 0 parameters
- `GET /billing/subscription-status` - 0 parameters
- `POST /billing/webhooks/stripe` - 1 parameter (Stripe event)
- Average: 0.3 parameters per endpoint

### Content Moderation (6 endpoints)
- `POST /moderation/report` - 4 parameters (message_id, report_reason, report_description, context_data)
- `GET /moderation/my-reports` - 3 parameters (status, limit, offset)
- `GET /moderation/admin/queue` - 5 parameters (status, priority, reason, limit, offset)
- `POST /moderation/admin/{report_id}/review` - 3 parameters (report_id, action, review_notes)
- `GET /moderation/admin/stats` - 0 parameters
- Average: 3.0 parameters per endpoint

### Admin Management (15 endpoints)
- Various endpoints with 0-8 parameters each
- User management, statistics, audit logs, system health
- Average: 2.1 parameters per endpoint

### Quota Management (2 endpoints)
- `GET /quota/status` - 0 parameters
- `GET /quota/history` - 1 parameter (limit)
- Average: 0.5 parameters per endpoint

## Overall Statistics
- **Total Parameters Across All Endpoints**: ~250+
- **Average Parameters per Endpoint**: 1.7
- **Most Complex Endpoint**: `POST /moderation/admin/queue` (5 parameters)
- **Simplest Endpoints**: Multiple GET endpoints with 0 parameters

## Complete API Endpoint Overview

| Category | Method | Endpoint | Parameters | Auth Required | Description |
|-----------|--------|----------|------------|---------------|-------------|
| **Authentication** | POST | `/auth/register` | 3 | No | User registration |
| | POST | `/auth/login` | 2 | No | User login |
| | GET | `/auth/me` | 0 | Yes | Get current user info |
| **User Management** | POST | `/user/onboarding` | 3 | Yes | User onboarding flow |
| | GET | `/user/onboarding/status` | 0 | Yes | Get onboarding status |
| | POST | `/user/preferences` | 1 | Yes | Update user preferences |
| | GET | `/user/preferences` | 0 | Yes | Get user preferences |
| | GET | `/system/info` | 0 | No | Get system information |
| **Health & Monitoring** | GET | `/health/` | 0 | No | Basic health check |
| | GET | `/health/detailed` | 0 | Yes | Detailed health (admin) |
| | GET | `/health/performance` | 0 | Yes | Performance metrics (admin) |
| **Chat & Conversation** | POST | `/llm/chat` | 5 | Yes | Advanced LLM chat |
| | POST | `/chat` | 2 | Yes | Simple chat |
| | GET | `/conversation/sessions` | 2 | Yes | List conversation sessions |
| | POST | `/conversation/sessions` | 2 | Yes | Create conversation |
| | GET | `/conversation/sessions/{id}` | 1 | Yes | Get conversation detail |
| | POST | `/conversation/sessions/{id}/messages` | 2 | Yes | Add message |
| | DELETE | `/conversation/sessions/{id}` | 1 | Yes | Delete conversation |
| | GET | `/conversation/memory/summary` | 0 | Yes | Conversation memory summary |
| **Research Workflows** | POST | `/research` | 6 | Yes | Start research workflow |
| | GET | `/research/{session_id}` | 1 | No | Get research report |
| | GET | `/research/stream/{session_id}` | 1 | No | Stream research progress |
| **Document & RAG** | POST | `/rag/upload-document` | 1 | Yes | Upload document |
| | GET | `/rag/document/{job_id}` | 1 | Yes | Get document status |
| | GET | `/rag/documents` | 2 | Yes | List user documents |
| | DELETE | `/rag/document/{job_id}` | 1 | Yes | Delete document |
| | POST | `/rag/document/{job_id}/retry` | 1 | Yes | Retry document processing |
| | GET | `/rag/search` | 4 | Yes | Search documents |
| | GET | `/rag/knowledge-bases` | 0 | Yes | List knowledge bases |
| | POST | `/rag/knowledge-bases` | 2 | Yes | Create knowledge base |
| | DELETE | `/rag/knowledge-bases/{name}` | 1 | Yes | Delete knowledge base |
| | POST | `/rag/knowledge-bases/{name}/upload` | 1 | Yes | Upload to knowledge base |
| | POST | `/rag/knowledge-bases/{name}/search` | 2 | Yes | Search knowledge base |
| **File Management** | POST | `/files/upload` | 1 | Yes | Upload file |
| | GET | `/files/{file_id}/status` | 1 | Yes | Get file status |
| | GET | `/files/list` | 2 | Yes | List user files |
| | DELETE | `/files/{file_id}` | 1 | Yes | Delete file |
| **OCR Services** | POST | `/ocr/recognize` | 1 | Yes | OCR recognition |
| | GET | `/ocr/status` | 0 | Yes | OCR service status |
| | POST | `/ocr/batch` | 1 | Yes | Batch OCR processing |
| **Search Services** | GET | `/search/providers` | 0 | Yes | Get search providers |
| | POST | `/search/providers/set` | 1 | Yes | Set search provider |
| | POST | `/search/` | 4 | Yes | Web search |
| | GET | `/search/test/{provider}` | 1 | Yes | Test search provider |
| **Evidence Chain** | GET | `/evidence/conversation/{id}` | 3 | Yes | Get conversation evidence |
| | GET | `/evidence/research/{session_id}` | 3 | Yes | Get research evidence |
| | PUT | `/evidence/evidence/{id}/mark_used` | 2 | Yes | Mark evidence used |
| | GET | `/evidence/stats` | 1 | Yes | Get evidence statistics |
| **Billing & Subscription** | POST | `/billing/create-checkout-session` | 0 | Yes | Create checkout session |
| | POST | `/billing/create-portal-session` | 0 | Yes | Create portal session |
| | GET | `/billing/subscription-status` | 0 | Yes | Get subscription status |
| | POST | `/billing/webhooks/stripe` | 1 | No | Stripe webhook handler |
| **Content Moderation** | POST | `/moderation/report` | 4 | Yes | Report content |
| | GET | `/moderation/my-reports` | 3 | Yes | Get my reports |
| | GET | `/moderation/admin/queue` | 5 | Yes | Get moderation queue (admin) |
| | POST | `/moderation/admin/{id}/review` | 3 | Yes | Review report (admin) |
| | GET | `/moderation/admin/stats` | 0 | Yes | Get moderation stats (admin) |
| **Quota Management** | GET | `/quota/status` | 0 | Yes | Get quota status |
| | GET | `/quota/history` | 1 | Yes | Get usage history |
| **Admin Management** | GET | `/admin/users` | 5 | Yes | List users (admin) |
| | GET | `/admin/users/{user_id}` | 1 | Yes | Get user detail (admin) |
| | PATCH | `/admin/users/{user_id}` | 2 | Yes | Update user (admin) |
| | POST | `/admin/users/{user_id}/toggle-active` | 1 | Yes | Toggle user active (admin) |
| | GET | `/admin/stats/users` | 0 | Yes | Get user statistics (admin) |
| | GET | `/admin/users/{user_id}/conversations` | 2 | Yes | Get user conversations (admin) |
| | GET | `/admin/users/{user_id}/api-usage` | 2 | Yes | Get user API usage (admin) |
| | GET | `/admin/users/{user_id}/documents` | 2 | Yes | Get user documents (admin) |
| | GET | `/admin/research-reports` | 2 | Yes | Get all research reports (admin) |
| | GET | `/admin/research-reports/{doc_id}` | 1 | Yes | Get research report detail (admin) |
| | GET | `/admin/subscriptions` | 3 | Yes | Get all subscriptions (admin) |
| | PATCH | `/admin/subscriptions/{sub_id}` | 1 | Yes | Update subscription (admin) |
| | GET | `/admin/audit-logs` | 7 | Yes | Get audit logs (admin) |
| | GET | `/admin/audit-logs/summary` | 0 | Yes | Get audit log summary (admin) |
| | GET | `/admin/health` | 0 | Yes | System health check (admin) |

## Key Statistics Summary

- **Total Endpoints**: 82 endpoints
- **Endpoints Requiring Authentication**: 73 (89%)
- **Admin-Only Endpoints**: 17 (21%)
- **File Upload Endpoints**: 4
- **Streaming Endpoints**: 1 (research progress)
- **Webhook Endpoints**: 1 (Stripe)
- **Average Parameters**: 1.7 per endpoint
- **Most Parameter-Rich Category**: Admin Management (average 2.1 parameters)
- **Simplest Category**: Billing (average 0.3 parameters)

## Feature Overview

### Core Capabilities
- **Multi-Agent Research**: Automated research workflows with multiple AI agents
- **Document Processing**: PDF, DOCX, TXT, MD file processing with OCR
- **Semantic Search**: Advanced RAG (Retrieval-Augmented Generation) search
- **Real-time Chat**: LLM-powered conversations with session management
- **Knowledge Bases**: Personal knowledge base creation and management
- **Content Moderation**: User-reported content review system
- **Billing Integration**: Stripe-based subscription management
- **Admin Dashboard**: Comprehensive user and system management

### Supported File Formats
- **Documents**: PDF, DOCX, DOC, TXT, MD, RTF
- **Images**: JPG, JPEG, PNG, BMP, TIFF (for OCR)
- **Presentations**: PPT, PPTX
- **Data**: JSON, CSV

## Authentication

### OAuth2 Password Flow

The platform uses OAuth2 with JWT tokens for authentication.

**Token Endpoint:** `POST /api/auth/login`

**Authorization Header:**
```
Authorization: Bearer <jwt_token>
```

### Token Types

- **Access Token**: JWT token for API access
- **Token Type**: "bearer"
- **Expiration**: Configurable (default 24 hours)

### Required Authentication

Most endpoints require authentication. Protected endpoints are marked with 🔒 in the documentation.

## Common Response Formats

### Success Response
```json
{
  "error": false,
  "message": "Operation successful",
  "data": { ... },
  "request_id": "optional_request_id"
}
```

### Error Response
```json
{
  "error": true,
  "code": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": { ... },
  "request_id": "optional_request_id"
}
```

### Pagination Response
```json
{
  "data": [...],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "has_next": true,
  "has_prev": false
}
```

## Error Handling

### HTTP Status Codes

| Code | Description | Example Scenarios |
|------|-------------|------------------|
| 200 | Success | Request completed successfully |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid input data, validation errors |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Resource already exists or operation conflicts |
| 413 | Payload Too Large | File size exceeds limits |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Input validation failed |
| `UNAUTHORIZED` | Authentication required |
| `FORBIDDEN` | Insufficient permissions |
| `NOT_FOUND` | Resource not found |
| `RATE_LIMITED` | Rate limit exceeded |
| `QUOTA_EXCEEDED` | User quota exceeded |
| `FILE_UPLOAD_ERROR` | File upload failed |
| `DATABASE_ERROR` | Database operation failed |
| `BUSINESS_LOGIC_ERROR` | Business rule violation |

## API Endpoints

### Authentication Endpoints

#### Register User
```http
POST /api/auth/register
```

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**Response (201):**
```json
{
  "access_token": "jwt_token",
  "token_type": "bearer",
  "user_id": 123,
  "username": "john_doe",
  "email": "john@example.com",
  "role": "free"
}
```

**Validation Rules:**
- `username`: 3-30 characters, alphanumeric + underscores
- `email`: Valid email format
- `password`: Minimum 8 characters, must contain uppercase, lowercase, and number

#### Login
```http
POST /api/auth/login
```

**Request Body (form-data):**
```
username: string
password: string
```

**Response (200):**
```json
{
  "access_token": "jwt_token",
  "token_type": "bearer"
}
```

#### Get Current User
```http
GET /api/auth/me
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": 123,
  "username": "john_doe",
  "email": "john@example.com",
  "role": "subscribed"
}
```

### User Management Endpoints

#### User Onboarding
```http
POST /api/user/onboarding
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "action": "start|complete|skip",
  "step": "optional_step_name",
  "data": { "key": "value" }
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Onboarding step completed",
  "next_step": "preferences_setup",
  "progress": { "completed": 2, "total": 5 }
}
```

#### Get User Preferences
```http
GET /api/user/preferences
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "theme": "dark",
  "language": "en",
  "notifications": {
    "email": true,
    "push": false
  },
  "research_settings": {
    "default_depth": "medium",
    "auto_citations": true
  }
}
```

#### Update User Preferences
```http
POST /api/user/preferences
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "preferences": {
    "theme": "light",
    "language": "zh",
    "notifications": {
      "email": false,
      "push": true
    }
  }
}
```

#### Get System Info
```http
GET /api/system/info
```

**Response (200):**
```json
{
  "platform_name": "Deep Research Platform",
  "version": "1.0.0",
  "features": [
    "multi_agent_research",
    "document_processing",
    "semantic_search",
    "real_time_chat"
  ],
  "limits": {
    "free_users": {
      "max_documents": 10,
      "max_research_per_day": 3
    },
    "subscribed_users": {
      "max_documents": 1000,
      "max_research_per_day": 50
    }
  }
}
```

### Health & Monitoring Endpoints

#### Basic Health Check
```http
GET /api/health/
```

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "uptime": 86400,
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "llm_providers": {
      "openai": "healthy",
      "anthropic": "healthy",
      "doubao": "degraded"
    }
  }
}
```

#### Detailed Health Check 🔒
```http
GET /api/health/detailed
Authorization: Bearer <token>
```

**Requirements:** Admin role

**Response (200):**
```json
{
  "status": "healthy",
  "database_stats": {
    "documents": 15420,
    "chunks": 487320,
    "embeddings": 487320,
    "evidence_records": 8934
  },
  "queue_stats": {
    "pending_tasks": 12,
    "processing_tasks": 3,
    "failed_tasks": 0
  },
  "routing_stats": {
    "total_requests": 12543,
    "avg_response_time": 1.2,
    "success_rate": 98.7
  }
}
```

#### Performance Metrics 🔒
```http
GET /api/health/performance
Authorization: Bearer <token>
```

**Requirements:** Admin role

**Response (200):**
```json
{
  "system_metrics": {
    "cpu_usage": 45.2,
    "memory_usage": 68.7,
    "disk_usage": 23.1
  },
  "api_metrics": {
    "requests_per_minute": 120,
    "avg_response_time": 850,
    "error_rate": 1.2
  },
  "database_metrics": {
    "connection_pool": {
      "active": 15,
      "idle": 25,
      "total": 40
    },
    "query_performance": {
      "avg_query_time": 45,
      "slow_queries": 2
    }
  }
}
```

### Chat & Conversation Endpoints

#### LLM Chat 🔒
```http
POST /api/llm/chat
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "messages": [
    {
      "role": "system|user|assistant",
      "content": "string"
    }
  ],
  "task": "general|research|analysis",
  "size": "small|medium|large",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Response (200):**
```json
{
  "model": "gpt-4",
  "content": "AI response content",
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 300,
    "total_tokens": 450
  }
}
```

#### Simple Chat 🔒
```http
POST /api/chat
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "message": "What is quantum computing?",
  "session_id": "optional_session_id"
}
```

**Response (200):**
```json
{
  "model": "gpt-4",
  "content": "Quantum computing is a revolutionary computing paradigm...",
  "session_id": "session_12345"
}
```

#### Get Conversation Sessions 🔒
```http
GET /api/conversation/sessions?page=1&page_size=20
Authorization: Bearer <token>
```

**Response (200):**
```json
[
  {
    "id": "session_123",
    "title": "Quantum Computing Research",
    "user_id": "user_456",
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T11:30:00Z",
    "message_count": 15,
    "last_message": "Thank you for the explanation!"
  }
]
```

#### Create Conversation Session 🔒
```http
POST /api/conversation/sessions
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "title": "New Research Topic",
  "initial_message": "I want to learn about artificial intelligence"
}
```

**Response (201):**
```json
{
  "id": "session_789",
  "title": "New Research Topic",
  "user_id": "user_456",
  "created_at": "2024-01-15T12:00:00Z",
  "updated_at": "2024-01-15T12:00:00Z",
  "message_count": 1,
  "last_message": "I want to learn about artificial intelligence"
}
```

#### Get Conversation Detail 🔒
```http
GET /api/conversation/sessions/{session_id}
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": "session_123",
  "title": "Quantum Computing Research",
  "user_id": "user_456",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T11:30:00Z",
  "messages": [
    {
      "role": "user",
      "content": "What is quantum computing?",
      "timestamp": "2024-01-15T10:00:00Z"
    },
    {
      "role": "assistant",
      "content": "Quantum computing is a revolutionary computing paradigm...",
      "timestamp": "2024-01-15T10:01:00Z"
    }
  ]
}
```

#### Add Message to Conversation 🔒
```http
POST /api/conversation/sessions/{session_id}/messages
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "role": "user|assistant|system",
  "content": "Can you explain more about qubits?"
}
```

**Response (200):**
```json
{
  "message": "Message added successfully",
  "session_id": "session_123",
  "message_id": "msg_456"
}
```

#### Get Conversation Memory Summary 🔒
```http
GET /api/conversation/memory/summary
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "user_id": "user_456",
  "total_conversations": 25,
  "total_messages": 340,
  "favorite_topics": [
    "quantum computing",
    "artificial intelligence",
    "machine learning"
  ],
  "conversation_style": "professional and detailed",
  "last_active": "2024-01-15T11:30:00Z"
}
```

### Research Endpoints

#### Start Research 🔒
```http
POST /api/research
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "query": "The impact of artificial intelligence on healthcare",
  "session_id": "optional_session_id",
  "depth": "basic|intermediate|comprehensive",
  "sources": ["academic", "news", "technical"],
  "language": "en|zh|es"
}
```

**Response (200):**
```json
{
  "session_id": "research_789",
  "status": "completed|failed|error",
  "documents_found": 45,
  "iterations": 3,
  "error": null
}
```

#### Get Research Report
```http
GET /api/research/{session_id}
```

**Response (200):**
```markdown
# Research Report: The Impact of AI on Healthcare

## Executive Summary
Artificial intelligence is revolutionizing healthcare through...

## Key Findings
1. **Diagnostic Accuracy**: AI algorithms have shown...
2. **Drug Discovery**: Machine learning models accelerate...
3. **Personalized Medicine**: AI enables...

## Sources
- [1] Smith et al. (2023). "AI in Medical Imaging..."
- [2] Johnson & Lee (2024). "Machine Learning for Drug Discovery..."
```

#### Stream Research Progress
```http
GET /api/research/stream/{session_id}
```

**Response (Server-Sent Events):**
```
data: {"phase":"planning","message":"Generating research plan..."}

data: {"phase":"collecting","message":"Retrieving and collecting sources..."}

data: {"phase":"synthesizing","message":"Writing report..."}

data: {"status":"completed"}
```

### Document & RAG Endpoints

#### Upload Document for RAG 🔒
```http
POST /api/rag/upload-document
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form Data:**
- `file`: Document file (PDF, DOCX, TXT, MD)

**Response (201):**
```json
{
  "job_id": "job_123",
  "status": "pending",
  "message": "Document uploaded successfully, processing in background"
}
```

**File Limits:**
- Maximum file size: 50MB
- Supported formats: .pdf, .docx, .doc, .txt, .md

#### Get Document Status 🔒
```http
GET /api/rag/document/{job_id}
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "job_id": "job_123",
  "status": "completed|processing|failed",
  "filename": "research_paper.pdf",
  "created_at": "2024-01-15T10:00:00Z",
  "started_at": "2024-01-15T10:01:00Z",
  "completed_at": "2024-01-15T10:05:00Z",
  "error_message": null,
  "result": {
    "chunks_created": 25,
    "embeddings_generated": 25,
    "extracted_text_length": 15000
  }
}
```

#### List User Documents 🔒
```http
GET /api/rag/documents?page=1&page_size=20
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "documents": [
    {
      "job_id": "job_123",
      "filename": "research_paper.pdf",
      "status": "completed",
      "created_at": "2024-01-15T10:00:00Z",
      "progress": 100,
      "error_message": null
    }
  ],
  "total": 15
}
```

#### Delete Document 🔒
```http
DELETE /api/rag/document/{job_id}
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "message": "Document deleted successfully"
}
```

#### Retry Document Processing 🔒
```http
POST /api/rag/document/{job_id}/retry
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "message": "Document reprocessing started"
}
```

#### Search Documents 🔒
```http
GET /api/rag/search?query=artificial intelligence&limit=10&score_threshold=0.5&use_reranking=true
Authorization: Bearer <token>
```

**Query Parameters:**
- `query`: Search query (required)
- `limit`: Maximum results (default: 10, max: 50)
- `score_threshold`: Minimum relevance score (default: 0.0)
- `use_reranking`: Enable two-stage reranking (default: true)

**Response (200):**
```json
{
  "query": "artificial intelligence",
  "results": [
    {
      "chunk_id": "chunk_123",
      "document_id": "doc_456",
      "content": "Artificial intelligence is transforming healthcare by...",
      "score": 0.89,
      "recall_score": 0.75,
      "rerank_score": 0.92,
      "source_url": "https://example.com/paper.pdf",
      "filename": "healthcare_ai_research.pdf",
      "snippet": "Artificial intelligence is transforming healthcare by...",
      "citation_id": "cite_789",
      "metadata": {
        "page": 15,
        "section": "Introduction"
      }
    }
  ],
  "total": 8,
  "search_method": "two_stage_reranking",
  "message": "Two-stage retrieval completed (recalled 50 candidates, reranked to 8)"
}
```

#### Knowledge Base Management 🔒

##### List Knowledge Bases
```http
GET /api/rag/knowledge-bases
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "knowledge_bases": [
    {
      "name": "medical_research",
      "description": "Medical research papers and articles",
      "created_at": "2024-01-10T10:00:00Z",
      "file_count": 25
    }
  ],
  "total": 1
}
```

##### Create Knowledge Base
```http
POST /api/rag/knowledge-bases
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "name": "ai_research",
  "description": "AI research papers and documentation"
}
```

**Validation:**
- Name: 3-20 characters, alphanumeric only
- Maximum 10 knowledge bases per user

##### Delete Knowledge Base
```http
DELETE /api/rag/knowledge-bases/{kb_name}
Authorization: Bearer <token>
```

##### Upload File to Knowledge Base
```http
POST /api/rag/knowledge-bases/{kb_name}/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form Data:**
- `file`: Document file

##### Search Knowledge Base
```http
POST /api/rag/knowledge-bases/{kb_name}/search
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "query": "machine learning algorithms",
  "top_k": 5
}
```

### File Upload Endpoints

#### Upload File 🔒
```http
POST /api/files/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form Data:**
- `file`: File to upload

**Supported Formats:**
- PDF, PPT, PPTX, DOC, DOCX, TXT, MD

**Response (201):**
```json
{
  "file_id": "file_123",
  "filename": "document.pdf",
  "file_path": "/uploads/user_456/file_123.pdf",
  "file_size": 2048576,
  "file_type": ".pdf",
  "status": "pending",
  "message": "File uploaded successfully, processing in background"
}
```

#### Get File Status 🔒
```http
GET /api/files/{file_id}/status
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "file_id": "file_123",
  "status": "completed",
  "extracted_text": "Extracted text content from the document...",
  "error": null
}
```

#### List User Files 🔒
```http
GET /api/files/list?skip=0&limit=50
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "total": 15,
  "files": [
    {
      "file_id": "file_123",
      "filename": "research_paper.pdf",
      "status": "completed",
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:05:00Z",
      "progress": 100,
      "error_message": null
    }
  ]
}
```

#### Delete File 🔒
```http
DELETE /api/files/{file_id}
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "message": "File deleted successfully"
}
```

### OCR Endpoints

#### Recognize Document 🔒
```http
POST /api/ocr/recognize
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form Data:**
- `file`: Document file (PDF, PPT, PPTX, DOC, DOCX, JPG, PNG)

**Response (200):**
```json
{
  "success": true,
  "text": "Extracted text content from the document...",
  "file_type": ".pdf",
  "pages": 15,
  "error": null
}
```

#### Get OCR Status 🔒
```http
GET /api/ocr/status
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "available": true,
  "provider": "doubao",
  "model": "ocr-general-v1.0",
  "supported_formats": [".pdf", ".ppt", ".pptx", ".doc", ".docx", ".jpg", ".jpeg", ".png", ".bmp"]
}
```

#### Batch Recognize 🔒
```http
POST /api/ocr/batch
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form Data:**
- `files`: Multiple document files

**Response (200):**
```json
{
  "success": true,
  "total": 3,
  "results": [
    {
      "filename": "document1.pdf",
      "success": true,
      "text": "Extracted text from document 1...",
      "error": null
    },
    {
      "filename": "document2.jpg",
      "success": false,
      "text": "",
      "error": "Unsupported image format"
    }
  ]
}
```

### Search Endpoints

#### Get Search Providers 🔒
```http
GET /api/search/providers
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "current_provider": "doubao",
  "available_providers": {
    "doubao": {
      "name": "Doubao Search",
      "description": "ByteDance's search engine",
      "status": "available"
    },
    "kimi": {
      "name": "Kimi Search",
      "description": "Moonshot AI's search engine",
      "status": "available"
    }
  }
}
```

#### Set Search Provider 🔒
```http
POST /api/search/providers/set
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "provider": "doubao|kimi"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Search provider switched to: doubao",
  "current_provider": "doubao"
}
```

#### Web Search 🔒
```http
POST /api/search/
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "query": "latest developments in quantum computing",
  "provider": "doubao|kimi|null",
  "system_prompt": "Focus on academic and technical sources",
  "search_limit": 10
}
```

**Response (200):**
```json
{
  "success": true,
  "query": "latest developments in quantum computing",
  "answer": "Recent developments in quantum computing include breakthroughs in...",
  "search_results": [
    {
      "title": "Quantum Computing Breakthrough 2024",
      "url": "https://example.com/quantum-breakthrough",
      "snippet": "Scientists achieve new milestone in quantum computing...",
      "relevance_score": 0.95
    }
  ],
  "sources": [
    {
      "title": "Nature Quantum Information",
      "url": "https://nature.com/quantum",
      "type": "academic_journal"
    }
  ],
  "provider": "doubao",
  "error": null
}
```

#### Test Search Provider 🔒
```http
GET /api/search/test/{provider}
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "provider": "doubao",
  "status": "available",
  "response_time": 1.2,
  "test_query": "quantum computing",
  "test_results": {
    "success": true,
    "result_count": 10
  }
}
```

### Evidence Chain Endpoints

#### Get Conversation Evidence 🔒
```http
GET /api/evidence/conversation/{conversation_id}?limit=50&offset=0
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "conversation_id": "conv_123",
  "research_session_id": null,
  "total_evidence": 15,
  "evidence_by_type": {
    "academic_paper": 8,
    "news_article": 4,
    "technical_document": 3
  },
  "evidence_list": [
    {
      "id": 123,
      "source_type": "academic_paper",
      "source_url": "https://arxiv.org/abs/2024.01234",
      "source_title": "Quantum Computing: A Comprehensive Survey",
      "content": "Quantum computing represents a fundamental shift...",
      "snippet": "Quantum computing represents a fundamental shift in computation...",
      "relevance_score": 0.92,
      "confidence_score": 0.88,
      "citation_text": "Smith et al. (2024). Quantum Computing: A Comprehensive Survey.",
      "used_in_response": true,
      "metadata": {
        "authors": ["John Smith", "Jane Doe"],
        "journal": "Nature Quantum Information",
        "year": 2024
      },
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Get Research Evidence 🔒
```http
GET /api/evidence/research/{research_session_id}?limit=50&offset=0
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "conversation_id": null,
  "research_session_id": "research_456",
  "total_evidence": 25,
  "evidence_by_type": {
    "academic_paper": 15,
    "news_article": 6,
    "technical_document": 4
  },
  "evidence_list": [...]
}
```

#### Mark Evidence Used 🔒
```http
PUT /api/evidence/evidence/{evidence_id}/mark_used?used=true
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "message": "Evidence usage status updated to: true"
}
```

#### Get Evidence Statistics 🔒
```http
GET /api/evidence/stats?days=7
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "period_days": 7,
  "total_evidence": 150,
  "used_evidence": 120,
  "usage_rate": 80.0,
  "avg_relevance_score": 0.85,
  "evidence_by_type": {
    "academic_paper": 80,
    "news_article": 40,
    "technical_document": 30
  }
}
```

### Billing & Subscription Endpoints

#### Create Checkout Session 🔒
```http
POST /api/billing/create-checkout-session
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "url": "https://checkout.stripe.com/pay/cs_test_123456"
}
```

#### Create Customer Portal Session 🔒
```http
POST /api/billing/create-portal-session
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "url": "https://billing.stripe.com/session/bps_123456"
}
```

#### Get Subscription Status 🔒
```http
GET /api/billing/subscription-status
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "has_active_subscription": true,
  "subscription_id": "sub_123456",
  "status": "active",
  "current_period_end": "2024-02-15T10:00:00Z",
  "plan_name": "Deep Research Pro"
}
```

#### Stripe Webhook
```http
POST /api/billing/webhooks/stripe
Stripe-Signature: <signature>
```

**Handled Events:**
- `checkout.session.completed`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_failed`
- `invoice.payment_succeeded`

**Response (200):**
```json
{
  "status": "success"
}
```

### Moderation Endpoints

#### Report Content 🔒
```http
POST /api/moderation/report
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "message_id": "msg_123456",
  "report_reason": "spam|harassment|violence|inappropriate_content|misinformation|other",
  "report_description": "Optional detailed description",
  "context_data": {
    "additional_info": "value"
  }
}
```

**Response (201):**
```json
{
  "id": 789,
  "message_id": "msg_123456",
  "reporter_user_id": "user_456",
  "reported_user_id": "user_789",
  "report_reason": "spam",
  "report_description": "This message appears to be spam",
  "status": "pending",
  "priority": "low",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Get My Reports 🔒
```http
GET /api/moderation/my-reports?status=pending&limit=20&offset=0
Authorization: Bearer <token>
```

**Response (200):**
```json
[
  {
    "id": 789,
    "message_id": "msg_123456",
    "report_reason": "spam",
    "status": "pending",
    "created_at": "2024-01-15T10:30:00Z",
    "message_content": "This is the reported message content...",
    "session_title": "Conversation Title"
  }
]
```

#### Get Moderation Queue 🔒
```http
GET /api/moderation/admin/queue?status=pending&priority=high&limit=50&offset=0
Authorization: Bearer <token>
```

**Requirements:** Admin role

**Response (200):**
```json
[
  {
    "id": 789,
    "message_id": "msg_123456",
    "reporter_user_id": "user_456",
    "reporter_username": "john_doe",
    "reported_user_id": "user_789",
    "reported_username": "jane_smith",
    "report_reason": "spam",
    "status": "pending",
    "priority": "low",
    "created_at": "2024-01-15T10:30:00Z",
    "message_content": "Reported message content...",
    "session_title": "Conversation Title"
  }
]
```

#### Review Report 🔒
```http
POST /api/moderation/admin/{report_id}/review
Authorization: Bearer <token>
```

**Requirements:** Admin role

**Request Body:**
```json
{
  "action": "warning|message_deleted|user_suspended|user_banned|dismiss",
  "review_notes": "Optional review notes",
  "priority_change": "low|medium|high|urgent"
}
```

**Response (200):**
```json
{
  "id": 789,
  "status": "resolved",
  "reviewer_admin_id": "admin_123",
  "reviewer_admin_username": "admin_user",
  "action_taken": "warning",
  "review_notes": "User warned about spam content",
  "reviewed_at": "2024-01-15T11:00:00Z",
  "resolved_at": "2024-01-15T11:00:00Z"
}
```

#### Get Moderation Statistics 🔒
```http
GET /api/moderation/admin/stats
Authorization: Bearer <token>
```

**Requirements:** Admin role

**Response (200):**
```json
{
  "total_reports": 150,
  "pending_reports": 12,
  "reviewing_reports": 5,
  "resolved_reports": 120,
  "dismissed_reports": 13,
  "reports_by_reason": {
    "spam": 60,
    "harassment": 25,
    "inappropriate_content": 30,
    "misinformation": 20,
    "other": 15
  },
  "reports_by_priority": {
    "low": 80,
    "medium": 50,
    "high": 18,
    "urgent": 2
  },
  "recent_reports": [...]
}
```

### Admin Management Endpoints

All admin endpoints require admin role authentication.

#### List Users
```http
GET /api/admin/users?skip=0&limit=100&role=free&is_active=true&search=john
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default: 100, max: 1000)
- `role`: Filter by role (free, subscribed, admin)
- `is_active`: Filter by active status
- `search`: Search username or email

**Response (200):**
```json
[
  {
    "id": "user_123",
    "username": "john_doe",
    "email": "john@example.com",
    "role": "subscribed",
    "is_active": true,
    "created_at": "2024-01-01T10:00:00Z"
  }
]
```

#### Get User Detail
```http
GET /api/admin/users/{user_id}
Authorization: Bearer <admin_token>
```

**Response (200):**
```json
{
  "id": "user_123",
  "username": "john_doe",
  "email": "john@example.com",
  "role": "subscribed",
  "is_active": true,
  "created_at": "2024-01-01T10:00:00Z",
  "stripe_customer_id": "cus_123456"
}
```

#### Update User
```http
PATCH /api/admin/users/{user_id}
Authorization: Bearer <admin_token>
```

**Request Body:**
```json
{
  "is_active": true,
  "role": "subscribed"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "User information updated",
  "user": {
    "id": "user_123",
    "username": "john_doe",
    "email": "john@example.com",
    "role": "subscribed",
    "is_active": true,
    "created_at": "2024-01-01T10:00:00Z"
  }
}
```

#### Toggle User Active Status
```http
POST /api/admin/users/{user_id}/toggle-active
Authorization: Bearer <admin_token>
```

**Response (200):**
```json
{
  "success": true,
  "message": "User banned",
  "is_active": false
}
```

#### Get User Statistics
```http
GET /api/admin/stats/users
Authorization: Bearer <admin_token>
```

**Response (200):**
```json
{
  "total_users": 1250,
  "active_users": 1180,
  "admin_users": 5,
  "subscribed_users": 180,
  "free_users": 1070
}
```

#### Get User Conversations
```http
GET /api/admin/users/{user_id}/conversations?skip=0&limit=50
Authorization: Bearer <admin_token>
```

**Response (200):**
```json
{
  "user_id": "user_123",
  "username": "john_doe",
  "total_sessions": 25,
  "sessions": [
    {
      "id": "session_456",
      "title": "Quantum Computing Research",
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T11:30:00Z",
      "message_count": 15
    }
  ]
}
```

#### Get User API Usage
```http
GET /api/admin/users/{user_id}/api-usage?skip=0&limit=100
Authorization: Bearer <admin_token>
```

**Response (200):**
```json
[
  {
    "id": 12345,
    "user_id": "user_123",
    "endpoint_called": "/api/llm/chat",
    "timestamp": "2024-01-15T10:30:00Z",
    "extra": "{\"model\": \"gpt-4\", \"tokens\": 150}"
  }
]
```

#### Get User Documents
```http
GET /api/admin/users/{user_id}/documents?skip=0&limit=50
Authorization: Bearer <admin_token>
```

**Response (200):**
```json
{
  "user_id": "user_123",
  "username": "john_doe",
  "total_jobs": 15,
  "jobs": [
    {
      "id": "job_456",
      "filename": "research_paper.pdf",
      "status": "completed",
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

#### Get All Research Reports
```http
GET /api/admin/research-reports?skip=0&limit=50
Authorization: Bearer <admin_token>
```

**Response (200):**
```json
{
  "total_documents": 500,
  "documents": [
    {
      "document_id": "doc_123",
      "chunks": [
        {
          "id": "chunk_456",
          "content": "Research introduction content...",
          "chunk_index": 0
        }
      ],
      "total_chunks": 25,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

#### Get Research Report Detail
```http
GET /api/admin/research-reports/{document_id}
Authorization: Bearer <admin_token>
```

**Response (200):**
```json
{
  "document_id": "doc_123",
  "total_chunks": 25,
  "content": "Full research report content...",
  "chunks": [
    {
      "id": "chunk_456",
      "chunk_index": 0,
      "content": "Chunk content...",
      "metadata": {
        "section": "introduction"
      }
    }
  ],
  "created_at": "2024-01-15T10:00:00Z"
}
```

#### Get All Subscriptions
```http
GET /api/admin/subscriptions?skip=0&limit=100&status=active
Authorization: Bearer <admin_token>
```

**Response (200):**
```json
{
  "total": 180,
  "subscriptions": [
    {
      "id": "sub_123",
      "user_id": "user_456",
      "username": "john_doe",
      "email": "john@example.com",
      "status": "active",
      "plan_name": "Deep Research Pro",
      "created_at": "2024-01-01T10:00:00Z",
      "current_period_end": "2024-02-01T10:00:00Z"
    }
  ]
}
```

#### Update Subscription
```http
PATCH /api/admin/subscriptions/{subscription_id}
Authorization: Bearer <admin_token>
```

**Request Body:**
```json
{
  "status": "cancelled"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Subscription status updated",
  "subscription": {
    "id": "sub_123",
    "status": "cancelled"
  }
}
```

#### Get Audit Logs
```http
GET /api/admin/audit-logs?admin_user_id=admin_123&action=user_update&page=1&page_size=50
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `admin_user_id`: Filter by admin user ID
- `action`: Filter by action type
- `target_user_id`: Filter by target user ID
- `status`: Filter by status
- `start_date`: Filter by start date
- `end_date`: Filter by end date
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 50, max: 200)

**Response (200):**
```json
{
  "logs": [
    {
      "id": 789,
      "admin_user_id": "admin_123",
      "admin_username": "admin_user",
      "action": "user_update",
      "target_user_id": "user_456",
      "target_username": "john_doe",
      "timestamp": "2024-01-15T11:00:00Z",
      "details": {
        "old_role": "free",
        "new_role": "subscribed"
      },
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "endpoint": "PATCH /admin/users/user_456",
      "status": "success",
      "error_message": null
    }
  ],
  "total": 1250,
  "page": 1,
  "page_size": 50
}
```

#### Get Audit Log Summary
```http
GET /api/admin/audit-logs/summary
Authorization: Bearer <admin_token>
```

**Response (200):**
```json
{
  "summary": {
    "total_operations_30_days": 2500,
    "active_admins_30_days": 5,
    "period_days": 30
  },
  "action_breakdown": [
    {"action": "user_view", "count": 800},
    {"action": "user_update", "count": 300},
    {"action": "user_ban", "count": 50}
  ],
  "status_breakdown": [
    {"status": "success", "count": 2400},
    {"status": "failed", "count": 100}
  ],
  "daily_operations": [
    {"date": "2024-01-15", "count": 85},
    {"date": "2024-01-14", "count": 92}
  ]
}
```

#### System Health Check
```http
GET /api/admin/health
Authorization: Bearer <admin_token>
```

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T12:00:00Z",
  "components": {
    "database": {
      "healthy": true,
      "response_time": 15,
      "connections": 25
    },
    "llm": {
      "healthy": true,
      "providers": {
        "openai": {"status": "healthy", "response_time": 1.2},
        "anthropic": {"status": "healthy", "response_time": 1.5},
        "doubao": {"status": "degraded", "response_time": 3.0}
      }
    },
    "ocr": {
      "available": true,
      "provider": "doubao",
      "response_time": 2.1
    }
  }
}
```

## Rate Limiting & Quotas

### Rate Limits

| Endpoint Type | Limit | Time Window |
|---------------|-------|-------------|
| Authentication | 5 requests | 15 minutes |
| Chat | 60 requests | 1 hour |
| Search | 30 requests | 1 hour |
| File Upload | 10 requests | 1 hour |
| Research | 5 requests | 1 hour |

### User Quotas

| Feature | Free Users | Subscribed Users |
|---------|------------|------------------|
| Documents | 10 | 1000 |
| Research Sessions | 3/day | 50/day |
| Chat Messages | 100/day | 1000/day |
| File Upload Size | 10MB | 50MB |
| Storage | 100MB | 10GB |

### Quota Headers

API responses include quota information in headers:
```
X-Quota-Limit: 1000
X-Quota-Remaining: 850
X-Quota-Reset: 1642694400
```

## SDK & Integration Examples

### Python Example

```python
import requests
import json

class DeepResearchAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def chat(self, message, session_id=None):
        """Send a chat message"""
        data = {
            "message": message,
            "session_id": session_id
        }
        response = requests.post(
            f"{self.base_url}/api/chat",
            headers=self.headers,
            json=data
        )
        return response.json()

    def start_research(self, query, session_id=None):
        """Start a research session"""
        data = {
            "query": query,
            "session_id": session_id
        }
        response = requests.post(
            f"{self.base_url}/api/research",
            headers=self.headers,
            json=data
        )
        return response.json()

    def upload_document(self, file_path):
        """Upload a document for processing"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{self.base_url}/api/files/upload",
                headers={"Authorization": f"Bearer {self.token}"},
                files=files
            )
        return response.json()

# Usage example
api = DeepResearchAPI("https://api.deepresearch.com/v1", "your_token_here")

# Chat
response = api.chat("What is quantum computing?")
print(response["content"])

# Research
research = api.start_research("The impact of AI on healthcare")
print(f"Research session ID: {research['session_id']}")

# Upload document
result = api.upload_document("research_paper.pdf")
print(f"Upload job ID: {result['file_id']}")
```

### JavaScript Example

```javascript
class DeepResearchAPI {
    constructor(baseUrl, token) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }

    async chat(message, sessionId = null) {
        const response = await fetch(`${this.baseUrl}/api/chat`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        });
        return await response.json();
    }

    async search(query, options = {}) {
        const response = await fetch(`${this.baseUrl}/api/search/`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                query: query,
                ...options
            })
        });
        return await response.json();
    }

    async uploadDocument(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${this.baseUrl}/api/files/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`
            },
            body: formData
        });
        return await response.json();
    }
}

// Usage example
const api = new DeepResearchAPI('https://api.deepresearch.com/v1', 'your_token_here');

// Chat
api.chat('What is quantum computing?')
    .then(response => console.log(response.content));

// Search
api.search('latest AI developments', { search_limit: 10 })
    .then(response => console.log(response.answer));

// Upload document
const fileInput = document.getElementById('file-input');
const file = fileInput.files[0];
api.uploadDocument(file)
    .then(response => console.log(`Upload job ID: ${response.file_id}`));
```

### cURL Examples

```bash
# Login
curl -X POST "https://api.deepresearch.com/v1/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_username&password=your_password"

# Chat
curl -X POST "https://api.deepresearch.com/v1/api/chat" \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is quantum computing?", "session_id": "optional_session"}'

# Upload document
curl -X POST "https://api.deepresearch.com/v1/api/files/upload" \
  -H "Authorization: Bearer your_token" \
  -F "file=@/path/to/document.pdf"

# Search
curl -X POST "https://api.deepresearch.com/v1/api/search/" \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{"query": "artificial intelligence in healthcare", "search_limit": 10}'

# Start research
curl -X POST "https://api.deepresearch.com/v1/api/research" \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{"query": "The impact of AI on healthcare"}'
```

## Support

For technical support and API questions:
- Email: support@deepresearch.com
- Documentation: https://docs.deepresearch.com
- Status Page: https://status.deepresearch.com

## Changelog

### v1.0.0 (2024-01-15)
- Initial API release
- Authentication endpoints
- Chat and conversation management
- Document processing and RAG
- Research workflows
- Search functionality
- Billing integration
- Admin management
- Content moderation

---

*This documentation is updated regularly. Last updated: January 15, 2024*