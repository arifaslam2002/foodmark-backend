from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from auth import decode_token, get_distance_meters
from models.dish import Dish
from models.user_badge import UserBadge
from models.review import Review
from models.shop import Shop
from database import get_db
from schemas.review import ReviewCreateSchema


router = APIRouter(prefix="/reviews", tags=["Reviews"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    data = decode_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return data
#add review 
@router.post("/add")
def add_review(
    data:ReviewCreateSchema,
    db:Session=Depends(get_db),
    current_user:dict =Depends(get_current_user)
):
    shop =db.query(Shop).filter(Shop.id==data.shop_id).first()
    if not shop:
        raise HTTPException(status_code=404,detail="Shop not found")
    distance = get_distance_meters(
        data.user_lat, data.user_lng,
        shop.latitude, shop.longitude
    )
    is_trusted = distance <= 100

    review = Review(
        user_id=current_user["user_id"],
        shop_id=data.shop_id,
        dish_id= data.dish_id,
        comment=data.comment,
        rating=data.rating,
        is_trusted=is_trusted,
        user_lat=data.user_lat,
        user_lng=data.user_lng
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    earned_badges = []
    if data.dish_id:
     dish = db.query(Dish).filter(Dish.id == data.dish_id).first()
    if dish:
            # check if dish was added within 48 hours
            now           = datetime.now(timezone.utc)
            dish_age      = now - dish.created_at.replace(tzinfo=timezone.utc)
            hours_old     = dish_age.total_seconds() / 3600

            if hours_old <= 48:
                # check no one else reviewed this dish before
                earlier_reviews = db.query(Review).filter(
                    Review.dish_id == data.dish_id,
                    Review.id != review.id
                ).count()

                if earlier_reviews == 0:
                    # give First to Try badge
                    already = db.query(UserBadge).filter(
                        UserBadge.user_id == current_user["user_id"],
                        UserBadge.dish_id == data.dish_id
                    ).first()

                    if not already:
                        badge = UserBadge(
                            user_id    = current_user["user_id"],
                            dish_id    = data.dish_id,
                            badge_name = "First to Try"
                        )
                        db.add(badge)
                        db.commit()
                        earned_badges.append("First to Try 🏅")

@router.get("/{shop_id}")
def get_reviews(shop_id: int, db: Session = Depends(get_db)):
    reviews = db.query(Review).filter(Review.shop_id == shop_id).all()
    return reviews