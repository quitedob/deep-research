"""Atomic, shared sliding-window request limits backed by Redis."""

import hashlib
import os
import secrets
from typing import Dict, Tuple

from fastapi import Depends, HTTPException, Request

from backend.core.security.redis_client import redis_client, SecurityStoreUnavailableError
from backend.middleware.auth import get_current_user


WINDOW_SCRIPT = """
local clock = redis.call('TIME')
local now = clock[1] * 1000 + math.floor(clock[2] / 1000)
local window = tonumber(ARGV[1])
local maximum = tonumber(ARGV[2])
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now - window)
local count = redis.call('ZCARD', KEYS[1])
local allowed = count < maximum
if ARGV[3] == '1' and allowed then
    redis.call('ZADD', KEYS[1], now, ARGV[4])
    redis.call('PEXPIRE', KEYS[1], window)
    count = count + 1
end
local oldest = redis.call('ZRANGE', KEYS[1], 0, 0, 'WITHSCORES')
local reset = now + window
if #oldest > 0 then reset = tonumber(oldest[2]) + window end
return {allowed and 1 or 0, count, reset}
"""


class SlidingWindowLimiter:
    def __init__(self, window_size: int = 3600, max_requests: int = 1000):
        if window_size <= 0 or max_requests <= 0:
            raise ValueError("Request limits and window size must be positive")
        self.window_size = window_size
        self.max_requests = max_requests

    @staticmethod
    def _cache_key(key: str, endpoint: str) -> str:
        identity = f"{key}:{endpoint}".encode("utf-8")
        return "rate_limit:" + hashlib.sha256(identity).hexdigest()

    async def _window(self, key: str, endpoint: str, consume: bool):
        return await redis_client.evaluate(
            WINDOW_SCRIPT, [self._cache_key(key, endpoint)],
            [self.window_size * 1000, self.max_requests, int(consume), secrets.token_hex(16)],
        )

    async def is_allowed(self, key: str, endpoint: str = "") -> Tuple[bool, int]:
        allowed, count, _ = await self._window(key, endpoint, True)
        return bool(allowed), int(count)

    async def get_remaining_requests(self, key: str, endpoint: str = "") -> int:
        _, count, _ = await self._window(key, endpoint, False)
        return max(0, self.max_requests - int(count))

    async def get_window_info(self, key: str, endpoint: str = "") -> Dict:
        _, count, reset = await self._window(key, endpoint, False)
        return {
            "window_size": self.window_size,
            "max_requests": self.max_requests,
            "current_requests": int(count),
            "remaining_requests": max(0, self.max_requests - int(count)),
            "reset_time": int(reset) / 1000,
        }

    async def reset(self, key: str, endpoint: str = "") -> bool:
        return await redis_client.delete(self._cache_key(key, endpoint))


request_limiter = SlidingWindowLimiter(
    window_size=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "3600")),
    max_requests=int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "1000")),
)
auth_limiter = SlidingWindowLimiter(window_size=60, max_requests=5)


async def _enforce(limiter, key, endpoint):
    try:
        allowed, _ = await limiter.is_allowed(key, endpoint)
    except SecurityStoreUnavailableError as exc:
        raise HTTPException(status_code=503, detail="请求限流服务暂时不可用") from exc
    if not allowed:
        raise HTTPException(
            status_code=429, detail="请求过于频繁，请稍后重试",
            headers={"Retry-After": str(limiter.window_size)},
        )


async def enforce_request_quota(request: Request, current_user=Depends(get_current_user)):
    """Attach to authenticated chat/research routers; all API calls share a user quota."""
    await _enforce(request_limiter, current_user["user_id"], "api")


async def enforce_auth_quota(request: Request):
    """Limit attempts using the direct peer address; untrusted proxy headers are ignored."""
    peer = request.client.host if request.client else "unknown"
    await _enforce(auth_limiter, peer, request.url.path)
