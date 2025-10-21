# -*- coding: utf-8 -*-
"""
Migration Runner for Deep Research Platform
Runs all database migrations in the correct order
"""

import asyncio
import sys
import os

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, project_root)

# Add the src directory to the path
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from core.database.migrations.create_research_tables import initialize_research_database
from core.database.migrations.add_research_indexes import migrate_research_indexes

async def run_all_migrations():
    """Run all database migrations"""

    print("="*60)
    print("DEEP RESEARCH PLATFORM - DATABASE MIGRATION")
    print("="*60)

    try:
        # Step 1: Create research tables
        print("\n🔧 Step 1: Creating research database tables...")
        success1 = await initialize_research_database()

        if not success1:
            print("❌ Table creation failed!")
            return False

        print("✅ Research tables created successfully!")

        # Step 2: Add performance indexes
        print("\n🚀 Step 2: Adding performance indexes...")
        success2 = await migrate_research_indexes()

        if not success2:
            print("❌ Index migration failed!")
            return False

        print("✅ Performance indexes created successfully!")

        print("\n" + "="*60)
        print("🎉 ALL MIGRATIONS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nDatabase is now ready for the Deep Research Platform!")
        print("✅ Research Plans table")
        print("✅ Evidence Chains & Items tables")
        print("✅ Multi-Agent Orchestration tables")
        print("✅ Research Synthesis tables")
        print("✅ Monitoring & Metrics tables")
        print("✅ Performance optimization indexes")
        print("✅ Full-text search capabilities")

        return True

    except Exception as e:
        print(f"\n❌ Migration failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run the migration
    success = asyncio.run(run_all_migrations())

    if success:
        print("\n🎊 Database setup completed! Ready to start the platform.")
        sys.exit(0)
    else:
        print("\n💥 Database setup failed! Please check the error messages above.")
        sys.exit(1)