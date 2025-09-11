# -*- coding: utf-8 -*-
"""
安全创建管理员用户脚本。
从环境变量读取管理员凭证，避免硬编码敏感信息。
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from pkg.db import get_sessionmaker
from src.sqlmodel.models import User
from src.config.settings import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_admin_user():
    """安全创建管理员用户"""
    # 从环境变量获取管理员信息
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@deepresearch.com")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_password:
        print("错误：必须设置 ADMIN_PASSWORD 环境变量")
        print("示例：ADMIN_PASSWORD=my_secure_password python scripts/create_admin.py")
        return False

    # 哈希密码
    hashed_password = pwd_context.hash(admin_password)

    async with get_sessionmaker()() as session:
        try:
            # 检查用户是否已存在
            existing_user = await session.get(User, admin_username)
            if existing_user:
                print(f"管理员用户 '{admin_username}' 已存在")
                return True

            # 创建新管理员用户
            admin_user = User(
                username=admin_username,
                email=admin_email,
                password_hash=hashed_password,
                role="admin",
                is_active=True
            )

            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)

            print("✓ 管理员用户创建成功"            print(f"  用户名: {admin_username}")
            print(f"  邮箱: {admin_email}")
            print(f"  角色: admin")
            print("\n⚠️  请妥善保存管理员密码，不要在代码或日志中明文存储")

            return True

        except Exception as e:
            await session.rollback()
            print(f"创建管理员用户失败: {e}")
            return False


async def main():
    """主函数"""
    print("🔐 DeerFlow 管理员用户创建工具")
    print("=" * 40)

    success = await create_admin_user()

    if success:
        print("\n✅ 操作完成")
        return 0
    else:
        print("\n❌ 操作失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
