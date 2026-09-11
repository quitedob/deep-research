"""Salted password hashes, with verification for pre-migration SHA-256 hashes."""

import hashlib
import hmac
import re
import secrets


PASSWORD_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def is_legacy_password_hash(password_hash: str) -> bool:
    return isinstance(password_hash, str) and bool(re.fullmatch(r"[0-9a-f]{64}", password_hash))


def verify_password(password: str, password_hash: str) -> bool:
    if is_legacy_password_hash(password_hash):
        digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(digest, password_hash)
    try:
        algorithm, iterations_text, salt_hex, digest_hex = password_hash.split("$")
        iterations = int(iterations_text)
        if algorithm != "pbkdf2_sha256" or not PASSWORD_ITERATIONS <= iterations <= 2_000_000:
            return False
        salt, expected = bytes.fromhex(salt_hex), bytes.fromhex(digest_hex)
        if len(salt) != 16 or len(expected) != 32:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(actual, expected)
    except (AttributeError, TypeError, ValueError):
        return False
