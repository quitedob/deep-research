"""Isolated integration resources; never recreate application tables for tests."""

import os
import re
import uuid

import asyncpg
import pytest
import pytest_asyncio

from backend.repositories.base import BaseDAO
from backend.repositories.db_config import db_config
from backend.repositories.db_schema import ALL_TABLES


@pytest_asyncio.fixture
async def postgres_pool():
    if os.getenv("RUN_DATABASE_TESTS") != "1":
        pytest.skip("Set RUN_DATABASE_TESTS=1 to exercise an isolated PostgreSQL schema")
    schema = "repair_test_" + uuid.uuid4().hex
    assert re.fullmatch(r"repair_test_[0-9a-f]{32}", schema)
    connection = await asyncpg.connect(db_config.get_dsn(), timeout=5)
    previous_pool, previous_enabled = BaseDAO._pool, BaseDAO._use_database
    pool = None
    try:
        await connection.execute(f'CREATE SCHEMA "{schema}"')
        pool = await asyncpg.create_pool(
            db_config.get_dsn(), min_size=1, max_size=3,
            server_settings={"search_path": schema, "timezone": "UTC"},
        )
        BaseDAO._pool, BaseDAO._use_database = pool, True
        async with pool.acquire() as conn:
            for ddl in ALL_TABLES.values():
                await conn.execute(ddl)
            await conn.executemany(
                "INSERT INTO users(id,username,email,password_hash) VALUES($1,$1,$2,$3)",
                [("alice", "alice@testing.invalid", "not-a-login-hash"),
                 ("bob", "bob@testing.invalid", "not-a-login-hash")],
            )
        yield pool
    finally:
        BaseDAO._pool, BaseDAO._use_database = previous_pool, previous_enabled
        if pool is not None:
            await pool.close()
        await connection.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        await connection.close()


@pytest_asyncio.fixture
async def redis_store(monkeypatch):
    port = os.getenv("TEST_REDIS_PORT")
    if not port:
        pytest.skip("Set TEST_REDIS_PORT for the isolated local Redis test instance")
    from backend.core.security.redis_client import redis_client
    previous = redis_client._redis
    redis_client._redis = None
    monkeypatch.setenv("REDIS_HOST", "127.0.0.1")
    monkeypatch.setenv("REDIS_PORT", port)
    monkeypatch.setenv("REDIS_PASSWORD", "")
    monkeypatch.setenv("REDIS_DB", "0")
    try:
        await redis_client.connect()
        yield redis_client
    finally:
        await redis_client.close()
        redis_client._redis = previous
