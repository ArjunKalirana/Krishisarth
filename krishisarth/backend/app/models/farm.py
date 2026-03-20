import uuid
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, func, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.postgres import Base

class Farm(Base):
    """
    Represents a geographic farm boundary belonging to a farmer.
    """
    __tablename__ = "farms"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    farmer_id = Column(UUID(as_uuid=True), ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    lat = Column(Float)
    lng = Column(Float)
    area_ha = Column(Float)
    soil_type = Column(String)
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    farmer = relationship("Farmer", back_populates="farms")
    zones = relationship("Zone", back_populates="farm", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="farm", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Farm(id='{self.id}', name='{self.name}')>"
