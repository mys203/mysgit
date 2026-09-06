from passlib.context import CryptContext

#创建密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#进行密码加密
def get_password_hash(password:str):
    return pwd_context.hash(password)