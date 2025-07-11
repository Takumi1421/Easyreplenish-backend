# main.py — FastAPI Backend with SQLite, CORS, and Render Compatibility

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os

# -------------------- DATABASE SETUP --------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'inventory.db')}"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# -------------------- MODELS --------------------

class SKU(Base):
    __tablename__ = "skus"
    sku_id = Column(String, primary_key=True, index=True)
    product_name = Column(String)
    current_stock = Column(Integer)
    reorder_threshold = Column(Integer)

Base.metadata.create_all(bind=engine)

# -------------------- SCHEMAS --------------------

class SKUModel(BaseModel):
    sku_id: str
    product_name: str
    current_stock: int
    reorder_threshold: int

    class Config:
        orm_mode = True

# -------------------- APP INIT --------------------

app = FastAPI()

# Enable CORS for Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://easyreplenish-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- DB DEPENDENCY --------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------- ROUTES --------------------

@app.get("/")
def root():
    return {"message": "EasyReplenish API is live!"}

@app.get("/inventory", response_model=list[SKUModel])
def get_inventory(db: Session = Depends(get_db)):
    return db.query(SKU).all()

@app.post("/sku")
def add_sku(sku: SKUModel, db: Session = Depends(get_db)):
    existing = db.query(SKU).filter(SKU.sku_id == sku.sku_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")
    db_sku = SKU(**sku.dict())
    db.add(db_sku)
    db.commit()
    db.refresh(db_sku)
    return {"message": "SKU added", "sku": db_sku}

@app.delete("/sku/{sku_id}")
def delete_sku(sku_id: str, db: Session = Depends(get_db)):
    sku = db.query(SKU).filter(SKU.sku_id == sku_id).first()
    if not sku:
        raise HTTPException(status_code=404, detail="SKU not found")
    db.delete(sku)
    db.commit()
    return {"message": "SKU deleted"}