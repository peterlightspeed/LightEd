"""Shared FastAPI dependencies: DB session, current user, role guards."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User

# auto_error=False lets us support public endpoints that optionally personalise
# their response (e.g. course list shows "enrolled" when logged in).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def _user_from_token(token: str | None, db: Session, expected_type: str) -> User | None:
    if not token:
        return None
    payload = decode_token(token)
    if not payload or payload.get("type") != expected_type:
        return None
    try:
        user_id = int(payload.get("sub", 0))
    except (TypeError, ValueError):
        return None
    return db.get(User, user_id)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    user = _user_from_token(token, db, "access")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_optional_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    return _user_from_token(token, db, "access")


def require_roles(*roles: str):
    """Dependency factory for role-based access control."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return checker
