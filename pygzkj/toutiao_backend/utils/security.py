from passlib.context import CryptContext

#创建密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#进行密码加密
def get_password_hash(password:str):
    return pwd_context.hash(password)

#验证密码是否正确（明文密码 + 数据库里的哈希密码）
def verify_password(plain_password:str, hashed_password:str):
    return pwd_context.verify(plain_password, hashed_password)