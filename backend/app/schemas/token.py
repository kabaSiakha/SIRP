from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class Token(BaseModel):
    """Schéma de réponse pour les tokens JWT"""
    access_token: str = Field(
        ...,
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    refresh_token: str = Field(
        ...,
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    token_type: str = Field(default="bearer", examples=["bearer"])

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwicm9sZSI6ImFkbWluIn0...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidHlwZSI6InJlZnJlc2gifQ...",
                "token_type": "bearer"
            }
        }
    )


class TokenPayload(BaseModel):
    """Payload décodé d'un token JWT"""
    sub: Optional[int] = Field(None, description="ID de l'utilisateur")
    role: Optional[str] = Field(None, description="Rôle de l'utilisateur")
