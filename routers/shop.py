from typing import Optional

from fastapi import APIRouter, Body, Depends,HTTPException, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from auth import decode_token
from models.shop import Shop
from schemas.shop import ShopCreateSchema, ShopResponseSchema
from database import get_db


router = APIRouter(prefix="/shops", tags=["Shops"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token missing")
    token = authorization.split(" ")[1]
    data = decode_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return data
@router.post("/create", response_model=ShopResponseSchema)
def create_shop(
    data: ShopCreateSchema = Body(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"]!="owner":
        raise HTTPException(status_code=403,detail="Only owners can create shops")
    shop = Shop(
       owner_id=current_user["user_id"],
        name=data.name,
        description=data.description,
        address=data.address,
        latitude=data.latitude,
        longitude=data.longitude,
        cuisine_type=data.cuisine_type,
        gst_number=data.gst_number,
        fssai_number=data.fssai_number 
    )
    db.add(shop)
    db.commit()
    db.refresh(shop)
    return shop
# get all verified shop
@router.get("/",response_model=list[ShopResponseSchema])
def get_shops(db:Session=Depends(get_db)):
    return db.query(Shop).filter(Shop.is_verified).all()
#admin verify
@router.patch("/{shop_id}/verify")
def verify_shop(
    shop_id:int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"]!="admin":
     raise HTTPException(status_code=403, detail="Only admin can verify shops")   
    shop=db.query(Shop).filter(Shop.id==shop_id).first()
    if not shop:
         raise HTTPException(status_code=404, detail="Shop not found")
    shop.is_verified=True
    db.commit()
    return {"message": f"{shop.name} verified successfully!"}


# --- Get shops owned by current user ---
@router.get("/my-shops")
def get_my_shops(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    shops = db.query(Shop).filter(
        Shop.owner_id == current_user["user_id"]
    ).all()
    return shops