from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from database import get_db
from models.shop import Shop
from models.dish import Dish
from models.vote import Vote
from models.review import Review
from models.visit import Visit
from models.rating import Rating
from models.user import User
from auth import decode_token
from pydantic import BaseModel

router = APIRouter(prefix="/battle", tags=["Shop Battle & Dish of Month"])

def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token missing")
    token = authorization.split(" ")[1]
    data = decode_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return data

# =====================
# SHOP VS SHOP BATTLE
# =====================

class BattleVoteSchema(BaseModel):
    shop1_id: int
    shop2_id: int
    vote    : int    # 1 for shop1, 2 for shop2

def get_shop_stats(shop_id: int, db: Session) -> dict:
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        return None

    # all dishes
    dishes = db.query(Dish).filter(Dish.shop_id == shop_id).all()

    # total upvotes on all dishes
    total_upvotes = 0
    for d in dishes:
        total_upvotes += db.query(Vote).filter(
            Vote.dish_id   == d.id,
            Vote.vote_type == "up"
        ).count()

    # trusted reviews
    trusted_reviews = db.query(Review).filter(
        Review.shop_id    == shop_id,
        Review.is_trusted == True
    ).count()

    # avg rating
    ratings = db.query(Rating).filter(Rating.shop_id == shop_id).all()
    avg_rating = 0
    if ratings:
        avg_rating = round(
            sum((r.service + r.cleanliness + r.staff + r.ambience) / 4
                for r in ratings) / len(ratings), 2
        )

    # total visits
    total_visits = db.query(Visit).filter(Visit.shop_id == shop_id).count()

    return {
        "shop_id"       : shop.id,
        "name"          : shop.name,
        "cuisine_type"  : shop.cuisine_type,
        "total_dishes"  : len(dishes),
        "total_upvotes" : total_upvotes,
        "trusted_reviews": trusted_reviews,
        "avg_rating"    : avg_rating,
        "total_visits"  : total_visits
    }

# --- Get battle stats ---
@router.get("/shops")
def shop_battle(
    shop1_id: int = Query(..., description="First shop id"),
    shop2_id: int = Query(..., description="Second shop id"),
    db: Session = Depends(get_db)
):
    if shop1_id == shop2_id:
        raise HTTPException(status_code=400, detail="Cannot battle same shop!")

    s1 = get_shop_stats(shop1_id, db)
    s2 = get_shop_stats(shop2_id, db)

    if not s1:
        raise HTTPException(status_code=404, detail=f"Shop {shop1_id} not found")
    if not s2:
        raise HTTPException(status_code=404, detail=f"Shop {shop2_id} not found")

    # --- winner per category ---
    def winner(val1, val2, name1, name2):
        if val1 > val2:   return name1
        elif val2 > val1: return name2
        else:             return "Tie"

    categories = {
        "most_upvotes"      : winner(s1["total_upvotes"],   s2["total_upvotes"],   s1["name"], s2["name"]),
        "most_trusted"      : winner(s1["trusted_reviews"], s2["trusted_reviews"], s1["name"], s2["name"]),
        "best_rated"        : winner(s1["avg_rating"],      s2["avg_rating"],      s1["name"], s2["name"]),
        "most_visited"      : winner(s1["total_visits"],    s2["total_visits"],    s1["name"], s2["name"]),
        "most_dishes"       : winner(s1["total_dishes"],    s2["total_dishes"],    s1["name"], s2["name"]),
    }

    # overall winner
    wins1 = sum(1 for v in categories.values() if v == s1["name"])
    wins2 = sum(1 for v in categories.values() if v == s2["name"])

    if wins1 > wins2:
        overall = s1["name"]
    elif wins2 > wins1:
        overall = s2["name"]
    else:
        overall = "Tie"

    return {
        "shop1"          : s1,
        "shop2"          : s2,
        "categories"     : categories,
        "overall_winner" : overall
    }

# =====================
# DISH OF THE MONTH
# =====================
@router.get("/dish-of-month")
def dish_of_month(
    month: Optional[int] = Query(None, description="Month number 1-12"),
    year : Optional[int] = Query(None, description="Year eg 2026"),
    db: Session = Depends(get_db)
):
    now   = datetime.utcnow()
    month = month or now.month
    year  = year  or now.year

    # get all votes in this month
    month_start = datetime(year, month, 1)
    if month == 12:
        month_end = datetime(year + 1, 1, 1)
    else:
        month_end = datetime(year, month + 1, 1)

    # count upvotes per dish this month
    votes = db.query(Vote).filter(
        Vote.vote_type   == "up",
        Vote.created_at  >= month_start,
        Vote.created_at  < month_end
    ).all()

    if not votes:
        return {"message": f"No votes found for {month}/{year}"}

    # count votes per dish
    dish_vote_count = {}
    for v in votes:
        dish_vote_count[v.dish_id] = dish_vote_count.get(v.dish_id, 0) + 1

    # find dish with most votes
    top_dish_id = max(dish_vote_count, key=dish_vote_count.get)
    top_votes   = dish_vote_count[top_dish_id]

    dish = db.query(Dish).filter(Dish.id == top_dish_id).first()
    shop = db.query(Shop).filter(Shop.id == dish.shop_id).first()

    # top 5 dishes this month
    sorted_dishes = sorted(
        dish_vote_count.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    top5 = []
    for i, (dish_id, votes_count) in enumerate(sorted_dishes):
        d = db.query(Dish).filter(Dish.id == dish_id).first()
        s = db.query(Shop).filter(Shop.id == d.shop_id).first() if d else None
        top5.append({
            "rank"     : i + 1,
            "dish_name": d.name     if d else "Unknown",
            "shop_name": s.name     if s else "Unknown",
            "upvotes"  : votes_count
        })

    return {
        "month"         : month,
        "year"          : year,
        "dish_of_month" : {
            "name"     : dish.name     if dish else "Unknown",
            "shop_name": shop.name     if shop else "Unknown",
            "upvotes"  : top_votes
        },
        "top5_this_month": top5
    }