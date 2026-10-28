"""Send email through SMTP (stdlib only). Without SMTP settings it just logs the message,
so password reset still works in development (copy the link from the server log)."""
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger("lighted.mail")


def send_email(to: str, subject: str, body: str) -> bool:
    if not settings.smtp_host:
        logger.warning("SMTP not configured. Email to %s | %s\n%s", to, subject, body)
        return False
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = settings.smtp_from, to, subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as s:
            s.starttls()
            if settings.smtp_user:
                s.login(settings.smtp_user, settings.smtp_password or "")
            s.send_message(msg)
        return True
    except Exception:  # noqa: BLE001
        logger.exception("email send failed")
        return False
