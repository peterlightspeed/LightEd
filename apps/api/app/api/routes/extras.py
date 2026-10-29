"""Notifications, class join codes, lesson resources + PDF import, password reset."""
import hashlib
import io
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.api.permissions import course_for_edit, lesson_for_edit
from app.core.config import settings
from app.core.ratelimit import RateLimiter
from app.core.security import hash_password
from app.db.session import get_db
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.extras import CourseJoinCode, LessonResource, LiveSession, Notification, PasswordReset
from app.models.lesson import Lesson
from app.models.user import User
from app.services.audit import record
from app.services.mailer import send_email
from app.services.notify import notify

router = APIRouter(tags=["extras"])


# ------------------------------------------------------------------ notifications
@router.get("/notifications")
def list_notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(
        select(Notification).where(Notification.user_id == user.id).order_by(Notification.id.desc()).limit(30)
    ).all()
    return {
        "unread": sum(1 for r in rows if not r.read),
        "items": [
            {"id": r.id, "kind": r.kind, "title": r.title, "body": r.body, "link": r.link, "read": r.read,
             "created_at": r.created_at.isoformat() if r.created_at else None}
            for r in rows
        ],
    }


@router.post("/notifications/read-all")
def mark_all_read(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    for n in db.scalars(select(Notification).where(Notification.user_id == user.id, Notification.read.is_(False))):
        n.read = True
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------------ class join codes
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O/1/I to avoid typos


def _new_code(db: Session) -> str:
    while True:
        code = "".join(secrets.choice(_ALPHABET) for _ in range(6))
        if not db.scalar(select(CourseJoinCode).where(CourseJoinCode.code == code)):
            return code


@router.get("/courses/{course_id}/join-code")
def get_join_code(course_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("teacher", "admin"))):
    course_for_edit(db, course_id, user)
    row = db.scalar(select(CourseJoinCode).where(CourseJoinCode.course_id == course_id))
    if not row:
        row = CourseJoinCode(course_id=course_id, code=_new_code(db))
        db.add(row)
        db.commit()
    return {"code": row.code}


@router.post("/courses/{course_id}/join-code/reset")
def reset_join_code(course_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("teacher", "admin"))):
    course_for_edit(db, course_id, user)
    row = db.scalar(select(CourseJoinCode).where(CourseJoinCode.course_id == course_id))
    if not row:
        row = CourseJoinCode(course_id=course_id, code=_new_code(db))
        db.add(row)
    else:
        row.code = _new_code(db)
    db.commit()
    return {"code": row.code}


class JoinRequest(BaseModel):
    code: str = Field(min_length=4, max_length=12)


