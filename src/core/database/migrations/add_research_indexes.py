# -*- coding: utf-8 -*-
"""
Database Migration: Add Research Performance Indexes
Adds performance optimization indexes for research tables
"""

import asyncio
from sqlalchemy import text
from .base import engine

async def add_research_indexes():
    """Add performance indexes for research tables"""

    print("Adding research performance indexes...")

    # Performance optimization indexes
    indexes = [
        # Research plan indexes
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_research_plans_user_status_created_at ON research_plans(user_id, status, created_at)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_research_plans_status_progress ON research_plans(status, progress_percentage)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_research_plans_domain_type ON research_plans(domain, research_type)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_research_plans_created_at_desc ON research_plans(created_at DESC)",

        # Subtask indexes
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_research_subtasks_plan_status_priority ON research_subtasks(plan_id, status, priority)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_research_subtasks_plan_order ON research_subtasks(plan_id, `order`)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_research_subtasks_status_created_at ON research_subtasks(status, created_at)",

        # Evidence chain indexes
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_evidence_chains_plan_status ON evidence_chains(plan_id, status)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_evidence_chains_confidence_quality ON evidence_chains(confidence_level, quality_score)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_evidence_chains_created_at_desc ON evidence_chains(created_at DESC)",

        # Evidence item indexes
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_evidence_items_chain_type_quality ON evidence_items(chain_id, evidence_type, quality)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_evidence_items_confidence_relevance ON evidence_items(confidence_score, relevance_score)",
        "CREATE INDEX IF NOT EXISTS idx_evidence_items_created_at_desc ON evidence_items(created_at DESC)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_evidence_items_collected_by_date ON evidence_items(collected_by, collection_date)",

        # Agent indexes
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agents_type_status ON agents(agent_type, status)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agents_status_activity ON agents(status, last_activity)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agents_success_rate ON agents(success_rate)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agents_created_at_desc ON agents(created_at DESC)",

        # Agent task indexes
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_tasks_agent_status_created ON agent_tasks(agent_id, status, created_at)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_tasks_type_priority ON agent_tasks(task_type, priority)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_tasks_status_progress ON agent_tasks(status, progress)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_tasks_created_at_desc ON agent_tasks(created_at DESC)",

        # Research synthesis indexes
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_research_syntheses_plan_type ON research_syntheses(plan_id, synthesis_type)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_research_syntheses_user_created_at ON research_syntheses(created_by, generated_at)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_research_syntheses_confidence_quality ON research_syntheses(confidence_level, quality_score)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_research_syntheses_created_at_desc ON research_syntheses(generated_at DESC)",

        # System metrics indexes
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_metrics_timestamp_desc ON system_metrics(timestamp DESC)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_metrics_cpu_memory ON system_metrics(cpu_usage, memory_usage)",

        # Agent activity indexes
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_activities_agent_timestamp ON agent_activities(agent_id, timestamp)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_activities_status_timestamp ON agent_activities(status, timestamp)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_activities_type_timestamp ON agent_activities(activity_type, timestamp)",

        # System alert indexes
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_alerts_level_active_created ON system_alerts(level, is_active, created_at)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_alerts_active_created_at ON system_alerts(is_active, created_at)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_alerts_created_at_desc ON system_alerts(created_at DESC)",

        # Project indexes
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_user_status ON projects(user_id, status)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_created_at_desc ON projects(created_at DESC)",

        # JSON field indexes (PostgreSQL specific)
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_research_plans_insights_gin ON research_plans USING gin(insights)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_research_plans_findings_gin ON research_plans USING gin(key_findings)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_evidence_items_tags_gin ON evidence_items USING gin(tags)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_evidence_items_metadata_gin ON evidence_items USING gin(metadata)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_tasks_parameters_gin ON agent_tasks USING gin(parameters)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_research_syntheses_insights_gin ON research_syntheses USING gin(key_insights)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_research_syntheses_recommendations_gin ON research_syntheses USING gin(recommendations)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_research_syntheses_themes_gin ON research_syntheses USING gin(themes)",

        # Partial indexes for better performance
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_research_plans_active ON research_plans(status) WHERE status = 'in_progress'",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_evidence_items_high_quality ON evidence_items(evidence_type, quality) WHERE quality = 'high'",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agents_working ON agents(status) WHERE status = 'working'",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_alerts_active ON system_alerts(is_active) WHERE is_active = true",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_alerts_critical ON system_alerts(level) WHERE level = 'critical'",

        # Full-text search indexes
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_research_plans_search ON research_plans USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '') || ' ' || COALESCE(research_query, '')))",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_evidence_items_search ON evidence_items USING gin(to_tsvector('english', COALESCE(content, '')))",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_research_syntheses_search ON research_syntheses USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')))",

        # Trigram indexes for fuzzy search
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_research_plans_title_trgm ON research_plans USING gin(title gin_trgm_ops)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_evidence_items_content_trgm ON evidence_items USING gin(content gin_trgm_ops)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_research_syntheses_title_trgm ON research_syntheses USING gin(title gin_trgm_ops)"
    ]

    async with engine.begin() as conn:
        for index_sql in indexes:
            try:
                await conn.execute(text(index_sql))
                print(f"Created index: {index_sql}")
            except Exception as e:
                print(f"Index creation failed (may already exist): {e}")

    print("Research performance indexes added successfully!")
    await engine.dispose()

