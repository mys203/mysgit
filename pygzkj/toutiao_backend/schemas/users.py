from typing import Optional

from pydantic import BaseModel, Field


class UserRequest(BaseModel):
    username: str
    password: str


class UpdateRequest(BaseModel):
    username: str
    avatar: Optional[str] = None
    nickname: Optional[str] = None
    gender: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None



class UpdatePassword(BaseModel):
    username: str
    old_password: str
    new_password: str