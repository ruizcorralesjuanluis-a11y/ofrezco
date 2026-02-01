from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="profile")

    profile_type = Column(String, nullable=False)
    description = Column(String, nullable=True)
    photo = Column(String, nullable=True) # Foto de perfil (avatar)
    phone = Column(String, nullable=True) # Teléfono para WhatsApp
    video_url = Column(String, nullable=True)
    available_now = Column(Boolean, default=False)
    
    # Ubicación
    lat = Column(String, nullable=True) # Guardamos como string para evitar problemas de float, o Float
    lon = Column(String, nullable=True)
    address = Column(String, nullable=True)

    # ✅ RELACIÓN CON OFERTAS
    offers = relationship(
        "Offer",
        back_populates="profile",
        cascade="all, delete-orphan"
    )

    # ✅ RELACIÓN CON RATINGS recibidos
    ratings = relationship(
        "Rating",
        back_populates="profile",
        cascade="all, delete-orphan"
    )
