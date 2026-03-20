import uuid
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, func, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.postgres import Base

class AIDecision(Base):
    """
    Represents a reasoning step and decision by the AI engine.
    """
    __tablename__ = "ai_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"), nullable=False, index=True)
    
    decision_type = Column(String, nullable=False)  # irrigate | skip | alert
    reasoning = Column(String)
    confidence = Column(Float, nullable=False)
    water_saved_l = Column(Float)
    input_snapshot = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    zone = relationship("Zone", back_populates="ai_decisions")

    def __repr__(self):
        return f"<AIDecision(id='{self.id}', type='{self.decision_type}')>"
