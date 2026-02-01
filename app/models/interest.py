from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base

class Interest(Base):
    __tablename__ = "interests"

    id = Column(Integer, primary_key=True, index=True)
    
    # Oferta en la que se está interesado
    offer_id = Column(Integer, ForeignKey("offers.id"), nullable=False)
    offer = relationship("Offer", back_populates="interests")

    # Usuario interesado (opcional, si es anónimo podría ser NULL o restringirlo)
    interested_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    interested_user = relationship("User")

    status = Column(String, default="PENDING") # PENDING, CONTACTED
    created_at = Column(DateTime, default=datetime.utcnow)
