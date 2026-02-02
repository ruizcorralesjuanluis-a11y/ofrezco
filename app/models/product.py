from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)

    # No "offer_kind" needed as this table IS for products (Mercadillo)
    category = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)

    price = Column(Float, nullable=True)
    currency = Column(String, default="EUR", nullable=False)
    
    # Products might be "sold", but "available_now" (live service) makes less sense.
    # We'll use status for "SOLD", "AVAILABLE".
    status = Column(String, default="DRAFT", nullable=False) # DRAFT, PUBLISHED, SOLD

    video_path = Column(String, nullable=True) # Mandatory for publishing

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    profile = relationship("Profile")
