from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    
    # Perfil que RECIBE la valoración
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)
    
    # Usuario que ESCRIBE la valoración
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    score = Column(Integer, nullable=False) # 1 a 5
    comment = Column(String, nullable=True) # Opinión texto
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    profile = relationship("Profile", back_populates="ratings")
    author = relationship("User") # No necesitamos back_populates en User obligatoriamente
