"""Authentication routes.

JWT access + refresh tokens. Google OAuth is intentionally a clearly-marked
placeholder so the MVP is not blocked on provider setup.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    Token,
)
from app.schemas.user import UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

ALLOWED_SIGNUP_ROLES = {"student", "teacher"}


def _issue(user: User) -> Token:
    """Build the token bundle returned by register/login/refresh."""
    return Token(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=UserOut.model_validate(user),
    )


@router.post("/register", response_model=Token, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if payload.role not in ALLOWED_SIGNUP_ROLES:
        raise HTTPException(400, "Role must be 'student' or 'teacher'")
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(400, "Email already registered")

    user = User(
        full_name=payload.full_name,
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue(user)


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    return _issue(user)


@router.post("/refresh", response_model=Token)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if not data or data.get("type") != "refresh":
        raise HTTPException(401, "Invalid refresh token")
    user = db.get(User, int(data["sub"]))
    if not user:
        raise HTTPException(401, "User no longer exists")
    return _issue(user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """MVP: always returns 200 so the endpoint cannot be used to enumerate emails.

    TODO: generate a signed reset token and email it (SendGrid/Resend).
    """
    db.scalar(select(User).where(User.email == payload.email.lower()))
    return MessageResponse(
        message="If an account exists for that email, a reset link has been sent."
    )


@router.post("/google", status_code=501)
def google_login():
    """Placeholder for Google OAuth.

    Integration plan (see GUIDE.md):
      1. Frontend obtains a Google ID token via Google Identity Services.
      2. POST it here.
      3. Verify with google-auth, find/create the user, then call `_issue(user)`.
    """
    raise HTTPException(
        status_code=501,
        detail="Google sign-in is not enabled yet. Use email/password for now.",
    )
