from pydantic import BaseModel

class UserRequest(BaseModel):
    username: str
    password: str



class UpdateRequest(BaseModel):
    avatar: str
    nickname: str
    gender : str
    bio: str
    phone: str