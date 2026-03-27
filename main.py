from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from models import Base, engine, SessionLocal, Item

# 建立資料庫表格（如果還沒有就建立）
Base.metadata.create_all(bind=engine)

app = FastAPI(title="我的 CRUD API（使用 SQLite）")

# 依賴注入：每次請求都取得一個資料庫連線
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic 模型（給請求/回應用）
class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True   # 新版 Pydantic v2 用法

# ===================== GET =====================
@app.get("/")
async def root():
    return {"message": "歡迎來到使用 SQLite 的 CRUD API！🚀"}

@app.get("/items", response_model=List[ItemResponse])
async def get_all_items(db: Session = Depends(get_db)):
    items = db.query(Item).all()
    return items

@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="找不到這個項目")
    return item

# ===================== POST =====================
@app.post("/items", response_model=ItemResponse)
async def create_item(new_item: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(name=new_item.name, description=new_item.description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# ===================== PUT =====================
@app.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(item_id: int, updated_item: ItemCreate, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="找不到這個項目")
    db_item.name = updated_item.name
    db_item.description = updated_item.description
    db.commit()
    db.refresh(db_item)
    return db_item

# ===================== DELETE =====================
@app.delete("/items/{item_id}")
async def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="找不到這個項目")
    db.delete(db_item)
    db.commit()
    return {"message": "刪除成功！"}