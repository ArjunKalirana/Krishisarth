import uuid
from sqlalchemy import Column, String, DateTime, func, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.postgres import Base

class Farmer(Base):
    """
    Represents a farmer user in the KrishiSarth system.
    """
    __tablename__ = "farmers"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    phone = Column(String)
    password_hash = Column(String, nullable=False)
    preferred_lang = Column(String, default="en")
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_login = Column(DateTime(timezone=True))

    # Relationships
    farms = relationship("Farm", back_populates="farmer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Farmer(id='{self.id}', email='{self.email}')>"
