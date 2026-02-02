from sqlalchemy import inspect, text
from app.db.session import engine
from app.db.base import Base

# IMPORTA LOS MODELOS PARA QUE SQLAlchemy LOS REGISTRE
from app.models.user import User  # noqa: F401
from app.models.profile import Profile  # noqa: F401
from app.models.offer import Offer  # noqa: F401
from app.models.rating import Rating  # noqa: F401
from app.models.interest import Interest  # noqa: F401


def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Auto-migración simple para SQLite/Mantenimiento
    try:
        inspector = inspect(engine)
        columns = [c["name"] for c in inspector.get_columns("profiles")]
        
        with engine.connect() as conn:
            if "phone" not in columns:
                conn.execute(text("ALTER TABLE profiles ADD COLUMN phone VARCHAR"))
                print("DEBUG: Migrated profiles ADD COLUMN phone")
            if "lat" not in columns:
                conn.execute(text("ALTER TABLE profiles ADD COLUMN lat VARCHAR"))
                print("DEBUG: Migrated profiles ADD COLUMN lat")
            if "lon" not in columns:
                conn.execute(text("ALTER TABLE profiles ADD COLUMN lon VARCHAR"))
                print("DEBUG: Migrated profiles ADD COLUMN lon")
            if "address" not in columns:
                conn.execute(text("ALTER TABLE profiles ADD COLUMN address VARCHAR"))
                print("DEBUG: Migrated profiles ADD COLUMN address")
            conn.commit()
    except Exception as e:
        print(f"DEBUG: Error en auto-migración: {e}")

def reset_db_completely():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
