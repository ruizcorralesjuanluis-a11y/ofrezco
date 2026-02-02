from app.db.session import engine
from app.db.base import Base

# IMPORTA LOS MODELOS PARA QUE SQLAlchemy LOS REGISTRE
from app.models.user import User  # noqa: F401
from app.models.profile import Profile  # noqa: F401
from app.models.offer import Offer  # noqa: F401


def init_db():
    Base.metadata.create_all(bind=engine)
