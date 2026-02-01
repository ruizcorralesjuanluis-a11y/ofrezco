from app.db.session import engine
from app.db.base import Base

# Import models to ensure they are registered with Base.metadata
from app.models.user import User
from app.models.profile import Profile
from app.models.offer import Offer
from app.models.rating import Rating

def reset_database():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Recreating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Database has been reset successfully. All data cleared.")

if __name__ == "__main__":
    reset_database()
