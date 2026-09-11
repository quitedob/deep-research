"""Regression tests for authentication, database error handling, and scoped persistence."""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
from urllib.parse import unquote, urlsplit
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
import jwt
import pytest
from sqlalchemy import Integer, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import configure_mappers

from backend.api import user as user_api
from backend.core.security.jwt_manager import JWTManager
from backend.core.security.passwords import hash_password, verify_password
from backend.core.security.quota import SlidingWindowLimiter, _enforce
from backend.core.security.redis_client import SecurityStoreUnavailableError, redis_client
from backend.core.security.sanitizer.security import sanitize_model_output
from backend.repositories.base import BaseDAO, DatabaseUnavailableError
from backend.repositories.chat_dao import ChatDAO
from backend.repositories.db_config import DatabaseConfig
from backend.repositories.db_init import DatabaseInitializer, SchemaMismatchError
from backend.repositories.memory_dao import MemoryDAO
from backend.repositories.research_dao import ResearchDAO
from backend.repositories.user_dao import UserDAO
from backend.middleware.auth import get_optional_user
from backend.schemas.chat import ChatResponse, ChatSessionCreate
from backend.schemas.user import UserLogin, UserPreferences
from backend.services.user_service import UserService
from backend.models.research_models import Base, ResearchCitation


TEST_SECRET = "regression-tests-only-key-never-for-production-1234"


class ConnectionPool:
    def __init__(self, connection):
        self.connection = connection

    @asynccontextmanager
    async def acquire(self):
        yield self.connection


@asynccontextmanager
async def transaction():
    yield


def test_password_hashes_are_salted_and_verify():
    first, second = hash_password("correct password"), hash_password("correct password")
    assert first != second
    assert first.startswith("pbkdf2_sha256$600000$")
    assert verify_password("correct password", first)
    assert not verify_password("wrong password", first)
    assert not verify_password("correct password", "not-a-password-hash")


@pytest.mark.asyncio
async def test_successful_legacy_login_upgrades_hash_before_issuing_tokens():
    password = "legacy password"
    service = UserService()
    service.user_dao = SimpleNamespace(
        get_user_by_username=AsyncMock(return_value={
            "id": "user", "username": "alice", "is_active": True,
            "password_hash": hashlib.sha256(password.encode()).hexdigest(),
        }),
        update_password_hash=AsyncMock(), update_last_login=AsyncMock(),
    )
    manager = JWTManager(TEST_SECRET)
    manager.store_refresh_token = AsyncMock(return_value=True)
    service.jwt_manager = manager
    result = await service.login(UserLogin(username="alice", password=password))
    user_id, upgraded_hash = service.user_dao.update_password_hash.await_args.args
    assert user_id == "user" and verify_password(password, upgraded_hash)
    assert "password_hash" not in result["user"]
    assert manager.verify_token(result["access_token"])[0]


