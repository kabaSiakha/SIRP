from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CommentBase(BaseModel):
    content: str = Field(..., min_length=1)


class CommentCreate(CommentBase):
    incident_id: int


class CommentUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1)


class CommentResponse(CommentBase):
    id: int
    incident_id: int
    author_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
