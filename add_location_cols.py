from app.db.session import engine
from sqlalchemy import text

def add_location_columns():
    with engine.connect() as conn:
        # Añadir columna lat
        try:
            conn.execute(text("ALTER TABLE profiles ADD COLUMN lat VARCHAR"))
            print("Columna lat añadida.")
        except Exception as e:
            print(f"Error añadiendo lat (quizás ya existe): {e}")

        # Añadir columna lon
        try:
            conn.execute(text("ALTER TABLE profiles ADD COLUMN lon VARCHAR"))
            print("Columna lon añadida.")
        except Exception as e:
            print(f"Error añadiendo lon (quizás ya existe): {e}")

        # Añadir columna address
        try:
            conn.execute(text("ALTER TABLE profiles ADD COLUMN address VARCHAR"))
            print("Columna address añadida.")
        except Exception as e:
            print(f"Error añadiendo address (quizás ya existe): {e}")
            
        conn.commit()

if __name__ == "__main__":
    add_location_columns()
