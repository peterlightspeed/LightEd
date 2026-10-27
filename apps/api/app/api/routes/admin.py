"""Minimal admin routes.

The admin shell in the UI only needs a user list, role changes and course
publishing for the MVP.

Both mutations accept a **JSON body** (not query params) because that is what the
Next.js client sends via `api.patch(path, body)`. Keeping the contract in one
place avoids the classic "422 Field required: query.role" mismatch.
"""
from fastapi import Request
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.services.audit import record
from app.models.audit import AuditLog
from app.api.deps import require_roles
from app.db.session import get_db
from app.models.course import Course
from app.models.user import User
from app.schemas.user import UserOut

router = APIRouter(prefix="/admin", tags=["admin"])

VALID_ROLES = {"student", "teacher", "admin"}


class RoleUpdate(BaseModel):
    """Body for PATCH /admin/users/{id}/role."""

    role: str = Field(..., description="student | teacher | admin")


class PublishUpdate(BaseModel):
    """Body for PATCH /admin/courses/{id}/publish."""

    published: bool = True


class PublishOut(BaseModel):
    id: int
    published: bool


@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    return db.scalars(select(User).order_by(User.id)).all()


@router.patch("/users/{user_id}/role", response_model=UserOut)
def update_role(
    user_id: int,
    payload: RoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    if payload.role not in VALID_ROLES:
        raise HTTPException(400, f"Invalid role. Expected one of {sorted(VALID_ROLES)}")
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404, "User not found")
    old = target.role
    target.role = payload.role
    db.commit()
    record(db, "admin.role_change", user=user, detail=f"{target.email}: {old} -> {payload.role}", request=request)
    db.refresh(target)
    return target


@router.patch("/courses/{course_id}/publish", response_model=PublishOut)
def toggle_publish(
    course_id: int,
    payload: PublishUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(404, "Course not found")
    course.published = payload.published
    db.commit()
    record(db, "admin.course_publish", user=user, detail=f"course {course.id} published={payload.published}", request=request)
    return PublishOut(id=course.id, published=course.published)


@router.get("/audit")
def audit_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    """Most recent security/admin events (PDF FR-24)."""
    rows = db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(max(1, min(limit, 200)))).all()
    return [
        {"id": r.id, "action": r.action, "actor": r.actor, "detail": r.detail, "ip": r.ip_address,
         "created_at": r.created_at.isoformat() if r.created_at else None}
        for r in rows
    ]
