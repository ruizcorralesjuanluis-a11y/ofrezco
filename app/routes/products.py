from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import select
import os
import subprocess

from app.db.session import get_db
from app.models.profile import Profile
from app.models.product import Product
from pydantic import BaseModel

router = APIRouter()

class ProductCreate(BaseModel):
    profile_id: int
    category: str
    title: str
    description: str | None = None
    price: float | None = None
    currency: str = "EUR"

class ProductOut(BaseModel):
    id: int
    title: str
    status: str
    video_path: str | None = None
    class Config:
        orm_mode = True

@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    profile = db.execute(select(Profile).where(Profile.id == payload.profile_id)).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile no encontrado.")

    product = Product(
        profile_id=payload.profile_id,
        category=payload.category,
        title=payload.title,
        description=payload.description,
        price=payload.price,
        currency=payload.currency,
        status="DRAFT",
    )

    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.post("/products/{product_id}/video", response_model=ProductOut)
def upload_product_video(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    product = db.execute(select(Product).where(Product.id == product_id)).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")

    ct = (file.content_type or "").lower()
    ext = ".mp4" # Simplify for now or reuse logic
    if "webm" in ct: ext = ".webm"
    
    uploads_dir = "app/static/uploads"
    os.makedirs(uploads_dir, exist_ok=True)
    filename = f"prod_{product_id}{ext}"
    save_path = os.path.join(uploads_dir, filename)

    data = file.file.read()
    with open(save_path, "wb") as f:
        f.write(data)

    product.video_path = f"/static/uploads/{filename}"
    db.commit()
    db.refresh(product)
    return product


@router.post("/products/{product_id}/submit", response_model=ProductOut)
def submit_product(product_id: int, db: Session = Depends(get_db)):
    product = db.execute(select(Product).where(Product.id == product_id)).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")

    # MANDATORY VIDEO CHECK
    if not product.video_path:
        raise HTTPException(status_code=400, detail="El vídeo es obligatorio para publicar en Mercadillo.")

    product.status = "PUBLISHED"
    db.commit()
    db.refresh(product)
    return product
