"""Password hashing + JWT helpers.

Only symmetric HS256 JWTs are used for the MVP. When Google OAuth is added,
the same access-token format can be issued after verifying the Google ID token,
so the rest of the app does not need to change.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str | None) -> bool:
    if not hashed:
        return False
    return pwd_context.verify(plain, hashed)


def _encode(subject: str | int, expires: timedelta, token_type: str) -> str:
    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": datetime.now(timezone.utc) + expires,
        "type": token_type,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str | int, expires_minutes: int | None = None) -> str:
    return _encode(
        subject,
        timedelta(minutes=expires_minutes or settings.access_token_expire_minutes),
        "access",
    )


def create_refresh_token(subject: str | int) -> str:
    return _encode(subject, timedelta(days=settings.refresh_token_expire_days), "refresh")


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
