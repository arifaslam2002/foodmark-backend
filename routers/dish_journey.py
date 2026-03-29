from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from auth import decode_token
from models.dish_journey import DishJourney
from schemas.dish_journey import DishJourneyCreateSchema
from database import get_db
from models.dish import Dish

from models.shop import Shop


router = APIRouter(prefix="/dish-journey", tags=["Dish Journey"])
def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token missing")
    token = authorization.split(" ")[1]
    data = decode_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return data
@router.post("/add")
def add_journey(
    data:DishJourneyCreateSchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "owner":
        raise HTTPException(status_code=403, detail="Only owners can log journey")
    dish = db.query(Dish).filter(Dish.id == data.dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")
    shop =db.query(Shop).filter(
        Shop.id == dish.shop_id,
        Shop.owner_id == current_user["user_id"]
    ).first()
    if not shop:
        raise HTTPException(status_code=403, detail="This dish is not yours")
    journey = DishJourney(
        dish_id = data.dish_id,
        shop_id = dish.shop_id,
        note    = data.note
    )
    db.add(journey)
    db.commit()
    db.refresh(journey)

    return {"message": "Journey logged!", "note": data.note}

@router.get("/{dish_id}")
def get_journey(dish_id: int, db: Session = Depends(get_db)):
    dish = db.query(Dish).filter(Dish.id == dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")

    journeys = db.query(DishJourney).filter(
        DishJourney.dish_id == dish_id
    ).order_by(DishJourney.created_at).all()

    if not journeys:
        return {
            "dish"   : dish.name,
            "message": "No journey logged yet",
            "journey": []
        }

    return {
        "dish"   : dish.name,
        "total"  : len(journeys),
        "journey": [
            {
                "note"      : j.note,
                "logged_at" : j.created_at
            }
            for j in journeys
        ]
    }