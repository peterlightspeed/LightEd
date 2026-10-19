from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    full_name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str
    role: str = "student"


class UserOut(UserBase):
    id: int
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}
