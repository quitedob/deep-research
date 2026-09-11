from unittest.mock import AsyncMock

import pytest


def startup_boundaries(monkeypatch):
    from backend.core.security.jwt_manager import jwt_manager
    from backend.core.security.redis_client import redis_client
    from backend.repositories.base import BaseDAO
    from backend.core.llm.base_llm import BaseLLM
    from backend.api.deep_research import research_service
    monkeypatch.setenv("JWT_SECRET_KEY", "test-startup-secret-" + "a" * 32)
    monkeypatch.setattr(redis_client, "connect", AsyncMock())
    monkeypatch.setattr(redis_client, "close", AsyncMock())
    monkeypatch.setattr(BaseDAO, "init_pool", AsyncMock())
    monkeypatch.setattr(BaseDAO, "close_pool", AsyncMock())
    monkeypatch.setattr(BaseLLM, "close_all", AsyncMock())
    monkeypatch.setattr(research_service, "close", AsyncMock())
    return redis_client, BaseDAO


async def test_startup_refuses_to_serve_without_database(monkeypatch):
    import backend.main as app
    from backend.repositories import db_init
    redis, dao = startup_boundaries(monkeypatch)
    monkeypatch.setattr(db_init, "init_database", AsyncMock(return_value=False))
    with pytest.raises(RuntimeError, match="Database initialization failed"):
        async with app.lifespan(app.app):
            pytest.fail("Application must not serve requests without persistence")
    dao.init_pool.assert_not_awaited()
    redis.close.assert_awaited_once()


async def test_startup_refuses_second_worker_and_closes_connection(monkeypatch):
    import backend.main as app
    from backend.repositories import db_init
    redis, dao = startup_boundaries(monkeypatch)
    monkeypatch.setattr(db_init, "init_database", AsyncMock(return_value=True))
    connection = AsyncMock()
    connection.fetchval.return_value = False
    monkeypatch.setattr(app.asyncpg, "connect", AsyncMock(return_value=connection))
    with pytest.raises(RuntimeError, match="single application worker"):
        async with app.lifespan(app.app):
            pytest.fail("A second worker must not silently lose research state")
    dao.init_pool.assert_not_awaited()
    connection.close.assert_awaited_once()


async def test_startup_requires_persistent_redis(monkeypatch):
    import backend.main as app
    from backend.repositories import db_init
    from backend.core.security.redis_client import SecurityStoreUnavailableError
    redis, dao = startup_boundaries(monkeypatch)
    redis.connect.side_effect = SecurityStoreUnavailableError("test unavailable")
    init = AsyncMock()
    monkeypatch.setattr(db_init, "init_database", init)
    with pytest.raises(SecurityStoreUnavailableError):
        async with app.lifespan(app.app):
            pytest.fail("Application must not serve without security state")
    init.assert_not_awaited()


async def test_startup_and_shutdown_acquire_and_release_ownership(monkeypatch):
    import backend.main as app
    from backend.repositories import db_init
    redis, dao = startup_boundaries(monkeypatch)
    monkeypatch.setattr(db_init, "init_database", AsyncMock(return_value=True))
    connection = AsyncMock()
    connection.fetchval.return_value = True
    monkeypatch.setattr(app.asyncpg, "connect", AsyncMock(return_value=connection))
    async with app.lifespan(app.app):
        dao.init_pool.assert_awaited_once()
        connection.close.assert_not_awaited()
    connection.close.assert_awaited_once()
    dao.close_pool.assert_awaited_once()
