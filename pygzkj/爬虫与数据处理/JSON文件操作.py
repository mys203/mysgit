# from typing import final
# try :
#     f=open("mys爱llh.txt","r",encoding="utf-8")
#     content=f.read()
#     print(content)
# finally:
#     f.close()
import json
user={
    "username":"admin",
    "password":"123",
    "email":"19077100306@163.com",
}
# with open("users.json","w",encoding="utf-8") as f:
#     json.dump(user,f,ensure_ascii=False)
with open("users.json","r",encoding="utf-8") as f:
    us=json.load(f)
    print(us)