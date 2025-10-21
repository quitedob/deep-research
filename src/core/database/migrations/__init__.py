# -*- coding: utf-8 -*-
"""
Database Migrations Package for Deep Research Platform
"""

from .base import engine, async_engine, SessionLocal, AsyncSessionLocal
from .create_research_tables import create_research_tables, drop_research_tables, initialize_research_database
from .add_research_indexes import add_research_indexes, drop_research_indexes, optimize_database, migrate_research_indexes

__all__ = [
    "engine",
    "async_engine",
    "SessionLocal",
    "AsyncSessionLocal",
    "create_research_tables",
    "drop_research_tables",
    "initialize_research_database",
    "add_research_indexes",
    "drop_research_indexes",
    "optimize_database",
    "migrate_research_indexes"
]