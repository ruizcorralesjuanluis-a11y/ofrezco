from app.db.session import engine
from app.db.base import Base

# Importar modelos para registrar tablas
from app.models.user import User  # noqa
from app.models.profile import Profile  # noqa
from app.models.category import Category  # noqa
from app.models.profile_category import ProfileCategory  # noqa

def run():
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas/actualizadas")

if __name__ == "__main__":
    run()
