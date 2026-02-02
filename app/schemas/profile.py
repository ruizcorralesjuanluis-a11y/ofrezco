from pydantic import BaseModel
from typing import Optional, Literal


ProfileType = Literal["PROFESIONAL", "COMUNITARIO"]


class ProfileCreate(BaseModel):
    user_id: int
    profile_type: ProfileType
    description: Optional[str] = None
    video_url: Optional[str] = None
    available_now: bool = False

class ProfileUpdateVideo(BaseModel):
    video_url: str


class ProfileOut(BaseModel):
    id: int
    user_id: int
    profile_type: ProfileType
    description: Optional[str] = None
    video_url: Optional[str] = None
    available_now: bool
    lat: Optional[str] = None
    lon: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    photo: Optional[str] = None

    class Config:
        from_attributes = True

class ProfileUpdateLocation(BaseModel):
    lat: Optional[str] = None
    lon: Optional[str] = None
    address: str
