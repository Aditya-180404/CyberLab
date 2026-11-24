"""
Authentication Schemas
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username for authentication")
    password: str = Field(..., min_length=6, description="Plaintext password")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: Dict[str, Any]


class TokenPayload(BaseModel):
    sub: str
    username: str
    role: str
    exp: int
    iss: str
    aud: str
