from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import cloudinary
import cloudinary.uploader
import os

from models import Base, engine, SessionLocal, Item

Base.metadata.create_all(bind=engine)

app = FastAPI(title="我的 CRUD API（Cloudinary 雲端圖片）")

# ===================== Cloudinary 設定 =====================
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

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
    image_url: Optional[str] = None   # ← 改成 image_url（雲端永久連結）

    class Config:
        from_attributes = True

# ===================== GET =====================
@app.get("/")
async def root():
    return {"message": "歡迎來到使用 Cloudinary 雲端圖片的 CRUD API！🚀"}

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

# ===================== 檔案上傳（Cloudinary） =====================
@app.post("/items/{item_id}/upload", response_model=ItemResponse)
async def upload_file_to_item(
    item_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="找不到這個項目")

    # 上傳到 Cloudinary
    result = cloudinary.uploader.upload(file.file)
    image_url = result["secure_url"]   # 永久雲端連結

    # 把雲端連結存進資料庫
    item.image_url = image_url
    db.commit()
    db.refresh(item)

    return item

# ===================== PUT / DELETE =====================
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