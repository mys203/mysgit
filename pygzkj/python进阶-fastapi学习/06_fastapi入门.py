from fastapi import FastAPI
#启动 uvicorn 文件名:app --reload
#创建FastAPI实例
app = FastAPI()
#定义api接口
@app.get("/")
def read_root():
    return {"Hello": "World"}
#定义API接口
@app.get("/items/")
def hello_world():
    return [
        {"Hello": "World"},
        {"Hello1": "World1"}
        ]

