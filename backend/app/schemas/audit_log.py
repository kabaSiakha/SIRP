from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class AuditLogBase(BaseModel):
    action: str
    entity_type: str
    entity_id: int
    details: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    user_id: int
    incident_id: Optional[int] = None
    ip_address: Optional[str] = None


class AuditLogResponse(AuditLogBase):
    id: int
    user_id: int
    incident_id: Optional[int]
    ip_address: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
