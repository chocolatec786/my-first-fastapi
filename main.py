from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI(title="我的第一個 CRUD API")

# 1. 定義資料的格式（Pydantic 模型）
class Item(BaseModel):
    id: int
    name: str
    description: str | None = None   # 可以是空

# 模擬資料庫（暫時用 list 存資料，之後會教真資料庫）
items_db: List[Item] = [
    Item(id=1, name="蘋果", description="紅色的好吃蘋果"),
    Item(id=2, name="香蕉", description="黃色的香蕉"),
]

# ===================== GET =====================
@app.get("/")
async def root():
    return {"message": "歡迎來到我的 CRUD API！🚀"}

@app.get("/items")
async def get_all_items():
    """取得所有項目"""
    return items_db

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    """取得單一項目"""
    for item in items_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="找不到這個項目")

# ===================== POST =====================
@app.post("/items")
async def create_item(new_item: Item):
    """新增一個項目"""
    # 檢查 id 是否重複
    if any(item.id == new_item.id for item in items_db):
        raise HTTPException(status_code=400, detail="id 已經存在")
    
    items_db.append(new_item)
    return {"message": "新增成功！", "item": new_item}

# ===================== PUT =====================
@app.put("/items/{item_id}")
async def update_item(item_id: int, updated_item: Item):
    """更新一個項目"""
    for index, item in enumerate(items_db):
        if item.id == item_id:
            items_db[index] = updated_item
            return {"message": "更新成功！", "item": updated_item}
    raise HTTPException(status_code=404, detail="找不到這個項目")

# ===================== DELETE =====================
@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """刪除一個項目"""
    for index, item in enumerate(items_db):
        if item.id == item_id:
            deleted = items_db.pop(index)
            return {"message": "刪除成功！", "deleted_item": deleted}
    raise HTTPException(status_code=404, detail="找不到這個項目")