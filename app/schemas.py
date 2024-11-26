from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        from_attributes = True

class VideoBase(BaseModel):
    title: str

class VideoCreate(VideoBase):
    pass

class Video(VideoBase):
    id: int
    filename: str
    file_path: str
    upload_date: datetime
    owner_id: int

    class Config:
        from_attributes = True
