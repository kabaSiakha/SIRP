from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=200)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole = UserRole.REPORTER


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    email: EmailStr
    password: str
