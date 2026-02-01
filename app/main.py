import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
import traceback
from fastapi.staticfiles import StaticFiles

from app.db.init_db import init_db

from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings

from app.routes.users import router as users_router
from app.routes.profiles import router as profiles_router
from app.routes.offers import router as offers_router
from app.routes.web import router as web_router
from app.routes.auth import router as auth_router
from app.routes.ratings import router as ratings_router
from app.routes.interests import router as interests_router

app = FastAPI(title="Ofrezco", version="0.1.0")
VERSION = "V4-DEBUG-2026-02-01-RECOVERY"

@app.get("/ping")
def ping():
    return {"status": "ok", "version": VERSION, "msg": "Si ves esto, el servidor esta VIVO"}

# --- FALLBACK PARA ERRORES DE IMPORTACIÓN O ARRANQUE ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Error Critico de Arranque", "error": str(exc), "trace": traceback.format_exc()},
    )

# Configuración de sesión mejorada para Render (HTTPS)
app.add_middleware(
    SessionMiddleware, 
    secret_key=settings.SECRET_KEY, 
    https_only=False, # Cambiar a True si tienes problemas persistentes
    same_site="lax"
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
def on_startup():
    print("--- DEBUG: Verificando variables de entorno ---")
    print(f"GOOGLE_CLIENT_ID presente: {bool(settings.GOOGLE_CLIENT_ID)}")
    print(f"GOOGLE_CLIENT_SECRET presente: {bool(settings.GOOGLE_CLIENT_SECRET)}")
    print(f"SECRET_KEY presente: {bool(settings.SECRET_KEY)}")
    print("---------------------------------------------")
    try:
        init_db()
        print("DEBUG: Base de datos inicializada correctamente.")
    except Exception as e:
        print(f"ERROR CRÍTICO inicializando DB: {str(e)}")

# Redirigir la raíz directamente a la UI visual
@app.get("/")
def root():
    return RedirectResponse(url="/ui")

@app.get("/api/v1/health", tags=["health"])
def health():
    return {
        "ok": True, 
        "render": os.getenv("RENDER") is not None,
        "google_id": bool(settings.GOOGLE_CLIENT_ID)
    }

app.include_router(users_router, prefix="/api/v1", tags=["users"])
app.include_router(profiles_router, prefix="/api/v1", tags=["profiles"])
app.include_router(offers_router, prefix="/api/v1", tags=["offers"])
app.include_router(auth_router, tags=["auth"])
app.include_router(ratings_router, prefix="/api/v1", tags=["ratings"])
app.include_router(interests_router, prefix="/api/v1", tags=["interests"])

app.include_router(web_router)
