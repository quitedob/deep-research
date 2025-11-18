#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库表结构定义
定义所有表的创建语句和验证规则
"""

# 用户表
USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
"""

# 用户偏好设置表
USER_PREFERENCES_TABLE = """
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    default_llm_provider VARCHAR(50) DEFAULT 'deepseek',
    default_model VARCHAR(100),
    theme VARCHAR(50) DEFAULT 'light',
    language VARCHAR(10) DEFAULT 'zh',
    preferences JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);
"""

# 对话会话表
CHAT_SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS chat_sessions (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    llm_provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    system_prompt TEXT,
    status VARCHAR(50) DEFAULT 'active',
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_status ON chat_sessions(status);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at DESC);
"""

# 对话消息表
CHAT_MESSAGES_TABLE = """
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    model_name VARCHAR(100),
    tokens_used INTEGER,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);
"""

# 研究会话表
RESEARCH_SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS research_sessions (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255),
    title TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_research_sessions_user_id ON research_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_research_sessions_status ON research_sessions(status);
CREATE INDEX IF NOT EXISTS idx_research_sessions_created_at ON research_sessions(created_at);
"""

# 研究发现表
RESEARCH_FINDINGS_TABLE = """
CREATE TABLE IF NOT EXISTS research_findings (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    source_type VARCHAR(100) NOT NULL,
    source_url TEXT,
    content TEXT NOT NULL,
    relevance_score FLOAT DEFAULT 0.8,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES research_sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_research_findings_session_id ON research_findings(session_id);
CREATE INDEX IF NOT EXISTS idx_research_findings_source_type ON research_findings(source_type);
CREATE INDEX IF NOT EXISTS idx_research_findings_relevance_score ON research_findings(relevance_score);
"""

# 引用表
CITATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS research_citations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    authors TEXT[] NOT NULL,
    source_url TEXT NOT NULL,
    publication_year INTEGER,
    doi VARCHAR(255),
    citation_type VARCHAR(50) DEFAULT 'article',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES research_sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_research_citations_session_id ON research_citations(session_id);
CREATE INDEX IF NOT EXISTS idx_research_citations_citation_type ON research_citations(citation_type);
"""

# 长期记忆表
LONG_TERM_MEMORY_TABLE = """
CREATE TABLE IF NOT EXISTS research_memory (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    message_role VARCHAR(50) NOT NULL,
    message_name VARCHAR(255),
    message_content TEXT NOT NULL,
    timestamp VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES research_sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_research_memory_session_id ON research_memory(session_id);
CREATE INDEX IF NOT EXISTS idx_research_memory_timestamp ON research_memory(timestamp);
"""

# 所有表的定义
ALL_TABLES = {
    "users": USERS_TABLE,
    "user_preferences": USER_PREFERENCES_TABLE,
    "chat_sessions": CHAT_SESSIONS_TABLE,
    "chat_messages": CHAT_MESSAGES_TABLE,
    "research_sessions": RESEARCH_SESSIONS_TABLE,
    "research_findings": RESEARCH_FINDINGS_TABLE,
    "research_citations": CITATIONS_TABLE,
    "research_memory": LONG_TERM_MEMORY_TABLE,
}

# 表结构验证规则
TABLE_SCHEMAS = {
    "users": {
        "columns": {
            "id": "character varying",
            "username": "character varying",
            "email": "character varying",
            "password_hash": "character varying",
            "full_name": "character varying",
            "avatar_url": "text",
            "is_active": "boolean",
            "is_verified": "boolean",
            "created_at": "timestamp without time zone",
            "updated_at": "timestamp without time zone",
            "last_login_at": "timestamp without time zone",
        }
    },
    "user_preferences": {
        "columns": {
            "id": "integer",
            "user_id": "character varying",
            "default_llm_provider": "character varying",
            "default_model": "character varying",
            "theme": "character varying",
            "language": "character varying",
            "preferences": "jsonb",
            "created_at": "timestamp without time zone",
            "updated_at": "timestamp without time zone",
        }
    },
    "chat_sessions": {
        "columns": {
            "id": "character varying",
            "user_id": "character varying",
            "title": "character varying",
            "llm_provider": "character varying",
            "model_name": "character varying",
            "system_prompt": "text",
            "status": "character varying",
            "message_count": "integer",
            "created_at": "timestamp without time zone",
            "updated_at": "timestamp without time zone",
        }
    },
    "chat_messages": {
        "columns": {
            "id": "integer",
            "session_id": "character varying",
            "role": "character varying",
            "content": "text",
            "model_name": "character varying",
            "tokens_used": "integer",
            "metadata": "jsonb",
            "created_at": "timestamp without time zone",
        }
    },
    "research_sessions": {
        "columns": {
            "id": "character varying",
            "user_id": "character varying",
            "title": "text",
            "status": "character varying",
            "created_at": "timestamp without time zone",
            "updated_at": "timestamp without time zone",
            "ended_at": "timestamp without time zone",
        }
    },
    "research_findings": {
        "columns": {
            "id": "integer",
            "session_id": "character varying",
            "source_type": "character varying",
            "source_url": "text",
            "content": "text",
            "relevance_score": "double precision",
            "created_at": "timestamp without time zone",
        }
    },
    "research_citations": {
        "columns": {
            "id": "integer",
            "session_id": "character varying",
            "title": "text",
            "authors": "ARRAY",
            "source_url": "text",
            "publication_year": "integer",
            "doi": "character varying",
            "citation_type": "character varying",
            "created_at": "timestamp without time zone",
        }
    },
    "research_memory": {
        "columns": {
            "id": "integer",
            "session_id": "character varying",
            "message_role": "character varying",
            "message_name": "character varying",
            "message_content": "text",
            "timestamp": "character varying",
            "created_at": "timestamp without time zone",
        }
    },
}
