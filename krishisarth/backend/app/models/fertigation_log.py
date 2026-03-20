import uuid
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, func, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.postgres import Base

class FertigationLog(Base):
    """
    Represents a nutrient injection event.
    """
    __tablename__ = "fertigation_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"), nullable=False, index=True)
    
    nutrient_type = Column(String, nullable=False)
    concentration_ml = Column(Float, nullable=False)
    ec_before = Column(Float)
    ec_after = Column(Float)
    status = Column(String, nullable=False, default="completed")
    applied_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    zone = relationship("Zone", back_populates="fertigation_logs")

    def __repr__(self):
        return f"<FertigationLog(id='{self.id}', nutrient='{self.nutrient_type}')>"
