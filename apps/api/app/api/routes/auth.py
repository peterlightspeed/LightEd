"""Authentication routes.

JWT access + refresh tokens. Google OAuth is intentionally a clearly-marked
placeholder so the MVP is not blocked on provider setup.
"""
import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
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
    GoogleLoginRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    Token,
)
from app.schemas.user import UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

ALLOWED_SIGNUP_ROLES = {"student", "teacher"}
logger = logging.getLogger("lighted.auth")


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
    if db.scalar(select(User).where(User.email == payload.email.lower())):
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
    if user and not user.hashed_password:
        # Account was created with Google and has no password.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "This account uses Google sign-in. Click 'Continue with Google'.")
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


@router.get("/providers")
def providers():
    """Tells the frontend which social logins are enabled (so only the backend needs the Google client id)."""
    return {"google_client_id": settings.google_client_id}


GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


def verify_google_credential(credential: str) -> dict:
    """Validate a Google ID token and return its claims.

    Uses Google's official tokeninfo endpoint (fine for MVP traffic). We check the
    audience matches OUR client id and that the email is verified.
    For high traffic, switch to the `google-auth` library to verify offline.
    """
    try:
        res = httpx.get(GOOGLE_TOKENINFO_URL, params={"id_token": credential}, timeout=8)
    except httpx.HTTPError as exc:
        logger.warning("Google tokeninfo unreachable: %s", exc)
        raise HTTPException(503, "Could not reach Google. Please try again.") from exc
    if res.status_code != 200:
        raise HTTPException(401, "Invalid Google sign-in. Please try again.")
    claims = res.json()
    if claims.get("aud") != settings.google_client_id:
        raise HTTPException(401, "Google sign-in was issued for a different app.")
    if str(claims.get("email_verified")).lower() != "true":
        raise HTTPException(401, "Your Google email is not verified.")
    return claims


@router.post("/google", response_model=Token)
def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    """Sign in / sign up with Google.

    Flow: frontend gets an ID token from Google Identity Services -> POSTs it here ->
    we verify it, find-or-create the user, and return OUR normal JWT bundle.
    Existing email accounts are linked automatically (Google verified the email).
    """
    if not settings.google_client_id:
        raise HTTPException(501, "Google sign-in is not configured on the server (set GOOGLE_CLIENT_ID).")

    claims = verify_google_credential(payload.credential)
    email = str(claims["email"]).lower()
    user = db.scalar(select(User).where(User.email == email))

    if not user:
        role = payload.role if payload.role in ALLOWED_SIGNUP_ROLES else "student"
        user = User(
            full_name=(claims.get("name") or email.split("@")[0])[:120],
            email=email,
            hashed_password=None,  # Google users have no password
            role=role,
            avatar_url=claims.get("picture"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif not user.avatar_url and claims.get("picture"):
        user.avatar_url = claims["picture"]
        db.commit()
    return _issue(user)
