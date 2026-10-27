"""First-party password, access-token, and refresh-session primitives."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

INVALID_ACCESS_MESSAGE = "Invalid access token"


ISSUER = os.getenv("AUTH_JWT_ISSUER", "https://neurolab.local")
AUDIENCE = os.getenv("AUTH_JWT_AUDIENCE", "neurolab-web")
ACCESS_TOKEN_SECONDS = 12 * 60
REFRESH_TOKEN_SECONDS = 14 * 24 * 60 * 60
MAX_PASSWORD_LENGTH = 1024
PASSWORD_HASHER = PasswordHasher()


class AuthenticationError(ValueError):
    """An intentionally generic authentication or token validation failure."""


def normalize_email(email: str) -> str:
    return email.strip().casefold()


def validate_password(password: str) -> None:
    if not 12 <= len(password) <= MAX_PASSWORD_LENGTH:
        raise ValueError("Password must contain between 12 and 1024 characters.")


def hash_password(password: str) -> str:
    validate_password(password)
    return PASSWORD_HASHER.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    if len(password) > MAX_PASSWORD_LENGTH:
        return False
    try:
        return PASSWORD_HASHER.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def _parse_key_material(
    configured: str, kid: str, production: bool
) -> tuple[Ed25519PrivateKey, bytes, str]:
    if configured:
        key = serialization.load_pem_private_key(configured.encode("utf-8"), password=None)
        if not isinstance(key, Ed25519PrivateKey):
            raise RuntimeError("AUTH_ED25519_PRIVATE_KEY must contain an Ed25519 private key")
    else:
        if production:
            raise RuntimeError("Production requires AUTH_ED25519_PRIVATE_KEY")
        key = Ed25519PrivateKey.generate()
    public_key = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return key, public_key, kid


@lru_cache(maxsize=4)
def _cached_key_material(
    configured: str, kid: str, production: bool
) -> tuple[Ed25519PrivateKey, bytes, str]:
    return _parse_key_material(configured, kid, production)


def _key_material() -> tuple[Ed25519PrivateKey, bytes, str]:
    configured = os.getenv("AUTH_ED25519_PRIVATE_KEY", "").replace("\\n", "\n").strip()
    kid = os.getenv("AUTH_JWT_KID", "local-ed25519-v1").strip()
    production = os.getenv("APP_ENV", "development").strip().lower() == "production"
    return _cached_key_material(configured, kid, production)


def _token_pepper() -> bytes:
    value = os.getenv("AUTH_TOKEN_PEPPER", "").encode("utf-8")
    if len(value) >= 32:
        return value
    if os.getenv("APP_ENV", "development").strip().lower() == "production":
        raise RuntimeError("Production requires AUTH_TOKEN_PEPPER with at least 32 characters")
    return b"neurolab-local-development-token-pepper-not-for-production"


def keyed_hash(value: str) -> str:
    return hmac.new(_token_pepper(), value.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_keyed_hash(value: str, expected: str) -> bool:
    return hmac.compare_digest(keyed_hash(value), expected)


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def issue_access_token(user_id: str, session_id: str, *, now: datetime | None = None) -> str:
    current = now or datetime.now(UTC)
    private_key, _public_key, kid = _key_material()
    claims = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": user_id,
        "sid": session_id,
        "iat": int(current.timestamp()),
        "nbf": int(current.timestamp()),
        "exp": int((current + timedelta(seconds=ACCESS_TOKEN_SECONDS)).timestamp()),
        "jti": str(uuid.uuid4()),
        "token_type": "access",
    }
    return jwt.encode(claims, private_key, algorithm="EdDSA", headers={"kid": kid, "typ": "JWT"})


def decode_access_token(token: str, *, now: datetime | None = None) -> dict[str, Any]:
    _private_key, public_key, kid = _key_material()
    try:
        header = jwt.get_unverified_header(token)
        if header.get("alg") != "EdDSA" or header.get("kid") != kid or header.get("typ") != "JWT":
            raise AuthenticationError(INVALID_ACCESS_MESSAGE)
        # PyJWT's clock is patched in tests if boundary-time behavior needs checking.
        claims = jwt.decode(
            token,
            public_key,
            algorithms=["EdDSA"],
            issuer=ISSUER,
            audience=AUDIENCE,
            leeway=15,
            options={
                "require": ["iss", "aud", "sub", "sid", "iat", "nbf", "exp", "jti", "token_type"]
            },
        )
    except (jwt.PyJWTError, TypeError, ValueError) as exc:
        raise AuthenticationError(INVALID_ACCESS_MESSAGE) from exc
    if claims.get("token_type") != "access":
        raise AuthenticationError(INVALID_ACCESS_MESSAGE)
    if now is not None:
        timestamp = int(now.timestamp())
        if (
            claims.get("nbf", timestamp + 1) > timestamp + 15
            or claims.get("exp", 0) < timestamp - 15
        ):
            raise AuthenticationError(INVALID_ACCESS_MESSAGE)
    return claims


def new_session_expiry(*, now: datetime | None = None) -> str:
    current = now or datetime.now(UTC)
    return (current + timedelta(seconds=REFRESH_TOKEN_SECONDS)).isoformat().replace("+00:00", "Z")


def session_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def assert_production_auth_config() -> None:
    if os.getenv("APP_ENV", "development").strip().lower() != "production":
        return
    if not os.getenv("AUTH_ED25519_PRIVATE_KEY", "").strip():
        raise RuntimeError("Production requires AUTH_ED25519_PRIVATE_KEY")
    if len(os.getenv("AUTH_TOKEN_PEPPER", "").encode("utf-8")) < 32:
        raise RuntimeError("Production requires AUTH_TOKEN_PEPPER with at least 32 characters")
    if len(os.getenv("AUTH_JWT_KID", "").strip()) < 1:
        raise RuntimeError("Production requires AUTH_JWT_KID")
