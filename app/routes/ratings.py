from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.models.rating import Rating
from app.models.profile import Profile
from app.models.user import User

router = APIRouter()

# Schemas Pydantic
class RatingCreate(BaseModel):
    profile_id: int
    author_id: int # Quien escribe
    score: int
    comment: Optional[str] = None

class RatingOut(BaseModel):
    id: int
    profile_id: int
    author_id: int
    author_name: str
    score: int
    comment: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/ratings", response_model=RatingOut)
def create_rating(payload: RatingCreate, db: Session = Depends(get_db)):
    # 1. Validar que el perfil destino existe
    profile = db.get(Profile, payload.profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
        
    # 2. Validar autor
    author = db.get(User, payload.author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Usuario autor no encontrado")
        
    # 3. Evitar auto-reseñas (opcional, pero recomendable)
    if profile.user_id == author.id:
         raise HTTPException(status_code=400, detail="No puedes reseñarte a ti mismo")

    # 4. Crear rating
    rating = Rating(
        profile_id=payload.profile_id,
        author_id=payload.author_id,
        score=payload.score,
        comment=payload.comment
    )
    db.add(rating)
    db.commit()
    db.refresh(rating)
    
    # Construir respuesta con nombre de autor
    return RatingOut(
        id=rating.id,
        profile_id=rating.profile_id,
        author_id=rating.author_id,
        author_name=author.name,
        score=rating.score,
        comment=rating.comment,
        created_at=rating.created_at
    )

@router.get("/profiles/{profile_id}/ratings", response_model=List[RatingOut])
def list_profile_ratings(profile_id: int, db: Session = Depends(get_db)):
    # Obtener ratings con autor
    # SQLAlchemy join
    stmt = select(Rating, User).join(User, Rating.author_id == User.id).where(Rating.profile_id == profile_id).order_by(Rating.created_at.desc())
    results = db.execute(stmt).all()
    
    out = []
    for r, u in results:
        out.append(RatingOut(
            id=r.id,
            profile_id=r.profile_id,
            author_id=r.author_id,
            author_name=u.name,
            score=r.score,
            comment=r.comment,
            created_at=r.created_at
        ))
    return out

@router.get("/profiles/{profile_id}/stats")
def get_profile_stats(profile_id: int, db: Session = Depends(get_db)):
    # Calcular media y total
    stmt = select(func.count(Rating.id), func.avg(Rating.score)).where(Rating.profile_id == profile_id)
    count, avg = db.execute(stmt).one()
    
    return {
        "count": count or 0,
        "average": round(avg, 1) if avg else 0.0
    }
