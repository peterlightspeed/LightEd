"""Create in-app notifications. Never raises (a failed notification must not break the action)."""
import logging

from sqlalchemy.orm import Session

from app.models.extras import Notification

logger = logging.getLogger("lighted.notify")


def notify(db: Session, user_id: int, title: str, body: str = "", *, kind: str = "info", link: str = "") -> None:
    try:
        db.add(Notification(user_id=user_id, kind=kind, title=title[:160], body=body[:300], link=link[:200]))
        db.commit()
    except Exception:  # noqa: BLE001
        db.rollback()
        logger.exception("notification failed")
