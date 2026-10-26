from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)
    role: str = "student"  # student | teacher (admin is seeded only)


class UserOut(UserBase):
    id: int
    role: str
    avatar_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserAdminOut(UserOut):
    """Extra fields for the admin shell."""

    course_count: int = 0
