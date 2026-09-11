"""Create missing schema objects and reject incompatible schemas without deleting data."""

import asyncio
import logging
import os
from backend.repositories.base import utc_now
from urllib.parse import urlsplit, urlunsplit

import asyncpg

from backend.repositories.db_config import db_config
from backend.repositories.db_schema import ALL_TABLES, TABLE_SCHEMAS

logger = logging.getLogger(__name__)


class SchemaMismatchError(RuntimeError):
    """An explicit, reviewed migration is needed before this application can start."""


class DatabaseInitializer:
    def __init__(self):
        self.config = db_config

    def _admin_dsn(self):
        parts = urlsplit(self.config.get_dsn())
        return urlunsplit(parts._replace(path="/postgres"))

    async def check_and_init_database(self) -> bool:
        valid, error = self.config.validate()
        if not valid:
            raise ValueError(error)
        if not await self._check_database_exists():
            await self._create_database()
        await self._check_and_init_tables()
        logger.info("Database initialization completed")
        return True

    async def _check_database_exists(self) -> bool:
        conn = await asyncpg.connect(self._admin_dsn())
        try:
            result = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1", self.config.database
            )
            return result is not None
        finally:
            await conn.close()

    async def _create_database(self) -> bool:
        conn = await asyncpg.connect(self._admin_dsn())
        try:
            # PostgreSQL identifiers cannot be bound as query parameters.
            name = self.config.database.replace('"', '""')
            await conn.execute(f'CREATE DATABASE "{name}"')
            return True
        finally:
            await conn.close()

    async def _check_and_init_tables(self):
        conn = await asyncpg.connect(
            self.config.get_dsn(), server_settings={"timezone": "UTC"}
        )
        try:
            async with conn.transaction():
                for table_name, create_sql in ALL_TABLES.items():
                    if await self._table_exists(conn, table_name):
                        if not await self._validate_table_schema(conn, table_name):
                            raise SchemaMismatchError(
                                f"Table {table_name!r} is incompatible; apply an explicit migration. "
                                "Existing data has not been deleted."
                            )
                    else:
                        await self._create_table(conn, table_name, create_sql)
                if os.getenv("ENABLE_TEST_USERS", "false").lower() == "true":
                    await self._create_test_users(conn)
        finally:
            await conn.close()

    async def _table_exists(self, conn, table_name: str) -> bool:
        return await conn.fetchval(
            """SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = $1
            )""", table_name,
        )

    async def _validate_table_schema(self, conn, table_name: str) -> bool:
        expected = TABLE_SCHEMAS.get(table_name)
        if expected is None:
            return True
        columns = await conn.fetch(
            """SELECT column_name, data_type, udt_name
               FROM information_schema.columns
               WHERE table_schema = 'public' AND table_name = $1""", table_name,
        )
        actual = {column["column_name"]: column for column in columns}
        for name, expected_type in expected["columns"].items():
            column = actual.get(name)
            if column is None or not self._types_match(expected_type, column["data_type"]):
                logger.error("Schema mismatch in %s.%s: expected %s", table_name, name, expected_type)
                return False
            if table_name == "research_citations" and name == "authors" and column["udt_name"] != "_text":
                logger.error("research_citations.authors must be TEXT[]")
                return False
        return True

    @staticmethod
    def _types_match(expected: str, actual: str) -> bool:
        aliases = {
            "character varying": {"character varying", "varchar", "text"},
            "text": {"text", "character varying"},
            "integer": {"integer", "int", "int4"},
            "double precision": {"double precision", "float8"},
            "timestamp without time zone": {"timestamp without time zone", "timestamp"},
        }
        return actual.lower() in aliases.get(expected.lower(), {expected.lower()})

    async def _create_table(self, conn, table_name: str, create_sql: str):
        await conn.execute(create_sql)
        logger.info("Created table %s", table_name)

    async def _create_test_users(self, conn):
        if os.getenv("ENABLE_TEST_USERS", "false").lower() != "true":
            return
        if os.getenv("APP_ENV", "production").lower() not in {"development", "test"}:
            raise ValueError("Test users are permitted only in APP_ENV=development or test")
        password = os.getenv("TEST_USER_PASSWORD", "")
        if len(password) < 12:
            raise ValueError("Set TEST_USER_PASSWORD to at least 12 characters when enabling test users")
        from backend.core.security.passwords import hash_password
        for username in ("demo_user_001", "demo_user_002", "demo_user_003", "test_user"):
            password_hash = await asyncio.to_thread(hash_password, password)
            await conn.execute(
                """INSERT INTO users
                   (id, username, email, password_hash, full_name, created_at, updated_at)
                   VALUES ($1, $1, $2, $3, $1, $4, $4)
                   ON CONFLICT (id) DO NOTHING""",
                username, f"{username}@example.com", password_hash, utc_now(),
            )
            await conn.execute(
                """INSERT INTO user_preferences (user_id, default_llm_provider, default_model)
                   VALUES ($1, 'deepseek', 'deepseek-flash')
                   ON CONFLICT (user_id) DO NOTHING""", username,
            )


db_initializer = DatabaseInitializer()


async def init_database() -> bool:
    return await db_initializer.check_and_init_database()
