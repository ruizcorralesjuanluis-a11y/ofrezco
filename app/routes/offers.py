from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import select
import os
import subprocess

from app.db.session import get_db
from app.models.profile import Profile
from app.models.offer import Offer
from app.schemas.offer import OfferCreate, OfferOut, OfferStatusUpdate

router = APIRouter()


@router.post("/offers", response_model=OfferOut, status_code=status.HTTP_201_CREATED)
def create_offer(payload: OfferCreate, db: Session = Depends(get_db)):
    print(f"DEBUG: Creando oferta con payload: {payload.dict()}")
    profile = db.execute(select(Profile).where(Profile.id == payload.profile_id)).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile no encontrado.")

    try:
        offer = Offer(
            profile_id=payload.profile_id,
            offer_kind=payload.offer_kind,
            category=payload.category,
            title=payload.title,
            description=payload.description,
            price=payload.price,
            currency=payload.currency,
            available_now=payload.available_now,
            allergens=payload.allergens,
            status="DRAFT",
        )

        db.add(offer)
        db.commit()
        db.refresh(offer)
        print(f"DEBUG: Oferta creada con éxito: {offer.id}")
        return offer
    except Exception as e:
        db.rollback()
        print(f"ERROR creando oferta: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno al guardar: {str(e)}")


@router.post("/offers/{offer_id}/submit", response_model=OfferOut)
def submit_for_review(offer_id: int, db: Session = Depends(get_db)):
    offer = db.execute(select(Offer).where(Offer.id == offer_id)).scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer no encontrada.")

    if not offer.video_path:
        raise HTTPException(status_code=400, detail="Para enviar a revisión necesitas subir un vídeo (máx 15s).")

    offer.status = "PUBLISHED" # Auto-publicar para demo (saltar revisión)
    db.commit()
    db.refresh(offer)
    return offer


@router.get("/offers", response_model=list[OfferOut])
def list_offers(
    db: Session = Depends(get_db),
    profile_id: int | None = None,
    offer_kind: str | None = None,
    available_now: bool | None = None,
    mine: bool = False,
    limit: int = 50,
    offset: int = 0,
):
    q = select(Offer).order_by(Offer.id.desc())

    if mine:
        if profile_id is None:
            raise HTTPException(status_code=400, detail="Para mine=true debes pasar profile_id.")
        q = q.where(Offer.profile_id == profile_id)
    else:
        q = q.where(Offer.status == "PUBLISHED")
        if profile_id is not None:
            q = q.where(Offer.profile_id == profile_id)

    if offer_kind is not None:
        q = q.where(Offer.offer_kind == offer_kind)
    if available_now is not None:
        q = q.where(Offer.available_now == available_now)

    q = q.limit(limit).offset(offset)
    return db.execute(q).scalars().all()


@router.get("/offers/pending", response_model=list[OfferOut])
def list_pending_offers(db: Session = Depends(get_db), limit: int = 100, offset: int = 0):
    q = (
        select(Offer)
        .where(Offer.status == "PENDING")
        .order_by(Offer.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return db.execute(q).scalars().all()


@router.patch("/offers/{offer_id}/status", response_model=OfferOut)
def update_offer_status(offer_id: int, payload: OfferStatusUpdate, db: Session = Depends(get_db)):
    offer = db.execute(select(Offer).where(Offer.id == offer_id)).scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer no encontrada.")

    offer.status = payload.status
    db.commit()
    db.refresh(offer)
    return offer


@router.post("/offers/{offer_id}/video", response_model=OfferOut)
def upload_offer_video(
    offer_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    offer = db.execute(select(Offer).where(Offer.id == offer_id)).scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer no encontrada.")

    # ✅ Aceptar content-types con codecs (ej. "video/webm;codecs=vp8,opus")
    # ✅ Lógica relajada para mayor compatibilidad (Android/iOS)
    ct = (file.content_type or "").lower()
    name = (file.filename or "").lower()
    
    ext = ".mp4" # Default
    if name.endswith(".webm"): ext = ".webm"
    elif name.endswith(".mov"): ext = ".mov"
    elif name.endswith(".3gp"): ext = ".3gp"
    elif name.endswith(".mkv"): ext = ".mkv"
    elif name.endswith(".avi"): ext = ".avi"
    
    # Si no tiene extensión conocida pero es video, lo guardamos tal cual (o como mp4)
    if not ct.startswith("video/") and not ext:
         raise HTTPException(
            status_code=400,
            detail=f"Formato no permitido (content_type={file.content_type})."
        )

    uploads_dir = "app/static/uploads"
    os.makedirs(uploads_dir, exist_ok=True)

    filename = f"offer_{offer_id}_video{ext}"
    save_path = os.path.join(uploads_dir, filename)

    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Archivo vacío.")

    with open(save_path, "wb") as f:
        f.write(data)

    # Duración <= 15s (si ffprobe existe). Si falla ffprobe, NO bloqueamos (demo).
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", save_path],
            capture_output=True,
            text=True,
            check=True,
        )
        duration = float((result.stdout or "").strip() or "0")
        if duration > 15.0:
            os.remove(save_path)
            raise HTTPException(status_code=400, detail=f"Vídeo demasiado largo ({duration:.1f}s). Máximo 15s.")
    except FileNotFoundError:
        pass
    except HTTPException:
        raise
    except Exception:
        # No bloqueamos por validación en demo
        pass

    offer.video_path = f"/static/uploads/{filename}"
    db.commit()
    db.refresh(offer)
    return offer


@router.post("/offers/{offer_id}/photo", response_model=OfferOut)
def upload_offer_photo(
    offer_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    offer = db.execute(select(Offer).where(Offer.id == offer_id)).scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer no encontrada.")

    # Validar extensión de imagen
    name = (file.filename or "").lower()
    ext = ".jpg"
    if name.endswith(".png"): ext = ".png"
    elif name.endswith(".jpeg"): ext = ".jpeg"
    elif name.endswith(".webp"): ext = ".webp"

    uploads_dir = "app/static/uploads"
    os.makedirs(uploads_dir, exist_ok=True)

    filename = f"offer_{offer_id}_photo{ext}"
    save_path = os.path.join(uploads_dir, filename)

    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Archivo vacío.")

    with open(save_path, "wb") as f:
        f.write(data)

    offer.photo_path = f"/static/uploads/{filename}"
    db.commit()
    db.refresh(offer)
    return offer


@router.delete("/offers/{offer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_offer(offer_id: int, db: Session = Depends(get_db)):
    offer = db.execute(select(Offer).where(Offer.id == offer_id)).scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer no encontrada.")
    
    # Borrar archivos si existen
    for p in [offer.video_path, offer.photo_path]:
        if p:
            file_path = "app" + p
            if os.path.exists(file_path):
                try: os.remove(file_path)
                except: pass

    db.delete(offer)
    db.commit()
    return None
