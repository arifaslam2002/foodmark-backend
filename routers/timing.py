from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from auth import decode_token
from database import get_db
from models.shop import Shop


router = APIRouter(prefix="/timing", tags=["Shop Timings"])
def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token missing")
    token = authorization.split(" ")[1]
    data = decode_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return data
class TimingSchema(BaseModel):
    open_time : str    # "09:00"
    close_time: str    # "22:00"
    open_days : str    # "Mon,Tue,Wed,Thu,Fri,Sat,Sun"
@router.post("/set/{shop_id}")
def set_time(
    shop_id:int,
    data:TimingSchema,
    db:Session =Depends(get_db),
    current_user:dict =Depends(get_current_user)
):
    if current_user["role"] != "owner":
        raise HTTPException(status_code=403, detail="Only owners can set timings")

    shop = db.query(Shop).filter(
        Shop.id == shop_id,
        Shop.owner_id == current_user["user_id"]
    ).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found or not yours")

    shop.open_time  = data.open_time
    shop.close_time = data.close_time
    shop.open_days  = data.open_days
    db.commit()

    return {"message": "Timings updated!"}  
@router.get("/is-open/{shop_id}")
def is_shop_open(shop_id:int,db:Session = Depends(get_db)):
    shop =db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    if not shop.open_time or not shop.close_time:
        return {"shop": shop.name, "status": "Timings not set"}
    now =datetime.utcnow()
    ist_hour = (now.hour + 5) % 24
    ist_minute = (now.minute + 30) % 60
    if now.minute + 30 >= 60:
        ist_hour = (ist_hour + 1) % 24
    current_time = f"{ist_hour:02d}:{ist_minute:02d}"
    days_map = {0:"Mon", 1:"Tue", 2:"Wed", 3:"Thu", 4:"Fri", 5:"Sat", 6:"Sun"}
    today = days_map[now.weekday()]
    open_days = shop.open_days.split(",") if shop.open_days else []
    day_open = today in open_days

    # check time
    time_open = shop.open_time <= current_time <= shop.close_time

    is_open = day_open and time_open

    return {
        "shop"      : shop.name,
        "is_open"   : is_open,
        "open_time" : shop.open_time,
        "close_time": shop.close_time,
        "open_days" : open_days,
        "today"     : today,
        "now_ist"   : current_time
    }
@router.get("/{shop_id}")
def get_timing(shop_id: int, db: Session = Depends(get_db)):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    return {
        "shop"      : shop.name,
        "open_time" : shop.open_time,
        "close_time": shop.close_time,
        "open_days" : shop.open_days
    }