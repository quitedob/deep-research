# -*- coding: utf-8 -*-
"""
配额执行中间件：实现高性能的配额检查系统，支持免费用户和订阅用户的不同限制。
"""

from __future__ import annotations

import time
import asyncio
from typing import Optional
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache import cache
from src.core.db import get_db_session
from src.sqlmodel.models import User, ApiUsageLog
from src.config.loader.config_loader import get_settings

settings = get_settings()


class QuotaMiddleware:
    """配额执行中间件"""
    
    def __init__(self):
        self.free_tier_limit = settings.free_tier_lifetime_limit
        self.subscribed_tier_limit = settings.subscribed_tier_hourly_limit
        self.quota_window_size = settings.quota_window_size
        
        # 需要配额检查的端点
        self.quota_endpoints = {
            "/api/llm/chat": "chat",
            "/api/research": "research",
            "/api/chat": "chat"
        }
    
    async def __call__(self, request: Request, call_next):
        """中间件主函数"""
        # 检查是否需要配额检查
        if not self._should_check_quota(request.url.path):
            return await call_next(request)
        
        # 获取用户信息（需要认证中间件在此之前运行）
        user = getattr(request.state, 'user', None)
        if not user:
            # 如果没有用户信息，跳过配额检查（由认证中间件处理）
            return await call_next(request)
        
        # 执行配额检查
        quota_check_result = await self._check_quota(user, request.url.path)
        if not quota_check_result['allowed']:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": quota_check_result['message'],
                    "quota_type": quota_check_result['quota_type'],
                    "limit": quota_check_result['limit'],
                    "used": quota_check_result['used'],
                    "remaining": quota_check_result['remaining']
                }
            )
        
        # 配额检查通过，执行请求
        response = await call_next(request)
        
        # 仅当请求成功时，记录用量
        if response.status_code == 200:
            await self._record_usage(user, request.url.path, quota_check_result)
        
        return response
    
    def _should_check_quota(self, path: str) -> bool:
        """检查是否需要配额检查"""
        return any(path.startswith(endpoint) for endpoint in self.quota_endpoints.keys())
    
    async def _check_quota(self, user: User, endpoint: str) -> dict:
        """检查用户配额"""
        try:
            if user.role == "free":
                return await self._check_free_tier_quota(user, endpoint)
            elif user.role == "subscribed":
                return await self._check_subscribed_tier_quota(user, endpoint)
            elif user.role == "admin":
                return {"allowed": True, "message": "Admin user", "quota_type": "admin"}
            else:
                return {"allowed": False, "message": "Invalid user role", "quota_type": "unknown"}
        except Exception as e:
            # 配额检查失败时，允许请求通过（避免阻塞用户）
            print(f"Quota check error for user {user.id}: {str(e)}")
            return {"allowed": True, "message": "Quota check failed, allowing request", "quota_type": "error"}
    
    async def _check_free_tier_quota(self, user: User, endpoint: str) -> dict:
        """检查免费用户配额（终身次数限制）"""
        try:
            # 使用 Redis 缓存查询结果，避免频繁数据库查询
            cache_key = f"free_quota:{user.id}:{endpoint}"
            cached_result = await cache.get(cache_key)
            
            if cached_result is not None:
                used_count = int(cached_result)
            else:
                # 查询数据库获取使用次数
                db = await get_db_session()
                result = await db.execute(
                    select(func.count(ApiUsageLog.id))
                    .where(ApiUsageLog.user_id == user.id)
                    .where(ApiUsageLog.endpoint_called == endpoint)
                )
                used_count = result.scalar_one() or 0
                await db.close()
                
                # 缓存结果 5 分钟
                await cache.set(cache_key, str(used_count), expire=300)
            
            remaining = max(0, self.free_tier_limit - used_count)
            allowed = remaining > 0
            
            return {
                "allowed": allowed,
                "message": "Free tier limit reached" if not allowed else "Quota available",
                "quota_type": "free_lifetime",
                "limit": self.free_tier_limit,
                "used": used_count,
                "remaining": remaining
            }
            
        except Exception as e:
            print(f"Free tier quota check error: {str(e)}")
            # 出错时允许请求通过
            return {"allowed": True, "message": "Quota check failed", "quota_type": "free_lifetime"}
    
    async def _check_subscribed_tier_quota(self, user: User, endpoint: str) -> dict:
        """检查订阅用户配额（每小时次数限制）"""
        try:
            # 使用 Redis 实现滑动窗口配额限制
            current_minute = int(time.time() / 60)
            cache_key = f"subscribed_quota:{user.id}:{endpoint}:{current_minute}"
            
            # 获取当前分钟的使用次数
            current_usage = await cache.get(cache_key)
            current_usage = int(current_usage) if current_usage else 0
            
            # 检查是否超过限制
            if current_usage >= self.subscribed_tier_limit:
                return {
                    "allowed": False,
                    "message": "Hourly limit reached",
                    "quota_type": "subscribed_hourly",
                    "limit": self.subscribed_tier_limit,
                    "used": current_usage,
                    "remaining": 0
                }
            
            # 增加当前分钟的使用次数
            await cache.incr(cache_key)
            await cache.expire(cache_key, self.quota_window_size)
            
            remaining = self.subscribed_tier_limit - (current_usage + 1)
            
            return {
                "allowed": True,
                "message": "Quota available",
                "quota_type": "subscribed_hourly",
                "limit": self.subscribed_tier_limit,
                "used": current_usage + 1,
                "remaining": remaining
            }
            
        except Exception as e:
            print(f"Subscribed tier quota check error: {str(e)}")
            # 出错时允许请求通过
            return {"allowed": True, "message": "Quota check failed", "quota_type": "subscribed_hourly"}
    
    async def _record_usage(self, user: User, endpoint: str, quota_result: dict):
        """记录 API 使用情况"""
        try:
            if user.role == "free":
                # 免费用户：记录到数据库
                await self._record_free_usage(user, endpoint)
            elif user.role == "subscribed":
                # 订阅用户：上报用量到 Stripe（异步）
                await self._report_stripe_usage(user, endpoint)
                
        except Exception as e:
            # 记录失败不影响用户响应
            print(f"Usage recording failed for user {user.id}: {str(e)}")
    
    async def _record_free_usage(self, user: User, endpoint: str):
        """记录免费用户使用情况到数据库"""
        try:
            db = await get_db_session()
            new_log = ApiUsageLog(
                user_id=user.id,
                endpoint_called=endpoint,
                extra="free_tier_usage"
            )
            db.add(new_log)
            await db.commit()
            await db.close()
            
            # 更新缓存中的使用次数
            cache_key = f"free_quota:{user.id}:{endpoint}"
            current_usage = await cache.get(cache_key)
            if current_usage is not None:
                await cache.incr(cache_key)
                
        except Exception as e:
            print(f"Failed to record free usage: {str(e)}")
    
    async def _report_stripe_usage(self, user: User, endpoint: str):
        """上报订阅用户用量到 Stripe（异步）"""
        try:
            # 这里应该调用 Stripe Meters API
            # 由于 Stripe 调用可能较慢，建议使用后台任务
            # 暂时记录到数据库作为备份
            db = await get_db_session()
            new_log = ApiUsageLog(
                user_id=user.id,
                endpoint_called=endpoint,
                extra="subscribed_tier_usage"
            )
            db.add(new_log)
            await db.commit()
            await db.close()
            
            # TODO: 实现 Stripe Meters API 调用
            # await self._call_stripe_meters_api(user, endpoint)
            
        except Exception as e:
            print(f"Failed to report Stripe usage: {str(e)}")
    
    async def _call_stripe_meters_api(self, user: User, endpoint: str):
        """调用 Stripe Meters API 上报用量"""
        # TODO: 实现 Stripe Meters API 调用
        # 需要安装 stripe 库并配置 API 密钥
        pass


# 创建中间件实例
quota_middleware = QuotaMiddleware()


async def get_quota_middleware():
    """获取配额中间件实例"""
    return quota_middleware
