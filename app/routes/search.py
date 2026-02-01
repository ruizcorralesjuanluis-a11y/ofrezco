import math
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, select

from app.db.session import get_db
from app.models.profile import Profile
from app.models.category import Category
from app.schemas.search import SearchRequest, SearchResponse, SearchProfileOut

router = APIRouter()


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


@router.post("/search", response_model=SearchResponse)
def search(payload: SearchRequest, db: Session = Depends(get_db)):
    # 1) Cargamos perfiles PRO/AMBOS con ubicación
    q = select(Profile).where(Profile.lat.isnot(None)).where(Profile.lon.isnot(None))

    # PRO/AMBOS (si tu campo se llama distinto, dime)
    if hasattr(Profile, "profile_type"):
        q = q.where(Profile.profile_type.in_(["PRO", "AMBOS"]))

    # disponibilidad opcional
    if payload.available_now is not None and hasattr(Profile, "available_now"):
        q = q.where(Profile.available_now == payload.available_now)

    profiles = db.execute(q).scalars().all()

    # 2) Si viene category_id, filtramos con SQL directo (sin ORM relationships)
    allowed_profile_ids = None
    category_name = None

    if payload.category_id is not None:
        cat = db.execute(select(Category).where(Category.id == payload.category_id)).scalar_one_or_none()
        if not cat:
            raise HTTPException(status_code=400, detail="category_id no existe")
        category_name = cat.name

        rows = db.execute(
            text("SELECT profile_id FROM profile_categories WHERE category_id = :cid"),
            {"cid": payload.category_id},
        ).all()
        allowed_profile_ids = {r[0] for r in rows}

    # 3) Distancia + radio
    tmp = []
    for p in profiles:
        if allowed_profile_ids is not None and p.id not in allowed_profile_ids:
            continue

        d = haversine_km(payload.lat, payload.lon, p.lat, p.lon)
        if d <= payload.radius_km:
            tmp.append((p, d))

    tmp.sort(key=lambda x: x[1])

    results = []
    for p, d in tmp[:50]:
        results.append(
            SearchProfileOut(
                profile_id=p.id,
                display_name=p.display_name or f"Profile #{p.id}",
                avatar_url=getattr(p, "avatar_url", None),
                verified=bool(getattr(p, "verified", False)),
                rating=getattr(p, "rating", None),
                available_now=bool(getattr(p, "available_now", False)),
                distance_km=round(d, 2),
                primary_category=category_name,
            )
        )

    return SearchResponse(count=len(results), radius_km=payload.radius_km, results=results)
