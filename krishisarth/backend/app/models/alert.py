import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, func, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.postgres import Base

class Alert(Base):
    """
    Represents a system notification or alarm.
    """
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id", ondelete="SET NULL"), nullable=True, index=True)
    
    severity = Column(String, nullable=False)  # critical | warning | info
    type = Column(String, nullable=False)      # SENSOR_FAULT | PUMP_FAILURE | LEAK_DETECTED
    message = Column(String, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    farm = relationship("Farm", back_populates="alerts")
    zone = relationship("Zone", back_populates="alerts")

    def __repr__(self):
        return f"<Alert(id='{self.id}', type='{self.type}')>"