@router.post("/courses/join", dependencies=[Depends(RateLimiter(20, 60, "join"))])
def join_with_code(payload: JoinRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.scalar(select(CourseJoinCode).where(CourseJoinCode.code == payload.code.strip().upper()))
    if not row:
        raise HTTPException(404, "That class code wasn't found. Check it and try again.")
    course = db.get(Course, row.course_id)
    if not db.scalar(select(Enrollment).where(Enrollment.user_id == user.id, Enrollment.course_id == course.id)):
        db.add(Enrollment(user_id=user.id, course_id=course.id))
        db.commit()
        notify(db, course.owner_id, "New student joined", f"{user.full_name} joined {course.title} with your class code.",
               kind="enrol", link="/students")
    return {"course_id": course.id, "title": course.title}


# ------------------------------------------------------------------ lesson resources (links)
class ResourceCreate(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    url: HttpUrl


@router.get("/lessons/{lesson_id}/resources")
def list_resources(lesson_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = db.scalars(select(LessonResource).where(LessonResource.lesson_id == lesson_id).order_by(LessonResource.id)).all()
    return [{"id": r.id, "title": r.title, "url": r.url} for r in rows]


@router.post("/lessons/{lesson_id}/resources", status_code=201)
def add_resource(lesson_id: int, payload: ResourceCreate, db: Session = Depends(get_db),
                 user: User = Depends(require_roles("teacher", "admin"))):
    lesson_for_edit(db, lesson_id, user)
    row = LessonResource(lesson_id=lesson_id, title=payload.title, url=str(payload.url))
    db.add(row)
    db.commit()
    return {"id": row.id, "title": row.title, "url": row.url}


@router.delete("/resources/{resource_id}")
def delete_resource(resource_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("teacher", "admin"))):
    row = db.get(LessonResource, resource_id)
    if not row:
        raise HTTPException(404, "Resource not found")
    lesson_for_edit(db, row.lesson_id, user)
    db.delete(row)
    db.commit()
    return {"ok": True}


MAX_PDF_BYTES = 5 * 1024 * 1024


@router.post("/materials/extract-pdf")
async def extract_pdf(file: UploadFile = File(...), user: User = Depends(require_roles("teacher", "admin"))):
    """Upload a PDF -> get its text back to review/edit as lesson content. The PDF itself is NOT stored."""
    data = await file.read(MAX_PDF_BYTES + 1)
    if len(data) > MAX_PDF_BYTES:
        raise HTTPException(413, "PDF is too large (max 5 MB).")
    if not data.startswith(b"%PDF"):
        raise HTTPException(400, "That file doesn't look like a PDF.")
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        text = "\n\n".join((p.extract_text() or "").strip() for p in reader.pages[:40]).strip()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, "Could not read this PDF (it may be scanned or protected).") from exc
    if not text:
        raise HTTPException(400, "No selectable text found. Scanned PDFs aren't supported yet.")
    return {"text": text[:30000], "pages": len(reader.pages)}


# ------------------------------------------------------------------ password reset
class ForgotRequest(BaseModel):
    email: str


class ResetRequest(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    password: str = Field(min_length=8, max_length=128)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@router.post("/auth/forgot-password", dependencies=[Depends(RateLimiter(5, 300, "reset-request"))])
def request_reset(payload: ForgotRequest, request: Request, background: BackgroundTasks, db: Session = Depends(get_db)):
    """Always answers the same way so emails can't be enumerated."""
    user = db.scalar(select(User).where(User.email == payload.email.strip().lower()))
    if user:
        token = secrets.token_urlsafe(32)
        db.add(PasswordReset(user_id=user.id, token_hash=_hash(token),
                             expires_at=datetime.now(timezone.utc) + timedelta(minutes=30)))
        db.commit()
        base = (settings.frontend_url or "http://localhost:3000").rstrip("/")
        link = f"{base}/reset-password?token={token}"
        background.add_task(send_email, user.email, "Reset your LightEd password",
                            f"Hi {user.full_name},\n\nUse this link to choose a new password (valid for 30 minutes):\n{link}\n\n"
                            "If you didn't ask for this, you can ignore this email.\n\nLightEd support: lightedsupport@gmail.com")
        record(db, "auth.reset_requested", user=user, request=request)
    return {"message": "If an account exists for that email, a reset link has been sent."}


@router.post("/auth/reset-password", dependencies=[Depends(RateLimiter(10, 300, "reset"))])
def reset_password(payload: ResetRequest, request: Request, db: Session = Depends(get_db)):
    row = db.scalar(select(PasswordReset).where(PasswordReset.token_hash == _hash(payload.token)))
    exp = row.expires_at if row else None
    if exp is not None and exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if not row or row.used or exp < datetime.now(timezone.utc):
        raise HTTPException(400, "This reset link is invalid or has expired. Please request a new one.")
    user = db.get(User, row.user_id)
    user.hashed_password = hash_password(payload.password)
    row.used = True
    db.commit()
    record(db, "auth.password_reset", user=user, request=request)
    return {"message": "Password updated. You can now log in."}


# ------------------------------------------------------------------ live classes
class SessionCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    starts_at: datetime
    duration_minutes: int = Field(default=60, ge=15, le=240)
    link: HttpUrl  # Google Meet / Zoom / Teams link pasted by the teacher


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _session_json(row: LiveSession, course_title: str | None = None) -> dict:
    start = _aware(row.starts_at)
    end = start + timedelta(minutes=row.duration_minutes)
    now = datetime.now(timezone.utc)
    # "live" opens 10 minutes before the start so students can walk in early.
    status = "ended" if now > end else "live" if now >= start - timedelta(minutes=10) else "upcoming"
    out = {"id": row.id, "course_id": row.course_id, "title": row.title, "starts_at": start.isoformat(),
           "duration_minutes": row.duration_minutes, "link": row.link, "status": status}
    if course_title:
        out["course_title"] = course_title
    return out


def _can_view_course(db: Session, course: Course, user: User) -> bool:
    if user.role == "admin" or course.owner_id == user.id:
        return True
    return bool(db.scalar(select(Enrollment).where(Enrollment.user_id == user.id, Enrollment.course_id == course.id)))


@router.get("/courses/{course_id}/sessions")
def list_sessions(course_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(404, "Course not found")
    if not _can_view_course(db, course, user):
        raise HTTPException(403, "Enrol in this course to see its live classes.")
    rows = db.scalars(select(LiveSession).where(LiveSession.course_id == course_id).order_by(LiveSession.starts_at)).all()
    items = [_session_json(r) for r in rows]
    # upcoming/live first (soonest first), then ended (most recent first)
    upcoming = [i for i in items if i["status"] != "ended"]
    ended = [i for i in items if i["status"] == "ended"][::-1]
    return upcoming + ended


@router.post("/courses/{course_id}/sessions", status_code=201)
def create_session(course_id: int, payload: SessionCreate, request: Request, db: Session = Depends(get_db),
                   user: User = Depends(require_roles("teacher", "admin"))):
    course = course_for_edit(db, course_id, user)
    if _aware(payload.starts_at) < datetime.now(timezone.utc) - timedelta(hours=1):
        raise HTTPException(400, "Choose a start time that is not in the past.")
    row = LiveSession(course_id=course_id, title=payload.title.strip(), starts_at=_aware(payload.starts_at),
                      duration_minutes=payload.duration_minutes, link=str(payload.link))
    db.add(row)
    db.commit()
    db.refresh(row)
    when = _aware(payload.starts_at).strftime("%d %b %Y, %H:%M UTC")
    for uid in db.scalars(select(Enrollment.user_id).where(Enrollment.course_id == course_id)):
        notify(db, uid, "Live class scheduled", f"{payload.title} ({course.title}) on {when}.", kind="live",
               link=f"/courses/{course_id}")
    record(db, "live.schedule", user=user, detail=f"course {course_id}: {payload.title}", request=request)
    return _session_json(row)


@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("teacher", "admin"))):
    row = db.get(LiveSession, session_id)
    if not row:
        raise HTTPException(404, "Session not found")
    course_for_edit(db, row.course_id, user)
    db.delete(row)
    db.commit()
    return {"ok": True}


@router.get("/sessions/upcoming")
def upcoming_sessions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Next live classes (next 14 days + ones in progress) across the user's courses."""
    if user.role == "student":
        cids = list(db.scalars(select(Enrollment.course_id).where(Enrollment.user_id == user.id)))
    elif user.role == "teacher":
        cids = list(db.scalars(select(Course.id).where(Course.owner_id == user.id)))
    else:
        cids = list(db.scalars(select(Course.id)))
    now = datetime.now(timezone.utc)
    rows = db.execute(
        select(LiveSession, Course.title).join(Course, Course.id == LiveSession.course_id)
        .where(LiveSession.course_id.in_(cids or [-1]), LiveSession.starts_at >= now - timedelta(hours=4),
               LiveSession.starts_at <= now + timedelta(days=14))
        .order_by(LiveSession.starts_at)
    ).all()
    items = [_session_json(r, t) for r, t in rows]
    return [i for i in items if i["status"] != "ended"][:5]
