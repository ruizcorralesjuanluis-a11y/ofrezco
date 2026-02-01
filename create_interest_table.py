from app.db.session import engine
from app.models.interest import Interest
from app.models.offer import Offer # Asegurar que Offer está cargado
from app.db.base import Base

def create_interest_table():
    print("Creando tabla 'interests'...")
    Interest.__table__.create(bind=engine)
    print("Tablas creadas.")

if __name__ == "__main__":
    create_interest_table()
