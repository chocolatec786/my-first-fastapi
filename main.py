from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware   # ← CORS
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
import cloudinary
import cloudinary.uploader
import os

from models import Base, engine, SessionLocal, User, Item

Base.metadata.create_all(bind=engine)

app = FastAPI(title="完整版 FastAPI + React 前端")

# ===================== CORS 加強版（解決 React localhost 問題） =====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],                    # 開發階段允許所有來源（最簡單）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== 其他設定 =====================
SECRET_KEY = "super-secret-key-please-change-this-in-production-1234567890abcdef"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

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

# ===================== 模型 =====================
class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

# ===================== 密碼與 JWT =====================
def get_password_hash(password: str):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(plain_password: str, hashed_password: str):
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# ===================== 註冊 & 登入 =====================
@app.post("/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "註冊成功！請登入"}

@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# ===================== 受保護路由 =====================
@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"你好 {current_user.username}！這是受保護的 API"}

# ===================== Item CRUD =====================
@app.get("/items", response_model=List[ItemResponse])
async def get_all_items(db: Session = Depends(get_db)):
    return db.query(Item).all()

@app.post("/items", response_model=ItemResponse)
async def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(name=item.name, description=item.description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.post("/items/{item_id}/upload", response_model=ItemResponse)
async def upload_image(item_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    result = cloudinary.uploader.upload(file.file)
    item.image_url = result["secure_url"]
    db.commit()
    db.refresh(item)
    return item

print("✅ 完整版伺服器已啟動（CORS 已開啟）")