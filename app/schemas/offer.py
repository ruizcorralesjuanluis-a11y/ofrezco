from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class OfferCreate(BaseModel):
    profile_id: int
    offer_kind: str
    category: str
    title: str
    description: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = "EUR"
    available_now: bool = False
    allergens: Optional[str] = None
    extra_info: Optional[Dict[str, Any]] = None


class OfferStatusUpdate(BaseModel):
    status: str


class OfferOut(BaseModel):
    id: int
    profile_id: int
    offer_kind: str
    category: str
    title: str
    description: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    available_now: bool
    allergens: Optional[str] = None
    status: str
    video_path: Optional[str] = None
    photo_path: Optional[str] = None
    extra_info: Optional[Dict[str, Any]] = None

    # ✅ campos obligatorios en respuesta
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
