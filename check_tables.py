#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库表
"""

import asyncio
from dotenv import load_dotenv
from pkg.db import get_db_session
from sqlalchemy import text

load_dotenv()

async def check_tables():
    """检查数据库中的表"""
    try:
        async for session in get_db_session():
            # 获取所有表
            result = await session.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'deerflow'")
            )
            tables = [row[0] for row in result.fetchall()]
            
            print("📊 数据库中的表:")
            for table in sorted(tables):
                print(f"   ✓ {table}")
            
            print(f"\n总共 {len(tables)} 个表")
            break
            
    except Exception as e:
        print(f"❌ 检查表失败: {e}")

if __name__ == "__main__":
    asyncio.run(check_tables())