async def drop_research_indexes():
    """Drop performance indexes for research tables"""

    print("Dropping research performance indexes...")

    # List of indexes to drop (excluding primary keys and foreign keys)
    indexes_to_drop = [
        "DROP INDEX CONCURRENTLY IF EXISTS idx_research_plans_user_status_created_at",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_research_plans_status_progress",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_research_plans_domain_type",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_research_plans_created_at_desc",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_research_subtasks_plan_status_priority",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_research_subtasks_plan_order",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_research_subtasks_status_created_at",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_evidence_chains_plan_status",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_evidence_chains_confidence_quality",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_evidence_chains_created_at_desc",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_evidence_items_chain_type_quality",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_evidence_items_confidence_relevance",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_evidence_items_created_at_desc",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_evidence_items_collected_by_date",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_agents_type_status",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_agents_status_activity",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_agents_success_rate",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_agents_created_at_desc",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_agent_tasks_agent_status_created",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_agent_tasks_type_priority",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_agent_tasks_status_progress",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_agent_tasks_created_at_desc",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_research_syntheses_plan_type",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_research_syntheses_user_created_at",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_research_syntheses_confidence_quality",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_research_syntheses_created_at_desc",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_system_metrics_timestamp_desc",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_system_metrics_cpu_memory",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_agent_activities_agent_timestamp",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_agent_activities_status_timestamp",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_agent_activities_type_timestamp",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_system_alerts_level_active_created",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_system_alerts_active_created_at",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_system_alerts_created_at_desc",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_projects_user_status",
        "DROP INDEX CONCURRENTLY IF EXISTS idx_projects_created_at_desc"
    ]

    async with engine.begin() as conn:
        for index_sql in indexes_to_drop:
            try:
                await conn.execute(text(index_sql))
                print(f"Dropped index: {index_sql}")
            except Exception as e:
                print(f"Index drop failed: {e}")

    print("Research performance indexes dropped successfully!")
    await engine.dispose()

async def optimize_database():
    """Run database optimization commands"""

    print("Optimizing database...")

    async with engine.begin() as conn:
        try:
            # Analyze tables (PostgreSQL specific)
            await conn.execute(text("ANALYZE"))
            print("Database analysis completed")

            # Update statistics (PostgreSQL specific)
            await conn.execute(text("UPDATE pg_statistic SET last_analyze = NOW()"))
            print("Statistics updated")

        except Exception as e:
            print(f"Database optimization skipped (not supported or failed): {e}")

    await engine.dispose()

async def migrate_research_indexes():
    """Complete index migration for research tables"""
    try:
        await drop_research_indexes()
        await add_research_indexes()
        await optimize_database()
        print("Research indexes migration completed successfully!")
        return True
    except Exception as e:
        print(f"Research indexes migration failed: {e}")
        return False

if __name__ == "__main__":
    # Run the migration
    asyncio.run(migrate_research_indexes())