from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Intentar cargar .env o .env.txt
load_dotenv(".env")
load_dotenv(".env.txt")


class Settings(BaseModel):
    APP_NAME: str = "Ofrezco"
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "change-me"
    DATABASE_URL: str = "sqlite:///./dev.db"  # por defecto, para arrancar rápido
    DEBUG: bool = True
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None


def get_settings() -> Settings:
    # Carga desde variables de entorno (si existe .env y lo exportas, perfecto)
    return Settings(
        APP_NAME=os.getenv("APP_NAME", "Ofrezco"),
        API_V1_PREFIX=os.getenv("API_V1_PREFIX", "/api/v1"),
        SECRET_KEY=os.getenv("SECRET_KEY", "change-me"),
        DATABASE_URL=os.getenv("DATABASE_URL", "sqlite:///./dev.db"),
        DEBUG=os.getenv("DEBUG", "true").lower() in ("1", "true", "yes", "y"),
        GOOGLE_CLIENT_ID=os.getenv("GOOGLE_CLIENT_ID"),
        GOOGLE_CLIENT_SECRET=os.getenv("GOOGLE_CLIENT_SECRET"),
    )


settings = get_settings()
