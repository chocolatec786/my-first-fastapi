from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil

from models import Base, engine, SessionLocal, Item

# 建立資料庫表格
Base.metadata.create_all(bind=engine)

app = FastAPI(title="我的 CRUD API（支援檔案上傳）")

# 建立上傳資料夾（如果不存在就自動建立）
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 讓 FastAPI 可以顯示上傳的圖片
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    image_path: Optional[str] = None

    class Config:
        from_attributes = True

# ===================== GET =====================
@app.get("/")
async def root():
    return {"message": "歡迎來到支援檔案上傳的 CRUD API！🚀"}

@app.get("/items", response_model=List[ItemResponse])
async def get_all_items(db: Session = Depends(get_db)):
    return db.query(Item).all()

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

# ===================== 檔案上傳（新功能） =====================
@app.post("/items/{item_id}/upload", response_model=ItemResponse)
async def upload_file_to_item(
    item_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上傳檔案到指定項目，並把路徑存進資料庫"""
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="找不到這個項目")

    # 儲存檔案（檔名加上 item_id 避免重複）
    file_path = f"{UPLOAD_DIR}/{item_id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 把路徑存進資料庫
    item.image_path = f"/uploads/{item_id}_{file.filename}"
    db.commit()
    db.refresh(item)

    return item

# ===================== PUT / DELETE（保持不變） =====================
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

@app.delete("/items/{item_id}")
async def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="找不到這個項目")
    db.delete(db_item)
    db.commit()
    return {"message": "刪除成功！"}