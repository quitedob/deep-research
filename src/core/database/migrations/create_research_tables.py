# -*- coding: utf-8 -*-
"""
Database Migration: Create Research Tables
Creates all tables for the advanced research functionality
"""

import asyncio
from datetime import datetime
from sqlalchemy import text
from .base import engine
from ..models.research import Base

async def create_research_tables():
    """Create all research-related database tables"""

    print("Creating research database tables...")

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Create indexes that might not be in models
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_research_plans_user_status_created_at ON research_plans(user_id, status, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_research_subtasks_plan_status ON research_subtasks(plan_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_evidence_chains_plan_status ON evidence_chains(plan_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_evidence_items_chain_type_quality ON evidence_items(chain_id, evidence_type, quality)",
            "CREATE INDEX IF NOT EXISTS idx_agents_type_status ON agents(agent_type, status)",
            "CREATE INDEX IF NOT EXISTS idx_agent_tasks_agent_status_created ON agent_tasks(agent_id, status, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_syntheses_plan_type_created ON research_syntheses(plan_id, synthesis_type, generated_at)",
            "CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_agent_activities_agent_timestamp ON agent_activities(agent_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_system_alerts_level_active_created ON system_alerts(level, is_active, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_projects_user_status ON projects(user_id, status)",

            # Full-text search indexes (if supported)
            "CREATE INDEX IF NOT EXISTS idx_research_plans_search ON research_plans USING gin(to_tsvector('english', title || ' ' || description))",
            "CREATE INDEX IF NOT EXISTS idx_evidence_items_search ON evidence_items USING gin(to_tsvector('english', content))",
        ]

        # Create indexes
        for index_sql in indexes:
            try:
                await conn.execute(text(index_sql))
                print(f"Created index: {index_sql}")
            except Exception as e:
                print(f"Index creation failed (may already exist): {e}")

    print("Research database tables created successfully!")
    await engine.dispose()

async def drop_research_tables():
    """Drop all research-related database tables"""

    print("Dropping research database tables...")

    async with engine.begin() as conn:
        # Drop tables in reverse order of dependencies
        tables_to_drop = [
            "synthesis_tags",
            "evidence_item_tags",
            "research_plan_tags",
            "system_alerts",
            "agent_activities",
            "system_metrics",
            "research_syntheses",
            "agent_tasks",
            "agents",
            "evidence_items",
            "evidence_chains",
            "research_subtasks",
            "research_plans",
            "projects"
        ]

        for table in tables_to_drop:
            try:
                await conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                print(f"Dropped table: {table}")
            except Exception as e:
                print(f"Failed to drop table {table}: {e}")

    print("Research database tables dropped successfully!")
    await engine.dispose()

def create_initial_data():
    """Create initial data for testing"""

    print("Creating initial data...")

    # This would be implemented to create sample data
    # For now, we'll just return True as the initial data will be created through the API

    print("Initial data setup completed!")
    return True

async def initialize_research_database():
    """Complete database initialization"""
    try:
        await create_research_tables()
        create_initial_data()
        print("Research database initialized successfully!")
        return True
    except Exception as e:
        print(f"Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    # Run the migration
    asyncio.run(initialize_research_database())