from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr = Field(..., examples=["analyst@sirp.com"])
    username: str = Field(..., min_length=3, max_length=100, examples=["analyst"])
    full_name: str = Field(..., min_length=1, max_length=200, examples=["Jean Dupont"])


class UserCreate(UserBase):
    """Schéma pour la création d'un utilisateur"""
    password: str = Field(..., min_length=8, max_length=100, examples=["SecurePass123!"])
    role: UserRole = Field(default=UserRole.REPORTER, examples=["analyst"])

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "analyst@sirp.com",
                "username": "analyst",
                "full_name": "Jean Dupont",
                "password": "SecurePass123!",
                "role": "analyst"
            }
        }
    )


class UserUpdate(BaseModel):
    """Schéma pour la mise à jour d'un utilisateur"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "Jean Dupont Updated",
                "role": "admin"
            }
        }
    )


class UserResponse(UserBase):
    """Schéma de réponse pour un utilisateur"""
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "analyst@sirp.com",
                "username": "analyst",
                "full_name": "Jean Dupont",
                "role": "analyst",
                "is_active": True,
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }
    )


class UserLogin(BaseModel):
    """Schéma pour la connexion"""
    email: EmailStr = Field(..., examples=["analyst@sirp.com"])
    password: str = Field(..., examples=["SecurePass123!"])
