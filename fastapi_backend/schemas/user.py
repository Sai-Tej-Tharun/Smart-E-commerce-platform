"""
schemas/user.py
------------------
Pydantic request/response models for auth + user endpoints.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from models.user import UserRole


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class SocialLoginRequest(BaseModel):
    # ID token issued by Auth0 after a successful Google/Facebook login on the frontend
    auth0_id_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
