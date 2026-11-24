"""
User Management Schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", description="Valid email address format")
    role: str = Field(default="soc_analyst")
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="User password must be at least 8 characters")
    organization_id: Optional[str] = None


class UserUpdateRole(BaseModel):
    role: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    is_active: bool
    is_verified: bool
    organization_id: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
