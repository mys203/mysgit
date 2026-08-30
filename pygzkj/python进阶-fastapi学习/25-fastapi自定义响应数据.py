from fastapi import FastAPI, HTTPException

from pydantic import BaseModel
app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World666"}

class Item(BaseModel):
    name: str
    age: int
    count: str

@app.get("/Item/{name}", response_model=Item)
async def get_item(name: str):
    return {
        "name": name,
        "age":1 ,
        "count":"这是好书"
    }

@app.get("/name/{id}")
async def get_id(id: int):
    id_list=[1,2,3,4]
    if id not in id_list:
        return HTTPException(status_code=404, detail="Not Found")
    return {"id":id}