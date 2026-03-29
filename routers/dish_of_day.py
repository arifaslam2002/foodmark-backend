from datetime import date
from typing import Optional

from auth import decode_token
from database import get_db
from fastapi import APIRouter, Depends, Header, HTTPException
from models.badge import Badge
from models.dish import Dish
from models.dish_of_day import DishOfDay
from models.shop import Shop
from models.vote import Vote
from schemas.dish_of_day import DishOfDayCreateSchema
from sqlalchemy.orm import Session

router = APIRouter(prefix="/dish-of-day", tags=["Dish of the Day"])


def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token missing")
    token = authorization.split(" ")[1]
    data = decode_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return data


@router.post("/set")
def set_dish_of_day(
    data: DishOfDayCreateSchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "owner":
        raise HTTPException(
            status_code=403, detail="Only owners can set dish of the day"
        )

    # check shop belongs to owner
    shop = (
        db.query(Shop)
        .filter(Shop.id == data.shop_id, Shop.owner_id == current_user["user_id"])
        .first()
    )
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found or not yours")

    # check dish belongs to shop
    dish = (
        db.query(Dish)
        .filter(Dish.id == data.dish_id, Dish.shop_id == data.shop_id)
        .first()
    )
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found in your shop")

    # check if already set today
    today = date.today()
    existing = (
        db.query(DishOfDay)
        .filter(DishOfDay.shop_id == data.shop_id, DishOfDay.date == today)
        .first()
    )

    if existing:
        # update todays dish
        existing.dish_id = data.dish_id
        existing.special_note = data.special_note
        db.commit()
        return {"message": f"Dish of the day updated to {dish.name}!"}

    # set new dish of the day
    dish_of_day = DishOfDay(
        shop_id=data.shop_id, dish_id=data.dish_id, special_note=data.special_note
    )
    db.add(dish_of_day)
    db.commit()
    return {"message": f"{dish.name} is now dish of the day!"}

@router.get("/today/{shop_id}")
def get_dish_of_day(shop_id: int, db: Session = Depends(get_db)):
    today = date.today()

    dish_of_day = (
        db.query(DishOfDay)
        .filter(DishOfDay.shop_id == shop_id, DishOfDay.date == today)
        .first()
    )

    if not dish_of_day:
        return {"message": "No dish of the day set for today"}

    dish = db.query(Dish).filter(Dish.id == dish_of_day.dish_id).first()
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    upvotes = (
        db.query(Vote).filter(Vote.dish_id == dish.id, Vote.vote_type == "up").count()
    )
    badges = db.query(Badge).filter(Badge.dish_id == dish.id).all()

    return {
        "shop": shop.name,
        "date": today,
        "dish_of_day": {
            "id": dish.id,
            "name": dish.name,
            "price": dish.price,
            "description": dish.description,
            "is_veg": dish.is_veg,
            "upvotes": upvotes,
            "badges": [b.badge_name for b in badges],
            "special_note": dish_of_day.special_note,
        },
    }


@router.get("/history/{shop_id}")
def get_dish_of_day_history(shop_id: int, db: Session = Depends(get_db)):
    history = (
        db.query(DishOfDay)
        .filter(DishOfDay.shop_id == shop_id)
        .order_by(DishOfDay.date.desc())
        .all()
    )

    if not history:
        return {"message": "No history found", "history": []}

    result = []
    for h in history:
        dish = db.query(Dish).filter(Dish.id == h.dish_id).first()
        result.append(
            {
                "date": h.date,
                "dish_name": dish.name if dish else "Unknown",
                "special_note": h.special_note,
            }
        )

    return {"total": len(result), "history": result}
