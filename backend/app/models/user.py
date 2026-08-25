import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    REPORTER = "reporter"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.REPORTER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    incidents_created = relationship("Incident", back_populates="creator", foreign_keys="Incident.created_by")
    incidents_assigned = relationship("Incident", back_populates="assignee", foreign_keys="Incident.assigned_to")
    comments = relationship("Comment", back_populates="author")
    audit_logs = relationship("AuditLog", back_populates="user")
