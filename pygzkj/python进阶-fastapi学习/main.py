from fastapi import FastAPI, Path

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World666"}


@app.get("/hello")
async def hello():
    return {"message": "神了"}

@app.get("/hello/{id}/{name}")
async def hello_by_id(
    id: int,
    name: str = Path(..., min_length=2, max_length=10),
):
    return {"id": id, "name": name, "message": f"神了，id是{id}，名字是{name}"}

@app.get("/hello/{name}")
async def hello_by_name(
    name: str = Path(..., min_length=2, max_length=10),
):
    return {"name": name, "message": f"神了，名字是{name}"}
