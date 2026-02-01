import os

# Permitir OAuth sin HTTPS en desarrollo
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import traceback
from fastapi.staticfiles import StaticFiles

from app.db.init_db import init_db

from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings

from app.routes.users import router as users_router
from app.routes.profiles import router as profiles_router
from app.routes.offers import router as offers_router
from app.routes.web import router as web_router
from app.routes.web import router as web_router
from app.routes.auth import router as auth_router
from app.routes.ratings import router as ratings_router
from app.routes.interests import router as interests_router

app = FastAPI(title="Ofrezco", version="0.1.0")



app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY, https_only=False, same_site="lax")

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {"app": "Ofrezco", "status": "running", "docs": "/docs", "api_prefix": "/api/v1"}


@app.get("/api/v1/health", tags=["health"])
def health():
    return {"ok": True}


app.include_router(users_router, prefix="/api/v1", tags=["users"])
app.include_router(profiles_router, prefix="/api/v1", tags=["profiles"])
app.include_router(offers_router, prefix="/api/v1", tags=["offers"])
app.include_router(auth_router, tags=["auth"])
app.include_router(ratings_router, prefix="/api/v1", tags=["ratings"])
app.include_router(interests_router, prefix="/api/v1", tags=["interests"])

app.include_router(web_router)
app = app