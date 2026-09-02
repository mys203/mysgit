from fastapi import FastAPI
from routers import news
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
# 接口实现流程
# 1.模块化路由
# 2.定义模型类 —> 数据库表
# 3.在crud 文件夹里面创建文件，封装操作方法
# 4.在路由里调用 crud 封装方法，响应

#把路由的news挂载（注册）过来(也就是把别的文件搞过来)
app.include_router(news.router)