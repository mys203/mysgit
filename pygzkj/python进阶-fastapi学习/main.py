from os import name

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World666"}


@app.get("/hello")
async def root():
    return {"message": "神了"}
@app.get("/hello/{id}/{name}")
async def hello(id: int, name: str):
    return {"id":id,"name":name,"message":f"神了，id是{id}，名字是{name}"}