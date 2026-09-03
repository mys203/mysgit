from fastapi import FastAPI

from routers import news

app = FastAPI()

# 添加CORS中间件允许前端跨域访问（Vite 开发服务器默认端口 5173）
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #允许的源
    allow_credentials=True,   #允许携带cookie
    allow_methods=["*"],      #允许的请求方法
    allow_headers=["*"],      #允许的请求头
)

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