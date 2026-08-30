from fastapi import FastAPI, Query
from pydantic import BaseModel
from fastapi.responses import HTMLResponse,FileResponse

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World666"}

@app.get("/html",response_class=HTMLResponse)
async def get_root():
    return "<h1>这是一级标题</h1>"


@app.get("/notsa")
async def note(book:str=Query("Some Book",description="一些书",lt=100)):
    return {"BOOK": f"书是{book}"}

class User(BaseModel):
    name: str
    age: int
@app.post("/users")
async def create_user(user: User):
    return {"user": user}

@app.get("/file")
async def get_file():
    path ="截图1.png"
    return FileResponse(path)