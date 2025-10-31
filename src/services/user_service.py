# -*- coding: utf-8 -*-
"""
UserService: 用户管理业务逻辑
提供用户相关的业务操作，包括注册、认证、权限管理等
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ..sqlmodel.models import User
from ..dao import UsersDAO
from ..dao.conversation import ConversationDAO
from .base_service import BaseService


class UserService(BaseService[User]):
    """用户业务逻辑服务"""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.users_dao = UsersDAO(session)
        self.conversation_dao = ConversationDAO(session)

    async def create_user(
        self,
        username: str,
        email: str,
        password_hash: str,
        role: str = "free"
    ) -> User:
        """
        创建新用户

        Args:
            username: 用户名
            email: 邮箱地址
            password_hash: 密码哈希
            role: 用户角色 (free, subscribed, admin)

        Returns:
            创建的用户对象

        Raises:
            ValueError: 如果用户名或邮箱已存在
        """
        # 验证用户名唯一性
        existing_user = await self.users_dao.get_by_username(username)
        if existing_user:
            raise ValueError(f"用户名 '{username}' 已被使用")

        # 验证邮箱唯一性
        if email:
            existing_email = await self.users_dao.get_by_email(email)
            if existing_email:
                raise ValueError(f"邮箱 '{email}' 已被使用")

        # 验证角色
        if role not in ["free", "subscribed", "admin"]:
            raise ValueError(f"无效的角色: {role}")

        # 创建用户
        try:
            await self.begin_transaction()
            user = await self.users_dao.create(
                username=username,
                email=email,
                password_hash=password_hash,
                role=role
            )
            await self.commit_transaction()

            await self.log_operation(
                user_id=user.id,
                operation="user_created",
                details={"username": username, "role": role}
            )

            return user

        except Exception as e:
            await self.rollback_transaction()
            raise e

    async def authenticate_user(self, username: str, password_hash: str) -> Optional[User]:
        """
        用户认证

        Args:
            username: 用户名
            password_hash: 密码哈希

        Returns:
            认证成功返回用户对象，失败返回 None
        """
        user = await self.users_dao.get_by_username(username)

        if not user:
            return None

        if not user.is_active:
            return None

        # 在实际应用中，这里应该使用密码验证库
        # 比如 bcrypt.checkpw(password.encode(), user.password_hash.encode())
        if user.password_hash != password_hash:
            return None

        await self.log_operation(
            user_id=user.id,
            operation="user_authenticated",
            details={"username": username}
        )

        return user

    async def update_user_role(self, user_id: str, new_role: str, updated_by: str) -> bool:
        """
        更新用户角色

        Args:
            user_id: 用户ID
            new_role: 新角色
            updated_by: 操作者ID

        Returns:
            更新成功返回 True，失败返回 False
        """
        # 验证权限
        if not await self.validate_permissions(updated_by, "admin"):
            raise PermissionError("没有权限修改用户角色")

        # 验证角色
        if new_role not in ["free", "subscribed", "admin"]:
            raise ValueError(f"无效的角色: {new_role}")

        try:
            await self.begin_transaction()

            user = await self.users_dao.get_by_id(user_id)
            if not user:
                await self.rollback_transaction()
                return False

            old_role = user.role
            success = await self.users_dao.update_role(user_id, new_role)

            if success:
                await self.commit_transaction()

                await self.log_operation(
                    user_id=updated_by,
                    operation="user_role_updated",
                    details={
                        "target_user_id": user_id,
                        "old_role": old_role,
                        "new_role": new_role
                    }
                )

                return True
            else:
                await self.rollback_transaction()
                return False

        except Exception as e:
            await self.rollback_transaction()
            raise e

    async def deactivate_user(self, user_id: str, deactivated_by: str) -> bool:
        """
        停用用户

        Args:
            user_id: 用户ID
            deactivated_by: 操作者ID

        Returns:
            停用成功返回 True，失败返回 False
        """
        # 验证权限
        if not await self.validate_permissions(deactivated_by, "admin"):
            raise PermissionError("没有权限停用用户")

        # 防止管理员停用自己
        if user_id == deactivated_by:
            raise ValueError("不能停用自己的账户")

        try:
            await self.begin_transaction()

            success = await self.users_dao.update_active_status(user_id, False)

            if success:
                await self.commit_transaction()

                await self.log_operation(
                    user_id=deactivated_by,
                    operation="user_deactivated",
                    details={"target_user_id": user_id}
                )

                return True
            else:
                await self.rollback_transaction()
                return False

        except Exception as e:
            await self.rollback_transaction()
            raise e

    async def activate_user(self, user_id: str, activated_by: str) -> bool:
        """
        激活用户

        Args:
            user_id: 用户ID
            activated_by: 操作者ID

        Returns:
            激活成功返回 True，失败返回 False
        """
        # 验证权限
        if not await self.validate_permissions(activated_by, "admin"):
            raise PermissionError("没有权限激活用户")

        try:
            await self.begin_transaction()

            success = await self.users_dao.update_active_status(user_id, True)

            if success:
                await self.commit_transaction()

                await self.log_operation(
                    user_id=activated_by,
                    operation="user_activated",
                    details={"target_user_id": user_id}
                )

                return True
            else:
                await self.rollback_transaction()
                return False

        except Exception as e:
            await self.rollback_transaction()
            raise e

    async def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户统计信息

        Args:
            user_id: 用户ID

        Returns:
            包含用户统计信息的字典
        """
        user = await self.users_dao.get_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")

        # 获取对话统计
        conversation_count = await self.conversation_dao.count_by_user(user_id)

        # 可以添加更多统计信息，比如文档处理任务数、API使用次数等

        return {
            "user_id": user_id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "conversation_count": conversation_count,
            # 可以添加更多统计字段
        }

    async def search_users(
        self,
        query: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[User]:
        """
        搜索用户

        Args:
            query: 搜索关键词
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            匹配的用户列表
        """
        return await self.users_dao.search_users(
            search_term=query,
            skip=skip,
            limit=limit
        )

    async def get_users_by_role(
        self,
        role: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[User]:
        """
        按角色获取用户

        Args:
            role: 用户角色
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            指定角色的用户列表
        """
        return await self.users_dao.get_users_by_role(
            role=role,
            skip=skip,
            limit=limit
        )

    async def update_user_profile(
        self,
        user_id: str,
        update_data: Dict[str, Any],
        updated_by: str
    ) -> Optional[User]:
        """
        更新用户资料

        Args:
            user_id: 用户ID
            update_data: 更新数据
            updated_by: 操作者ID

        Returns:
            更新后的用户对象，失败返回 None
        """
        # 验证权限（用户只能更新自己的资料，管理员可以更新任何用户）
        if user_id != updated_by:
            if not await self.validate_permissions(updated_by, "admin"):
                raise PermissionError("没有权限修改其他用户的资料")

        # 验证和清理更新数据
        allowed_fields = ["email"]  # 只允许更新邮箱
        sanitized_data = {}

        for field in allowed_fields:
            if field in update_data:
                if field == "email":
                    # 验证邮箱唯一性
                    existing_email = await self.users_dao.get_by_email(update_data[field])
                    if existing_email and str(existing_email.id) != user_id:
                        raise ValueError(f"邮箱 '{update_data[field]}' 已被使用")

                sanitized_data[field] = update_data[field]

        if not sanitized_data:
            return None

        try:
            await self.begin_transaction()

            updated_user = await self.users_dao.update(user_id, sanitized_data)

            if updated_user:
                await self.commit_transaction()

                await self.log_operation(
                    user_id=updated_by,
                    operation="user_profile_updated",
                    details={
                        "target_user_id": user_id,
                        "updated_fields": list(sanitized_data.keys())
                    }
                )

                return updated_user
            else:
                await self.rollback_transaction()
                return None

        except Exception as e:
            await self.rollback_transaction()
            raise e

    async def delete_user(self, user_id: str, deleted_by: str) -> bool:
        """
        删除用户（软删除，实际只是标记为不活跃）

        Args:
            user_id: 用户ID
            deleted_by: 操作者ID

        Returns:
            删除成功返回 True，失败返回 False
        """
        # 验证权限
        if not await self.validate_permissions(deleted_by, "admin"):
            raise PermissionError("没有权限删除用户")

        # 防止管理员删除自己
        if user_id == deleted_by:
            raise ValueError("不能删除自己的账户")

        return await self.deactivate_user(user_id, deleted_by)