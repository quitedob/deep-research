"""JWT issuance and verification backed by persistent Redis security state."""

from datetime import datetime, timedelta, timezone
import hashlib
import math
import os
import secrets
from typing import Any, Dict, Optional, Tuple

import jwt

from backend.core.security.redis_client import redis_client, SecurityStoreUnavailableError


class JWTManager:
    def __init__(self, secret_key: Optional[str] = None):
        self._secret_key = secret_key
        self.algorithm = "HS256"
        self.access_token_expire = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")))
        self.refresh_token_expire = timedelta(days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")))

    @property
    def secret_key(self) -> str:
        secret = self._secret_key if self._secret_key is not None else os.getenv("JWT_SECRET_KEY", "")
        if len(secret.encode("utf-8")) < 32:
            raise ValueError("JWT_SECRET_KEY must be configured with at least 32 bytes")
        return secret

    def validate_configuration(self):
        _ = self.secret_key
        if self.access_token_expire.total_seconds() <= 0 or self.refresh_token_expire.total_seconds() <= 0:
            raise ValueError("Token expiration periods must be positive")

    def _create_token(self, user_id, username, token_type, lifetime, additional_claims=None):
        self.validate_configuration()
        now = datetime.now(timezone.utc)
        claims = dict(additional_claims or {})
        # Callers may add custom claims, but cannot replace identity or expiration.
        claims.update({
            "sub": user_id,
            "username": username,
            "type": token_type,
            "iat": now,
            "exp": now + lifetime,
            "jti": secrets.token_urlsafe(16),
        })
        return jwt.encode(claims, self.secret_key, algorithm=self.algorithm)

    def create_access_token(self, user_id: str, username: str, additional_claims=None) -> str:
        return self._create_token(user_id, username, "access", self.access_token_expire, additional_claims)

    def create_refresh_token(self, user_id: str, username: str) -> str:
        return self._create_token(user_id, username, "refresh", self.refresh_token_expire)

    def create_token_pair(self, user_id: str, username: str) -> Tuple[str, str]:
        return self.create_access_token(user_id, username), self.create_refresh_token(user_id, username)

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        secret = self.secret_key  # Invalid configuration is a server error, not an invalid user token.
        try:
            payload = jwt.decode(
                token, secret, algorithms=[self.algorithm],
                options={"require": ["sub", "username", "type", "exp", "iat"]},
            )
            if not isinstance(payload.get("sub"), str) or not payload["sub"]:
                return None
            if not isinstance(payload.get("username"), str) or not payload["username"]:
                return None
            return payload
        except jwt.InvalidTokenError:
            return None

    def verify_token(self, token: str, expected_type: str = "access"):
        payload = self.decode_token(token)
        if not payload or payload.get("type") != expected_type:
            return False, None
        return True, payload

    @staticmethod
    def _blacklist_key(token: str) -> str:
        return "blacklist:" + hashlib.sha256(token.encode("utf-8")).hexdigest()

    async def store_refresh_token(self, user_id: str, refresh_token: str, expire_seconds=None) -> bool:
        expire = expire_seconds or int(self.refresh_token_expire.total_seconds())
        saved = await redis_client.set(f"refresh_token:{user_id}", refresh_token, expire)
        if not saved:
            raise SecurityStoreUnavailableError("Refresh token could not be stored")
        return True

    async def get_refresh_token(self, user_id: str) -> Optional[str]:
        return await redis_client.get(f"refresh_token:{user_id}")

    async def revoke_refresh_token(self, user_id: str) -> bool:
        return await redis_client.delete(f"refresh_token:{user_id}")

    async def add_to_blacklist(self, token: str, expire_seconds=None) -> bool:
        payload = self.decode_token(token)
        if not payload:
            return False
        remaining = math.ceil(payload["exp"] - datetime.now(timezone.utc).timestamp())
        if remaining <= 0:
            return True
        return await redis_client.set(self._blacklist_key(token), "1", remaining)

    async def is_blacklisted(self, token: str) -> bool:
        # Honor revocations written by the previous release until their TTL expires.
        return await redis_client.exists(self._blacklist_key(token)) or await redis_client.exists(f"blacklist:{token}")

    async def refresh_access_token(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        valid, payload = await self.verify_and_check_blacklist(refresh_token, expected_type="refresh")
        if not valid:
            return None
        access, refresh = self.create_token_pair(payload["sub"], payload["username"])
        rotated = await redis_client.compare_and_set(
            f"refresh_token:{payload['sub']}", refresh_token, refresh,
            int(self.refresh_token_expire.total_seconds()),
        )
        return (access, refresh) if rotated else None

    async def logout(self, access_token: str, user_id: str) -> bool:
        valid, payload = self.verify_token(access_token)
        if not valid or payload["sub"] != user_id:
            return False
        revoked_access = await self.add_to_blacklist(access_token)
        revoked_refresh = await self.revoke_refresh_token(user_id)
        return revoked_access and revoked_refresh

    async def verify_and_check_blacklist(self, token: str, expected_type: str = "access"):
        valid, payload = self.verify_token(token, expected_type)
        if not valid or await self.is_blacklisted(token):
            return False, None
        return True, payload


jwt_manager = JWTManager()