def test_jwt_requires_stable_config_and_token_type(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
        JWTManager().validate_configuration()
    first, second = JWTManager(TEST_SECRET), JWTManager(TEST_SECRET)
    access, refresh = first.create_token_pair("user", "alice")
    assert second.verify_token(access)[0]
    assert not second.verify_token(refresh)[0]
    assert second.verify_token(refresh, expected_type="refresh")[0]
    claims = first.decode_token(first.create_access_token("user", "alice", {"sub": "victim", "type": "refresh"}))
    assert claims["sub"] == "user" and claims["type"] == "access"


def test_malformed_expired_and_missing_claim_tokens_are_invalid():
    manager = JWTManager(TEST_SECRET)
    expired = jwt.encode({
        "sub": "user", "username": "alice", "type": "access",
        "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }, TEST_SECRET, algorithm="HS256")
    missing_exp = jwt.encode({"sub": "user"}, TEST_SECRET, algorithm="HS256")
    wrong_signature = JWTManager(TEST_SECRET + "wrong").create_access_token("user", "alice")
    for token in ("garbage", "", expired, missing_exp, wrong_signature):
        assert manager.decode_token(token) is None


@pytest.mark.asyncio
async def test_optional_auth_only_allows_absent_credentials(monkeypatch):
    monkeypatch.setattr(UserService, "get_current_user", AsyncMock(return_value=None))
    assert await get_optional_user(None) is None
    for header in ("", "Basic abc", "Bearer broken"):
        with pytest.raises(HTTPException) as error:
            await get_optional_user(header)
        assert error.value.status_code == 401


def test_refresh_accepts_json_and_preserves_invalid_token_status(monkeypatch):
    app = FastAPI()
    app.include_router(user_api.router)
    refresh = AsyncMock(return_value={"access_token": "new-access", "refresh_token": "new-refresh"})
    monkeypatch.setattr(user_api.user_service, "refresh_token", refresh)
    with TestClient(app) as client:
        response = client.post("/api/users/refresh", json={"refresh_token": "old-refresh"})
        assert response.status_code == 200
        refresh.assert_awaited_once_with("old-refresh")
        assert client.post("/api/users/refresh?refresh_token=old-refresh").status_code == 422
        refresh.return_value = None
        assert client.post("/api/users/refresh", json={"refresh_token": "expired"}).status_code == 401
        refresh.side_effect = SecurityStoreUnavailableError("private backend details")
        response = client.post("/api/users/refresh", json={"refresh_token": "old-refresh"})
        assert response.status_code == 503
        assert "private backend details" not in response.text


def test_user_endpoint_rejects_refresh_token_and_reports_storage_outage(monkeypatch):
    app = FastAPI()
    app.include_router(user_api.router)
    monkeypatch.setattr(user_api.user_service.jwt_manager, "_secret_key", TEST_SECRET)
    refresh = JWTManager(TEST_SECRET).create_refresh_token("user", "alice")
    with TestClient(app) as client:
        assert client.get("/api/users/me", headers={"Authorization": f"Bearer {refresh}"}).status_code == 401
        monkeypatch.setattr(UserService, "get_current_user", AsyncMock(side_effect=RuntimeError("private DSN")))
        response = client.get("/api/users/me", headers={"Authorization": "Bearer present"})
        assert response.status_code == 503 and "private DSN" not in response.text


@pytest.mark.asyncio
async def test_database_disabled_and_driver_errors_propagate(monkeypatch):
    monkeypatch.setattr(BaseDAO, "_pool", None)
    monkeypatch.setattr(BaseDAO, "_use_database", False)
    for operation in (BaseDAO().execute_query, BaseDAO().fetch_one, BaseDAO().fetch_all):
        with pytest.raises(DatabaseUnavailableError):
            await operation("SELECT 1")
    connection = SimpleNamespace(
        execute=AsyncMock(side_effect=RuntimeError("write failed")),
        fetchrow=AsyncMock(side_effect=RuntimeError("insert failed")),
        fetch=AsyncMock(side_effect=RuntimeError("read failed")),
    )
    monkeypatch.setattr(BaseDAO, "_pool", ConnectionPool(connection))
    monkeypatch.setattr(BaseDAO, "_use_database", True)
    operations = [
        UserDAO().update_user_profile("user", full_name="Changed"),
        UserDAO().update_user_preferences("user", preferences={"nested": True}),
        ChatDAO().create_session("user", "title", "deepseek", "deepseek-flash"),
        ChatDAO().add_message("session", "user", "message"),
        MemoryDAO().create_user_fact("user", "fact"),
        BaseDAO().fetch_all("SELECT 1"),
    ]
    for operation in operations:
        with pytest.raises(RuntimeError, match="failed"):
            await operation


@pytest.mark.asyncio
async def test_json_preferences_roundtrip_and_citation_array_encoding(monkeypatch):
    preferences = {"nested": {"enabled": True}, "list": ["a", "b"]}
    connection = SimpleNamespace(
        execute=AsyncMock(return_value="UPDATE 1"),
        fetchrow=AsyncMock(return_value={"preferences": json.dumps(preferences)}),
    )
    monkeypatch.setattr(BaseDAO, "_pool", ConnectionPool(connection))
    monkeypatch.setattr(BaseDAO, "_use_database", True)
    assert await UserDAO().update_user_preferences("user", preferences=preferences)
    assert json.loads(connection.execute.await_args.args[1]) == preferences
    assert (await UserDAO().get_user_preferences("user"))["preferences"] == preferences
    connection.fetchrow.return_value = {"id": 3}
    created_at = datetime(2026, 9, 11, 14, tzinfo=timezone(timedelta(hours=8)))
    assert await ResearchDAO().add_citation("session", "title", ["Alice", "Bob"], "https://example.com", created_at=created_at) == 3
    assert connection.fetchrow.await_args.args[3] == ["Alice", "Bob"]
    assert connection.fetchrow.await_args.args[-1] == datetime(2026, 9, 11, 6)


@pytest.mark.asyncio
async def test_startup_schema_mismatch_never_executes_destructive_ddl(monkeypatch):
    initializer = DatabaseInitializer()
    connection = SimpleNamespace(transaction=transaction, execute=AsyncMock(), close=AsyncMock())
    monkeypatch.setattr("backend.repositories.db_init.asyncpg.connect", AsyncMock(return_value=connection))
    initializer._table_exists = AsyncMock(return_value=True)
    initializer._validate_table_schema = AsyncMock(return_value=False)
    with pytest.raises(SchemaMismatchError, match="explicit migration"):
        await initializer._check_and_init_tables()
    connection.execute.assert_not_awaited()
    connection.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_seed_users_require_explicit_development_opt_in(monkeypatch):
    connection = SimpleNamespace(execute=AsyncMock())
    monkeypatch.delenv("ENABLE_TEST_USERS", raising=False)
    await DatabaseInitializer()._create_test_users(connection)
    connection.execute.assert_not_awaited()
    monkeypatch.setenv("ENABLE_TEST_USERS", "true")
    monkeypatch.setenv("APP_ENV", "production")
    with pytest.raises(ValueError, match="only"):
        await DatabaseInitializer()._create_test_users(connection)


def test_database_dsn_preserves_reserved_characters(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_USER", "user@example")
    monkeypatch.setenv("DB_PASSWORD", "password:/?#@")
    monkeypatch.setenv("DB_NAME", "research/name")
    parsed = urlsplit(DatabaseConfig().get_dsn())
    assert unquote(parsed.username) == "user@example"
    assert unquote(parsed.password) == "password:/?#@"
    assert unquote(parsed.path) == "/research/name"
    monkeypatch.setenv("DATABASE_URL", "postgresql://app@localhost/research?sslmode=require")
    monkeypatch.setenv("DB_PASSWORD", "")
    config = DatabaseConfig()
    assert config.get_dsn() == "postgresql://app@localhost/research?sslmode=require"
    assert config.validate()[0]


@pytest.mark.asyncio
async def test_quota_inspection_does_not_consume_and_outages_fail_closed(monkeypatch):
    evaluate = AsyncMock(return_value=[1, 2, 10000])
    monkeypatch.setattr(redis_client, "evaluate", evaluate)
    limiter = SlidingWindowLimiter(window_size=60, max_requests=5)
    assert await limiter.get_remaining_requests("user") == 3
    assert evaluate.await_args.args[2][2] == 0
    assert (await limiter.get_window_info("user"))["current_requests"] == 2
    assert evaluate.await_args.args[2][2] == 0
    evaluate.side_effect = SecurityStoreUnavailableError("offline")
    with pytest.raises(HTTPException) as error:
        await _enforce(limiter, "user", "api")
    assert error.value.status_code == 503


def test_orm_matches_integer_ids_and_postgres_author_array():
    configure_mappers()
    assert isinstance(ResearchCitation.__table__.c.id.type, Integer)
    assert isinstance(ResearchCitation.__table__.c.authors.type, ARRAY)
    assert isinstance(ResearchCitation.__table__.c.authors.type.item_type, Text)
    assert set(Base.metadata.tables) == {"research_sessions", "research_findings", "research_citations", "research_memory"}


def test_nested_usage_default_model_and_output_sanitization():
    response = ChatResponse(session_id="session", message={"role": "assistant", "content": "ok"}, usage={
        "prompt_tokens": 10, "prompt_tokens_details": {"cached_tokens": 3},
    })
    assert response.usage["prompt_tokens_details"]["cached_tokens"] == 3
    assert UserPreferences().default_model == "deepseek-flash"
    assert ChatSessionCreate(title="title").model_name == "deepseek-flash"
    assert ChatSessionCreate(title="title", model_name="explicit").model_name == "explicit"
    sanitized = sanitize_model_output('<script>alert("secret")</script><b>safe</b>')
    assert "secret" not in sanitized and "<b>" not in sanitized and "safe" in sanitized


@pytest.mark.asyncio
async def test_search_requires_a_scope():
    dao = ResearchDAO()
    dao.fetch_all = AsyncMock()
    assert await dao.search_research_content("AI: the future & plans") == []
    dao.fetch_all.assert_not_awaited()


@pytest.mark.asyncio
async def test_postgres_citation_roundtrip_and_scope_all_search_branches(postgres_pool):
    dao = ResearchDAO()
    for user_id in ("alice", "bob"):
        session_id = f"{user_id}-research"
        await dao.create_research_session(session_id, user_id, "AI future research")
        await dao.add_research_finding(session_id, "web", "https://example.com", "AI future finding")
        await dao.add_citation(session_id, "AI future citation", [user_id, "Coauthor"], "https://example.com")
        await dao.save_message_to_long_term(session_id, "assistant", "memory", "AI future memory", "2026-09-11T00:00:00Z")
    citations = await dao.get_session_citations("alice-research")
    assert citations[0]["authors"] == ["alice", "Coauthor"]
    assert (await dao.get_research_findings("alice-research"))[0]["relevance_score"] is None
    results = await dao.search_research_content("AI: the future", user_id="alice")
    assert {row["content_type"] for row in results} == {"finding", "citation", "memory"}
    assert {row["session_id"] for row in results} == {"alice-research"}
    assert await dao.search_research_content("AI: the future", user_id="alice", session_id="bob-research") == []
    assert await dao.search_research_content("AI: the future", user_id="user-with-no-sessions") == []
    assert await dao.search_research_content("a & b", user_id="alice") == []


@pytest.mark.asyncio
async def test_postgres_preferences_and_chat_message_persist_together(postgres_pool):
    user = await UserDAO().create_user("carol", "carol@testing.invalid", hash_password("password for testing"))
    assert (await UserDAO().get_user_preferences(user["id"]))["default_model"] == "deepseek-flash"
    preferences = {"nested": {"enabled": True}, "models": ["deepseek-flash"]}
    assert await UserDAO().update_user_preferences(user["id"], preferences=preferences)
    assert (await UserDAO().get_user_preferences(user["id"]))["preferences"] == preferences
    await UserDAO().update_user_preferences(user["id"], default_model="explicit-model")
    await UserService().update_preferences(user["id"], UserPreferences(theme="dark"))
    assert (await UserDAO().get_user_preferences(user["id"]))["default_model"] == "explicit-model"
    chat = ChatDAO()
    session = await chat.create_session(user["id"], "chat", "deepseek", "deepseek-flash")
    await chat.add_message(session["id"], "user", "question", metadata={"nested": {"k": "v"}})
    assert (await chat.get_session(session["id"]))["message_count"] == 1
    assert (await chat.get_session_messages(session["id"]))[0]["metadata"] == {"nested": {"k": "v"}}
    assert await chat.clear_session_messages(session["id"])
    assert (await chat.get_session(session["id"]))["message_count"] == 0
    assert await chat.get_session_messages(session["id"]) == []


@pytest.mark.asyncio
async def test_postgres_secondary_write_failure_rolls_back_primary_insert(postgres_pool):
    import asyncpg
    await postgres_pool.execute(
        "ALTER TABLE user_preferences ADD CONSTRAINT reject_model CHECK (default_model <> 'deepseek-flash')"
    )
    with pytest.raises(asyncpg.CheckViolationError):
        await UserDAO().create_user("carol", "carol@testing.invalid", "hash")
    assert await postgres_pool.fetchval("SELECT count(*) FROM users WHERE username = 'carol'") == 0
    chat = ChatDAO()
    session = await chat.create_session("alice", "chat", "deepseek", "deepseek-flash")
    await postgres_pool.execute("ALTER TABLE chat_sessions ADD CONSTRAINT reject_counter CHECK (message_count = 0)")
    with pytest.raises(asyncpg.CheckViolationError):
        await chat.add_message(session["id"], "user", "question")
    assert await postgres_pool.fetchval("SELECT count(*) FROM chat_messages") == 0


@pytest.mark.asyncio
async def test_postgres_memory_vector_lookup_and_delete_require_owner(postgres_pool):
    dao = MemoryDAO()
    fact = await dao.create_user_fact("alice", "A remembered preference", embedding_id="vector-memory-id")
    assert (await dao.get_fact_by_embedding_id("vector-memory-id", "alice"))["id"] == fact["id"]
    assert await dao.get_fact_by_embedding_id("vector-memory-id", "bob") is None
    assert not await dao.delete_fact(fact["id"], "bob")
    assert await dao.get_fact_by_id(fact["id"]) is not None
    assert await dao.delete_fact(fact["id"], "alice")


@pytest.mark.asyncio
async def test_redis_rotation_is_single_use_and_logout_revokes(redis_store):
    manager = JWTManager(TEST_SECRET)
    user_id = "security-test-" + uuid.uuid4().hex
    access, refresh = manager.create_token_pair(user_id, "alice")
    await manager.store_refresh_token(user_id, refresh)
    try:
        results = await asyncio.gather(*(manager.refresh_access_token(refresh) for _ in range(8)))
        pairs = [result for result in results if result is not None]
        assert len(pairs) == 1
        new_access, new_refresh = pairs[0]
        assert await manager.refresh_access_token(refresh) is None
        assert not (await manager.verify_and_check_blacklist(new_refresh))[0]
        assert await manager.logout(new_access, user_id)
        assert not (await manager.verify_and_check_blacklist(new_access))[0]
        assert await manager.refresh_access_token(new_refresh) is None
    finally:
        await redis_store.delete(f"refresh_token:{user_id}")
        await redis_store.delete(manager._blacklist_key(access))
        if "new_access" in locals():
            await redis_store.delete(manager._blacklist_key(new_access))


@pytest.mark.asyncio
async def test_redis_quota_limits_concurrent_requests_without_consuming_reads(redis_store):
    limiter = SlidingWindowLimiter(window_size=60, max_requests=5)
    user_id = "quota-test-" + uuid.uuid4().hex
    try:
        results = await asyncio.gather(*(limiter.is_allowed(user_id, "api") for _ in range(20)))
        assert sum(allowed for allowed, count in results) == 5
        assert await limiter.get_remaining_requests(user_id, "api") == 0
        assert (await limiter.get_window_info(user_id, "api"))["current_requests"] == 5
        assert (await limiter.get_window_info(user_id, "api"))["current_requests"] == 5
    finally:
        await limiter.reset(user_id, "api")
