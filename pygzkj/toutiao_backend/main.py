from fastapi import FastAPI
from routers import news
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

#把路由的news挂载（注册）过来(也就是把别的文件搞过来)
app.include_router(news.router)