from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from auth import decode_token
from database import get_db
from models.rating import Rating
from models.shop import Shop
from schemas.rating import RatingCreateSchema


router = APIRouter(prefix="/ambience", tags=["Ambience,Service,staff & cleanliness"])
def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token missing")
    token = authorization.split(" ")[1]
    data = decode_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return data
@router.post("/rate")
def add_rate(
    data: RatingCreateSchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    shop = db.query(Shop).filter(Shop.id == data.shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    # check if already rated
    existing = db.query(Rating).filter(
        Rating.user_id == current_user["user_id"],
        Rating.shop_id == data.shop_id
    ).first()

    if existing:
        # update existing rating
        existing.service     = data.service
        existing.cleanliness = data.cleanliness
        existing.staff       = data.staff
        existing.ambience    = data.ambience
        db.commit()
        return {"message": "Rating updated!"}

    # new rating
    rating = Rating(
        shop_id     = data.shop_id,
        user_id     = current_user["user_id"],
        service     = data.service,
        cleanliness = data.cleanliness,
        staff       = data.staff,
        ambience    = data.ambience
    )
    db.add(rating)
    db.commit()
    return {"message": "Rating added!"}
@router.get("/{shop_id}")
def get_rating(shop_id: int, db: Session = Depends(get_db)):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    ratings = db.query(Rating).filter(Rating.shop_id == shop_id).all()

    if not ratings:
        return {"shop": shop.name, "message": "No ratings yet"}

    total = len(ratings)

    avg_service     = round(sum(r.service     for r in ratings) / total, 2)
    avg_cleanliness = round(sum(r.cleanliness for r in ratings) / total, 2)
    avg_staff       = round(sum(r.staff       for r in ratings) / total, 2)
    avg_ambience    = round(sum(r.ambience    for r in ratings) / total, 2)

    overall = round(
        (avg_service + avg_cleanliness + avg_staff + avg_ambience) / 4, 2
    )

    return {
        "shop"          : shop.name,
        "total_ratings" : total,
        "overall"       : overall,
        "breakdown"     : {
            "service"    : avg_service,
            "cleanliness": avg_cleanliness,
            "staff"      : avg_staff,
            "ambience"   : avg_ambience
        }
    }