# -*- coding: utf-8 -*-
"""
Base Migration Configuration for Deep Research Platform
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.declarative import declarative_base
import os

Base = declarative_base()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./deep_research.db"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
    echo=os.getenv("DB_ECHO", "false").lower() == "true"
)

# Async engine for background tasks
async_engine = create_async_engine(
    DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://"),
    echo=os.getenv("DB_ECHO", "false").lower() == "true"
)

# Session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)