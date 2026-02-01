from pydantic import BaseModel, Field
from typing import Optional, List


class SearchRequest(BaseModel):
    lat: float
    lon: float
    radius_km: float = Field(default=3.0, ge=0.1, le=50.0)

    category_id: Optional[int] = None
    available_now: Optional[bool] = None

    # texto libre tipo “electricista urgente” (MVP: no lo usamos aún)
    q: Optional[str] = None


class SearchProfileOut(BaseModel):
    profile_id: int
    display_name: str
    avatar_url: Optional[str] = None
    verified: bool
    rating: Optional[float] = None
    available_now: bool

    distance_km: float
    primary_category: Optional[str] = None

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    count: int
    radius_km: float
    results: List[SearchProfileOut]
