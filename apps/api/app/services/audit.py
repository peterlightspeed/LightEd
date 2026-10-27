"""Tiny helper to record audit events. Never raises: auditing must not break a request."""
import logging

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit import AuditLog

logger = logging.getLogger("lighted.audit")


def record(db: Session, action: str, *, user=None, actor: str = "", detail: str = "", request: Request | None = None) -> None:
    try:
        ip = ""
        if request is not None:
            # Behind Render/Vercel proxies the real client IP is the first X-Forwarded-For entry.
            fwd = request.headers.get("x-forwarded-for", "")
            ip = (fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else ""))[:64]
        db.add(
            AuditLog(
                user_id=getattr(user, "id", None),
                actor=(getattr(user, "email", None) or actor)[:160],
                action=action,
                detail=detail[:300],
                ip_address=ip,
            )
        )
        db.commit()
    except Exception:  # noqa: BLE001
        db.rollback()
        logger.exception("audit write failed for %s", action)
