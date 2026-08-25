from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")
    incident = relationship("Incident", back_populates="audit_logs")
