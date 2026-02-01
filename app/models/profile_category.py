from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from app.db.base import Base


class ProfileCategory(Base):
    __tablename__ = "profile_categories"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("profile_id", "category_id", name="uq_profile_category"),
    )
