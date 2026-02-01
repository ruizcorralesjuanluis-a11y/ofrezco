from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserOut, UserCreate

router = APIRouter()


@router.post("/users", response_model=UserOut)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    user = User(email=payload.email, name=payload.name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/users", response_model=list[UserOut])
def list_users(
    email: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = select(User)
    if email:
        q = q.where(User.email == email)

    return db.execute(q).scalars().all()
