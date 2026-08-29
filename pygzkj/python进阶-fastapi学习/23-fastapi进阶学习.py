from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Item(BaseModel):
    name: str
    price: float


items = []


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/items")
def create_item(item: Item):
    items.append(item)
    return {"message": "saved", "item": item}

