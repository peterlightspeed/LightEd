"""Minimal admin routes.

The admin shell in the UI only needs a user list and role changes for the MVP.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.course import Course
from app.models.user import User
from app.schemas.user import UserOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    return db.scalars(select(User).order_by(User.id)).all()


@router.patch("/users/{user_id}/role", response_model=UserOut)
def update_role(
    user_id: int,
    role: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    if role not in {"student", "teacher", "admin"}:
        raise HTTPException(400, "Invalid role")
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404, "User not found")
    target.role = role
    db.commit()
    db.refresh(target)
    return target


@router.patch("/courses/{course_id}/publish", response_model=dict)
def toggle_publish(
    course_id: int,
    published: bool = True,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(404, "Course not found")
    course.published = published
    db.commit()
    return {"id": course.id, "published": course.published}
