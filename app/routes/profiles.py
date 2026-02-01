from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.profile import Profile
from app.schemas.profile import ProfileCreate, ProfileOut

router = APIRouter()


@router.post("/profiles", response_model=ProfileOut)
def create_profile(payload: ProfileCreate, request: Request, db: Session = Depends(get_db)):
    print(f"DEBUG: Intentando crear perfil para user_id={payload.user_id}, tipo={payload.profile_type}")
    
    # Verificar que el usuario existe (evitar IntegrityError por FK)
    from app.models.user import User
    try:
        user = db.get(User, payload.user_id)
        if not user:
            print(f"ERROR: Usuario {payload.user_id} NO encontrado en la base de datos.")
            raise HTTPException(status_code=404, detail=f"El usuario {payload.user_id} no existe. Por favor, cierra sesión e inicia de nuevo.")

        profile = Profile(
            user_id=payload.user_id,
            profile_type=payload.profile_type,
            description=payload.description or "",
            video_url=payload.video_url,
            available_now=payload.available_now,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        print(f"DEBUG: Perfil creado con éxito. ID={profile.id}")

        # Actualizar la sesión del usuario si existe
        if "user_id" in request.session and request.session["user_id"] == profile.user_id:
            request.session["profile_id"] = profile.id
        
        return profile

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR CRÍTICO creando perfil: {str(e)}\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"Error interno al crear perfil: {str(e)}")


@router.get("/profiles", response_model=list[ProfileOut])
def list_profiles(db: Session = Depends(get_db)):
    q = select(Profile).order_by(Profile.id.desc())
    return db.execute(q).scalars().all()


@router.get("/profiles/{profile_id}", response_model=ProfileOut)
def get_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.execute(select(Profile).where(Profile.id == profile_id)).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile no encontrado.")
    return profile
    return profile


from fastapi import UploadFile, File
import os
import shutil

@router.post("/profiles/{profile_id}/photo")
def upload_profile_photo(profile_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    profile = db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile no encontrado")

    # Guardar en static/uploads
    upload_dir = "app/static/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Extension
    ext = ".jpg"
    if "png" in file.content_type: ext = ".png"
    elif "jpeg" in file.content_type: ext = ".jpg"
    
    filename = f"profile_avatar_{profile_id}{ext}"
    file_location = f"{upload_dir}/{filename}"
    
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
        
    # Actualizar DB
    profile.photo = f"/static/uploads/{filename}"
    db.commit()
    
    return {"status": "ok", "photo_url": profile.photo}

@router.post("/profiles/{profile_id}/video_upload")
def upload_profile_video_file(profile_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    profile = db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile no encontrado")

    # Guardar en static/uploads
    upload_dir = "app/static/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Extension permitida
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un video")
        
    ext = ".mp4" # Forzar mp4 o detectar extension
    if "webm" in file.content_type: ext = ".webm"
    elif "quicktime" in file.content_type: ext = ".mov"
    
    filename = f"profile_video_{profile_id}{ext}"
    file_location = f"{upload_dir}/{filename}"
    
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
        
    # Actualizar DB
    profile.video_url = f"/static/uploads/{filename}"
    db.commit()
    
    return {"status": "ok", "video_url": profile.video_url}


from pydantic import BaseModel

class ProfileUpdateDesc(BaseModel):
    description: str

@router.put("/profiles/{profile_id}/description")
def update_profile_desc(profile_id: int, payload: ProfileUpdateDesc, db: Session = Depends(get_db)):
    profile = db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile no encontrado")
        
    profile.description = payload.description
    db.commit()
    return {"status": "ok", "description": profile.description}

class ProfileUpdatePhone(BaseModel):
    phone: str

@router.put("/profiles/{profile_id}/phone")
def update_profile_phone(profile_id: int, payload: ProfileUpdatePhone, db: Session = Depends(get_db)):
    profile = db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile no encontrado")
        
    profile.phone = payload.phone
    db.commit()
    return {"status": "ok", "phone": profile.phone}

from app.schemas.profile import ProfileUpdateLocation, ProfileUpdateVideo

@router.put("/profiles/{profile_id}/video")
def update_profile_video(profile_id: int, payload: ProfileUpdateVideo, db: Session = Depends(get_db)):
    profile = db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile no encontrado")
        
    profile.video_url = payload.video_url
    db.commit()
    return {"status": "ok", "video_url": profile.video_url}

@router.put("/profiles/{profile_id}/location")
def update_profile_location(profile_id: int, payload: ProfileUpdateLocation, db: Session = Depends(get_db)):
    profile = db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile no encontrado")
        
    profile.lat = payload.lat
    profile.lon = payload.lon
    profile.address = payload.address
    db.commit()
    return {"status": "ok", "location": profile.address}
