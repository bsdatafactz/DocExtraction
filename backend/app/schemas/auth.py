from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class SignupRequest(BaseModel):
    # No role field — role is never client-supplied. See auth.py:signup().
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserSummary(BaseModel):
    id: int
    email: str
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    user: UserSummary


class RoleUpdateRequest(BaseModel):
    role: UserRole
