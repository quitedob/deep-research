"""Required Redis storage for token revocation, refresh rotation, and quotas."""

import json
import logging
import os
from typing import Optional

import redis.asyncio as redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class SecurityStoreUnavailableError(RuntimeError):
    """Security state cannot be read or persisted."""


class RedisClient:
    _instance = None
    _redis: Optional[redis.Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self):
        if self._redis is not None:
            await self.ping()
            return
        connection = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD") or None,
            db=int(os.getenv("REDIS_DB", "0")),
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        try:
            await connection.ping()
        except RedisError as exc:
            await connection.aclose()
            raise SecurityStoreUnavailableError("Redis is required for authentication and quotas") from exc
        self._redis = connection
        logger.info("Redis connected")

    async def close(self):
        connection = self._redis
        self._redis = None
        if connection is not None:
            await connection.aclose()

    def is_available(self) -> bool:
        return self._redis is not None

    async def _execute(self, method, *args, **kwargs):
        if self._redis is None:
            raise SecurityStoreUnavailableError("Redis is not connected")
        try:
            return await getattr(self._redis, method)(*args, **kwargs)
        except RedisError as exc:
            raise SecurityStoreUnavailableError("Security storage is temporarily unavailable") from exc

    async def ping(self) -> bool:
        return bool(await self._execute("ping"))

    async def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        return bool(await self._execute("set", key, value, ex=expire))

    async def get(self, key: str) -> Optional[str]:
        return await self._execute("get", key)

    async def delete(self, key: str) -> bool:
        await self._execute("delete", key)
        return True

    async def exists(self, key: str) -> bool:
        return bool(await self._execute("exists", key))

    async def expire(self, key: str, seconds: int) -> bool:
        return bool(await self._execute("expire", key, seconds))

    async def ttl(self, key: str) -> int:
        return await self._execute("ttl", key)

    async def set_json(self, key: str, value, expire: Optional[int] = None) -> bool:
        return await self.set(key, json.dumps(value, ensure_ascii=False), expire)

    async def get_json(self, key: str):
        value = await self.get(key)
        return json.loads(value) if value is not None else None

    async def incr(self, key: str) -> int:
        return await self._execute("incr", key)

    async def decr(self, key: str) -> int:
        return await self._execute("decr", key)

    async def evaluate(self, script: str, keys: list, args: list):
        return await self._execute("eval", script, len(keys), *keys, *args)

    async def compare_and_set(self, key: str, expected: str, value: str, expire: int) -> bool:
        # A replayed refresh token must not race another successful refresh.
        script = """
        if redis.call('GET', KEYS[1]) ~= ARGV[1] then return 0 end
        redis.call('SET', KEYS[1], ARGV[2], 'EX', ARGV[3])
        return 1
        """
        return bool(await self.evaluate(script, [key], [expected, value, expire]))


redis_client = RedisClient()
