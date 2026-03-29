from typing import Optional

from auth import decode_token
from database import get_db
from fastapi import APIRouter, Depends, Header, HTTPException
from models.dish import Dish
from models.shop import Shop
from schemas.dish import DishCreateSchema, DishResponseSchema
from sqlalchemy.orm import Session

router = APIRouter(prefix="/dishes", tags=["Dishes"])


def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token missing")
    token = authorization.split(" ")[1]
    data = decode_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return data


# --- Owner adds dish ---
@router.post("/add", response_model=DishResponseSchema)
def add_dish(
    data: DishCreateSchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "owner":
        raise HTTPException(status_code=403, detail="Only owners can add dishes")

    # check shop belongs to this owner
    shop = (
        db.query(Shop)
        .filter(Shop.id == data.shop_id, Shop.owner_id == current_user["user_id"])
        .first()
    )
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found or not yours")

    if not shop.is_verified:
        raise HTTPException(status_code=403, detail="Shop not verified yet by admin")

    dish = Dish(
        shop_id=data.shop_id,
        name=data.name,
        description=data.description,
        price=data.price,
        ingredients=data.ingredients,
        is_veg=data.is_veg,
        is_vegan=data.is_vegan,  # ✅ new
        is_gluten_free=data.is_gluten_free,  # ✅ new
        is_diabetic_friendly=data.is_diabetic_friendly,  # ✅ new
        spice_level=data.spice_level,
    )
    db.add(dish)
    db.commit()
    db.refresh(dish)
    return dish


# --- Get all dishes of a shop ---
@router.get("/{shop_id}", response_model=list[DishResponseSchema])
def get_dishes(shop_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Dish).filter(Dish.shop_id == shop_id, Dish.is_available == True).all()
    )


# --- Owner updates dish availability ---
@router.patch("/{dish_id}/toggle")
def toggle_dish(
    dish_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "owner":
        raise HTTPException(status_code=403, detail="Only owners can update dishes")

    dish = db.query(Dish).filter(Dish.id == dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")

    dish.is_available = not dish.is_available
    db.commit()
    return {
        "message": f"{dish.name} is now {'available' if dish.is_available else 'unavailable'}"
    }
@router.get("/detail/{dish_id}", response_model=DishResponseSchema)
def get_dish_by_id(dish_id: int, db: Session = Depends(get_db)):
    dish = db.query(Dish).filter(Dish.id == dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")
    return dish