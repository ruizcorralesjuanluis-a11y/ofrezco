from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import List, Optional

from app.db.session import get_db
from app.models.offer import Offer
from app.models.interest import Interest
from app.models.user import User

router = APIRouter()

class InterestCreate(BaseModel):
    offer_id: int

@router.post("/interests")
def create_interest(payload: InterestCreate, request: Request, db: Session = Depends(get_db)):
    # Verificar oferta
    offer = db.get(Offer, payload.offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Oferta no encontrada")

    # Obtener usuario logueado (si existe)
    user_id = request.session.get("user_id")
    
    # Crear interés
    interest = Interest(
        offer_id=offer.id,
        interested_user_id=user_id,
        status="PENDING"
    )
    db.add(interest)
    db.commit()
    db.refresh(interest)
    
    return {"status": "ok", "msg": "Interés registrado", "id": interest.id}

@router.get("/interests/my-offers")
def get_my_offers_interests(request: Request, db: Session = Depends(get_db)):
    # Devuelve intereses sobre mis ofertas
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="No autenticado")
        
    # Buscar ofertas mías que tengan intereses
    # Hacemos una query manual
    # Select offers where profile.user_id == user_id
    # Join interest
    
    from app.models.profile import Profile
    
    # Obtener mi perfil
    profile = db.execute(select(Profile).where(Profile.user_id == user_id)).scalar_one_or_none()
    if not profile:
        return []

    # Obtener ofertas de mi perfil
    offers = db.execute(select(Offer).where(Offer.profile_id == profile.id)).scalars().all()
    
    result = []
    for o in offers:
        # Contar intereses
        count = db.execute(select(func.count(Interest.id)).where(Interest.offer_id == o.id)).scalar()
        if count > 0:
            result.append({
                "offer_title": o.title,
                "offer_id": o.id,
                "interested_count": count
            })
            
    return result

@router.get("/interests/poll")
def poll_interests(last_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Endpoint para long-polling (simulado).
    Comprueba si hay nuevos intereses creados después de 'last_id' para las ofertas del usuario.
    """
    user_id = request.session.get("user_id")
    if not user_id:
        return {"has_new": False}

    from app.models.profile import Profile
    
    # Mi perfil y mis ofertas
    profile = db.execute(select(Profile).where(Profile.user_id == user_id)).scalar_one_or_none()
    if not profile:
        return {"has_new": False}
        
    my_offers_ids = db.execute(select(Offer.id).where(Offer.profile_id == profile.id)).scalars().all()
    
    if not my_offers_ids:
         return {"has_new": False}

    # Buscar intereses nuevos en mis ofertas
    new_interests = db.execute(
        select(Interest)
        .where(Interest.offer_id.in_(my_offers_ids))
        .where(Interest.id > last_id)
        .order_by(Interest.id.desc())
    ).scalars().all()
    
    if new_interests:
        return {
            "has_new": True, 
            "last_id": new_interests[0].id, # El ID más alto encontrado
            "count": len(new_interests)
        }
    
    return {"has_new": False}
