from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import settings
from app.models.user import User

router = APIRouter()

oauth = OAuth()

if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

@router.get("/login")
async def login(request: Request):
    if not settings.GOOGLE_CLIENT_ID:
        return RedirectResponse(url="/ui?error=missing_google_config")
    
    # En Render (u otros proxies), url_for puede devolver http en lugar de https.
    # Forzamos https si estamos en producción.
    redirect_uri = str(request.url_for('auth_callback'))
    if os.getenv("RENDER"):
        redirect_uri = redirect_uri.replace("http://", "https://")
    
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth/google/callback")
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        print(f"Auth Error: {e}")
        return RedirectResponse(url="/ui?error=auth_failed")

    user_info = token.get('userinfo')
    if not user_info:
        # Fallback manual si no viene en el token
        user_info = await oauth.google.userinfo(token=token)

    email = user_info.get('email')
    name = user_info.get('name') or email.split('@')[0]
    picture = user_info.get('picture')

    if not email:
        return RedirectResponse(url="/ui?error=no_email")

    # 1. Buscar usuario
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # 2. Crear si no existe
        user = User(email=email, name=name)
        db.add(user)
        db.commit()
        db.refresh(user)

    # 3. Guardar en sesión
    request.session['user_id'] = user.id
    request.session['user_email'] = user.email
    request.session['user_name'] = user.name
    request.session['user_picture'] = picture
    
    # 4. Manejo de perfil (si ya tiene uno, lo seleccionamos)
    if user.profile:
        request.session['profile_id'] = user.profile.id
    else:
        request.session.pop('profile_id', None)

    return RedirectResponse(url="/ui")


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/ui")
