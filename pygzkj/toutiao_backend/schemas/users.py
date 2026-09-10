from typing import Optional

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse


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

def success_response(massage: str='Success!',date=None):
    content = {"code":200,"msg":massage,date:date}
    #把对象转换成json数据结构输出
    return JSONResponse(content=jsonable_encoder(content))