from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str | None = None
    type: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str
