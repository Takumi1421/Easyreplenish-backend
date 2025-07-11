# 🚀 FastAPI Backend for EasyReplenish Clone
# File: main.py
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import date

app = FastAPI()

# In-memory mock database
inventory_db = {}
orders_db = {}

# ----------- Models -----------

class SKU(BaseModel):
    sku_id: str
    product_name: str
    current_stock: int
    reorder_threshold: int

class Order(BaseModel):
    order_id: str
    sku_id: str
    quantity: int
    status: str  # ordered, received, returned
    order_date: date

# ----------- API Endpoints -----------

@app.post("/sku", response_model=SKU)
def add_sku(sku: SKU):
    if sku.sku_id in inventory_db:
        raise HTTPException(status_code=400, detail="SKU already exists")
    inventory_db[sku.sku_id] = sku
    return sku

@app.get("/inventory", response_model=List[SKU])
def get_inventory():
    return list(inventory_db.values())

@app.post("/order", response_model=Order)
def place_order(order: Order):
    if order.sku_id not in inventory_db:
        raise HTTPException(status_code=404, detail="SKU not found")
    
    # Reduce stock if status is ordered
    if order.status == "ordered":
        inventory_db[order.sku_id].current_stock -= order.quantity
    elif order.status == "returned":
        inventory_db[order.sku_id].current_stock += order.quantity

    orders_db[order.order_id] = order
    return order

@app.get("/orders", response_model=List[Order])
def get_orders():
    return list(orders_db.values())

@app.get("/reorder-alerts", response_model=List[SKU])
def get_reorder_alerts():
    return [sku for sku in inventory_db.values() if sku.current_stock < sku.reorder_threshold]