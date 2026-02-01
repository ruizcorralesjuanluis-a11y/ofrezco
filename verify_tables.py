from app.db.session import engine
from app.db.base import Base
from app.models.rating import Rating
from sqlalchemy import inspect

def check_and_fix():
    print("Conectando a BBDD...")
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tablas encontradas: {tables}")
    
    if "ratings" not in tables:
        print("Falta la tabla 'ratings'. Intentando crearla...")
        try:
            Base.metadata.create_all(bind=engine)
            print("Tablas creadas. Verificando de nuevo...")
            tables_new = inspect(engine).get_table_names()
            print(f"Tablas ahora: {tables_new}")
        except Exception as e:
            print(f"Error creando tablas: {e}")
    else:
        print("La tabla 'ratings' ya existe.")

if __name__ == "__main__":
    check_and_fix()
