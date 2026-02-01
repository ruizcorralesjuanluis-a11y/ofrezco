from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)

    offer_kind = Column(String, nullable=False)      # "SERVICIO" / "COMIDA"
    category = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)

    price = Column(Float, nullable=True)
    currency = Column(String, default="EUR", nullable=False)
    available_now = Column(Boolean, default=False, nullable=False)

    allergens = Column(String, nullable=True)
    status = Column(String, default="DRAFT", nullable=False)  # DRAFT/PENDING/APPROVED/REJECTED
    video_path = Column(String, nullable=True)
    photo_path = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ✅ relación correcta
    profile = relationship("Profile", back_populates="offers")

    # ✅ RELACIÓN CON INTERESES
    interests = relationship("Interest", back_populates="offer", cascade="all, delete-orphan")
