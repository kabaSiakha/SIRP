from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict

from app.models.incident import IncidentSeverity, IncidentStatus, IncidentCategory


class IncidentBase(BaseModel):
    title: str = Field(
        ...,
        min_length=5,
        max_length=300,
        examples=["Tentative de phishing détectée"]
    )
    description: str = Field(
        ...,
        min_length=10,
        examples=["Plusieurs employés ont reçu des emails suspects demandant leurs identifiants."]
    )
    severity: IncidentSeverity = Field(..., examples=["high"])
    category: IncidentCategory = Field(..., examples=["phishing"])


class IncidentCreate(IncidentBase):
    """Schéma pour la création d'un incident"""
    assigned_to: Optional[int] = Field(None, examples=[2])

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Tentative de phishing détectée",
                "description": "Plusieurs employés ont reçu des emails suspects demandant leurs identifiants.",
                "severity": "high",
                "category": "phishing",
                "assigned_to": 2
            }
        }
    )


class IncidentUpdate(BaseModel):
    """Schéma pour la mise à jour d'un incident"""
    title: Optional[str] = Field(None, min_length=5, max_length=300)
    description: Optional[str] = Field(None, min_length=10)
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None
    category: Optional[IncidentCategory] = None
    assigned_to: Optional[int] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Phishing confirmé - campagne massive",
                "severity": "critical"
            }
        }
    )


class IncidentResponse(IncidentBase):
    """Schéma de réponse pour un incident"""
    id: int
    status: IncidentStatus
    created_by: int
    assigned_to: Optional[int]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "title": "Tentative de phishing détectée",
                "description": "Plusieurs employés ont reçu des emails suspects.",
                "severity": "high",
                "category": "phishing",
                "status": "open",
                "created_by": 1,
                "assigned_to": 2,
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00",
                "resolved_at": None,
                "closed_at": None
            }
        }
    )


class IncidentListResponse(BaseModel):
    """Schéma de réponse pour une liste d'incidents paginée"""
    items: List[IncidentResponse]
    total: int = Field(..., examples=[42])
    page: int = Field(..., examples=[1])
    page_size: int = Field(..., examples=[20])

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": 1,
                        "title": "Tentative de phishing",
                        "description": "Emails suspects détectés",
                        "severity": "high",
                        "category": "phishing",
                        "status": "open",
                        "created_by": 1,
                        "assigned_to": 2,
                        "created_at": "2024-01-15T10:30:00",
                        "updated_at": "2024-01-15T10:30:00",
                        "resolved_at": None,
                        "closed_at": None
                    }
                ],
                "total": 42,
                "page": 1,
                "page_size": 20
            }
        }
    )
