import uuid
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, func, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.postgres import Base

class IrrigationSchedule(Base):
    """
    Represents a planned or executed irrigation event.
    """
    __tablename__ = "irrigation_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"), nullable=False, index=True)
    source = Column(String, nullable=False, default="ai")  # ai | manual | rule
    
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    duration_min = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="pending")
    executed_at = Column(DateTime(timezone=True))
    celery_task_id = Column(String)

    # Relationships
    zone = relationship("Zone", back_populates="irrigation_schedules")

    def __repr__(self):
        return f"<IrrigationSchedule(id='{self.id}', status='{self.status}')>"
