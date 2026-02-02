from pydantic import BaseModel
from typing import Optional, Literal


ProfileType = Literal["PROFESIONAL", "COMUNITARIO"]


class ProfileCreate(BaseModel):
    user_id: int
    profile_type: ProfileType
    description: Optional[str] = None
    video_url: Optional[str] = None
    available_now: bool = False


class ProfileOut(BaseModel):
    id: int
    user_id: int
    profile_type: ProfileType
    description: Optional[str] = None
    video_url: Optional[str] = None
    available_now: bool

    class Config:
        from_attributes = True
