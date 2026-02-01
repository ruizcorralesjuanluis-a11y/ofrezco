from app.db.session import engine
from sqlalchemy import text

def add_phone_column():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE profiles ADD COLUMN phone VARCHAR"))
            conn.commit()
            print("Columna 'phone' añadida exitosamente.")
        except Exception as e:
            print(f"Error (quizás ya existe): {e}")

if __name__ == "__main__":
    add_phone_column()
