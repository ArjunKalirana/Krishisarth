import uuid
from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey, func, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.postgres import Base

class Device(Base):
    """
    Represents an IoT device in a zone.
    """
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String, nullable=False)  # sensor | gateway | actuator
    serial_no = Column(String, nullable=False, unique=True, index=True)
    firmware_ver = Column(String)
    battery_pct = Column(Integer)
    is_online = Column(Boolean, nullable=False, default=False)
    last_seen = Column(DateTime(timezone=True))

    # Relationships
    zone = relationship("Zone", back_populates="devices")

    def __repr__(self):
        return f"<Device(id='{self.id}', serial='{self.serial_no}')>"
