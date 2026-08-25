from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from app.models.incident import IncidentSeverity, IncidentStatus, IncidentCategory


class IncidentBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=300)
    description: str = Field(..., min_length=10)
    severity: IncidentSeverity
    category: IncidentCategory


class IncidentCreate(IncidentBase):
    assigned_to: Optional[int] = None


class IncidentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=300)
    description: Optional[str] = Field(None, min_length=10)
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None
    category: Optional[IncidentCategory] = None
    assigned_to: Optional[int] = None


class IncidentResponse(IncidentBase):
    id: int
    status: IncidentStatus
    created_by: int
    assigned_to: Optional[int]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class IncidentListResponse(BaseModel):
    items: List[IncidentResponse]
    total: int
    page: int
    page_size: int
