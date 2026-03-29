from datetime import date, datetime, timedelta
from typing import Optional

from auth import decode_token
from database import get_db
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from models.announcement import Announcement
from models.badge import Badge
from models.dish import Dish
from models.dish_of_day import DishOfDay
from models.follow import Follow
from models.rating import Rating
from models.report import Report
from models.review import Review
from models.shop import Shop
from models.user import User
from models.user_badge import UserBadge
from models.visit import Visit
from models.vote import Vote
from sqlalchemy.orm import Session

router = APIRouter(prefix="/profile", tags=["Profiles"])


def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token missing")
    token = authorization.split(" ")[1]
    data = decode_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return data


# =====================
# SHOP PROFILE
# =====================
@router.get("/shop/{shop_id}")
def shop_profile(shop_id: int, db: Session = Depends(get_db)):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    # --- dishes ---
    dishes = (
        db.query(Dish).filter(Dish.shop_id == shop_id, Dish.is_available == True).all()
    )

    dish_list = []
    for d in dishes:
        upvotes = (
            db.query(Vote).filter(Vote.dish_id == d.id, Vote.vote_type == "up").count()
        )
        badges = db.query(Badge).filter(Badge.dish_id == d.id).all()
        dish_list.append(
            {
                "id": d.id,
                "name": d.name,
                "price": d.price,
                "is_veg": d.is_veg,
                "ingredients": d.ingredients,
                "upvotes": upvotes,
                "badges": [b.badge_name for b in badges],
            }
        )

    # --- ratings ---
    ratings = db.query(Rating).filter(Rating.shop_id == shop_id).all()
    total_r = len(ratings)
    avg_ratings = None
    if total_r > 0:
        avg_ratings = {
            "service": round(sum(r.service for r in ratings) / total_r, 2),
            "cleanliness": round(sum(r.cleanliness for r in ratings) / total_r, 2),
            "staff": round(sum(r.staff for r in ratings) / total_r, 2),
            "ambience": round(sum(r.ambience for r in ratings) / total_r, 2),
        }
        avg_ratings["overall"] = round(sum(avg_ratings.values()) / 4, 2)

    # --- reviews ---
    reviews = db.query(Review).filter(Review.shop_id == shop_id).all()
    review_list = []
    for review in reviews:        # ✅ changed rv to review
            u = db.query(User).filter(User.id == review.user_id).first()
            review_list.append({
                "id"      : review.id,
                "user_id" : review.user_id,
                "user"    : u.name if u else "Unknown",
                "comment" : review.comment,
                "rating"  : review.rating,
                "trusted" : review.is_trusted,
                "date"    : review.created_at
            })

    # --- total visits ---
    total_visits = db.query(Visit).filter(Visit.shop_id == shop_id).count()

    # --- today dish of day ---
    today = date.today()
    dish_of_day = (
        db.query(DishOfDay)
        .filter(DishOfDay.shop_id == shop_id, DishOfDay.date == today)
        .first()
    )
    dod = None
    if dish_of_day:
        d = db.query(Dish).filter(Dish.id == dish_of_day.dish_id).first()
        dod = {
            "dish_name": d.name if d else "Unknown",
            "special_note": dish_of_day.special_note,
        }

    # --- announcements ---
    announcements = (
        db.query(Announcement)
        .filter(Announcement.shop_id == shop_id, Announcement.is_active == True)
        .order_by(Announcement.created_at.desc())
        .limit(3)
        .all()
    )

    return {
        "shop": {
            "id": shop.id,
            "name": shop.name,
            "description": shop.description,
            "address": shop.address,
            "cuisine_type": shop.cuisine_type,
            "district": shop.district,
            "state": shop.state,
            "open_time": shop.open_time,
            "close_time": shop.close_time,
            "open_days": shop.open_days,
            "is_verified": shop.is_verified,
        },
        "total_visits": total_visits,
        "dish_of_day": dod,
        "ratings": avg_ratings,
        "dishes": dish_list,
        "reviews": review_list,
        "announcements": [
            {"title": a.title, "message": a.message} for a in announcements
        ],
    }


# =====================
# USER PROFILE
# =====================
@router.get("/user/{user_id}")
def user_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # --- reviews ---
    reviews = db.query(Review).filter(Review.user_id == user_id).all()
    trusted = sum(1 for r in reviews if r.is_trusted)

    # --- votes ---
    total_votes = db.query(Vote).filter(Vote.user_id == user_id).count()

    # --- badges ---
    badges = db.query(UserBadge).filter(UserBadge.user_id == user_id).all()
    badge_list = []
    for b in badges:
        d = db.query(Dish).filter(Dish.id == b.dish_id).first()
        badge_list.append(
            {"badge": b.badge_name, "dish_name": d.name if d else "Unknown"}
        )

    # --- follow stats ---
    followers = db.query(Follow).filter(Follow.following_id == user_id).count()
    following = db.query(Follow).filter(Follow.follower_id == user_id).count()

    # --- visit history ---
    visits = (
        db.query(Visit)
        .filter(Visit.user_id == user_id)
        .order_by(Visit.created_at.desc())
        .limit(5)
        .all()
    )

    visit_list = []
    for v in visits:
        s = db.query(Shop).filter(Shop.id == v.shop_id).first()
        visit_list.append(
            {"shop_name": s.name if s else "Unknown", "visited_at": v.created_at}
        )

    # --- trust score ---
    raw_score = (trusted * 5) + (len(reviews) * 2) + (total_votes * 1)
    trust_score = min(round((raw_score / 100) * 10, 1), 10.0)
    trust_score = trust_score if trust_score > 0 else 1.0

    return {
        "user": {"id": user.id, "name": user.name, "role": user.role},
        "stats": {
            "total_reviews": len(reviews),
            "trusted_reviews": trusted,
            "total_votes": total_votes,
            "trust_score": trust_score,
            "followers": followers,
            "following": following,
        },
        "badges": badge_list,
        "recent_visits": visit_list,
    }


# =====================
# ADMIN DASHBOARD
# =====================
@router.get("/admin/dashboard")
def admin_dashboard(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view dashboard")

    # --- user stats ---
    total_users = db.query(User).count()
    total_customers = db.query(User).filter(User.role == "customer").count()
    total_owners = db.query(User).filter(User.role == "owner").count()

    # --- shop stats ---
    total_shops = db.query(Shop).count()
    verified_shops = db.query(Shop).filter(Shop.is_verified == True).count()
    pending_shops = db.query(Shop).filter(Shop.is_verified == False).count()

    # --- dish stats ---
    total_dishes = db.query(Dish).count()

    # --- review stats ---
    total_reviews = db.query(Review).count()
    trusted_reviews = db.query(Review).filter(Review.is_trusted == True).count()

    # --- vote stats ---
    total_votes = db.query(Vote).count()
    total_up = db.query(Vote).filter(Vote.vote_type == "up").count()
    total_down = db.query(Vote).filter(Vote.vote_type == "down").count()

    # --- report stats ---
    total_reports = db.query(Report).count()
    pending_reports = db.query(Report).filter(Report.is_resolved == False).count()

    # --- visit stats ---
    total_visits = db.query(Visit).count()
    week_ago = datetime.utcnow() - timedelta(days=7)
    visits_this_week = db.query(Visit).filter(Visit.created_at >= week_ago).count()

    # --- top 5 shops by visits ---
    shops = db.query(Shop).filter(Shop.is_verified == True).all()
    shop_visits = []
    for s in shops:
        count = db.query(Visit).filter(Visit.shop_id == s.id).count()
        shop_visits.append({"name": s.name, "visits": count})
    shop_visits.sort(key=lambda x: x["visits"], reverse=True)

    # --- top 5 dishes by upvotes ---
    dishes = db.query(Dish).all()
    dish_votes = []
    for d in dishes:
        upvotes = (
            db.query(Vote).filter(Vote.dish_id == d.id, Vote.vote_type == "up").count()
        )
        s = db.query(Shop).filter(Shop.id == d.shop_id).first()
        dish_votes.append(
            {
                "dish_name": d.name,
                "shop_name": s.name if s else "Unknown",
                "upvotes": upvotes,
            }
        )
    dish_votes.sort(key=lambda x: x["upvotes"], reverse=True)

    # --- pending shops waiting for verification ---
    pending = db.query(Shop).filter(Shop.is_verified == False).all()
    pending_list = []
    for s in pending:
        owner = db.query(User).filter(User.id == s.owner_id).first()
        pending_list.append(
            {
                "shop_id": s.id,
                "shop_name": s.name,
                "owner": owner.name if owner else "Unknown",
                "created_at": s.created_at,
            }
        )

    return {
        "users": {
            "total": total_users,
            "customers": total_customers,
            "owners": total_owners,
        },
        "shops": {
            "total": total_shops,
            "verified": verified_shops,
            "pending": pending_shops,
        },
        "dishes": {"total": total_dishes},
        "reviews": {"total": total_reviews, "trusted": trusted_reviews},
        "votes": {"total": total_votes, "upvotes": total_up, "downvotes": total_down},
        "reports": {"total": total_reports, "pending": pending_reports},
        "visits": {"total": total_visits, "this_week": visits_this_week},
        "top_shops": shop_visits[:5],
        "top_dishes": dish_votes[:5],
        "pending_verifications": pending_list,
    }
# =====================
# RECENTLY ADDED SHOPS
# =====================
@router.get("/recently-added")
def recently_added_shops(
    limit: int = Query(10, description="How many results"),
    db: Session = Depends(get_db)
):
    shops = db.query(Shop).filter(
        Shop.is_verified == True
    ).order_by(Shop.created_at.desc()).limit(limit).all()

    if not shops:
        return {"message": "No shops found", "results": []}

    result = []
    for s in shops:
        # total dishes
        total_dishes = db.query(Dish).filter(
            Dish.shop_id == s.id
        ).count()

        # total visits
        total_visits = db.query(Visit).filter(
            Visit.shop_id == s.id
        ).count()

        result.append({
            "shop_id"     : s.id,
            "name"        : s.name,
            "address"     : s.address,
            "cuisine_type": s.cuisine_type,
            "district"    : s.district,
            "state"       : s.state,
            "total_dishes": total_dishes,
            "total_visits": total_visits,
            "added_on"    : s.created_at
        })

    return {
        "total"  : len(result),
        "results": result
    }


# =====================
# DISH COMPARISON
# =====================
@router.get("/compare-dishes")
def compare_dishes(
    dish1_id: int = Query(..., description="First dish id"),
    dish2_id: int = Query(..., description="Second dish id"),
    db: Session = Depends(get_db)
):
    dish1 = db.query(Dish).filter(Dish.id == dish1_id).first()
    dish2 = db.query(Dish).filter(Dish.id == dish2_id).first()

    if not dish1:
        raise HTTPException(status_code=404, detail=f"Dish {dish1_id} not found")
    if not dish2:
        raise HTTPException(status_code=404, detail=f"Dish {dish2_id} not found")

    def get_dish_info(dish):
        shop = db.query(Shop).filter(Shop.id == dish.shop_id).first()

        upvotes   = db.query(Vote).filter(
            Vote.dish_id   == dish.id,
            Vote.vote_type == "up"
        ).count()

        downvotes = db.query(Vote).filter(
            Vote.dish_id   == dish.id,
            Vote.vote_type == "down"
        ).count()

        badges = db.query(Badge).filter(
            Badge.dish_id == dish.id
        ).all()

        reviews = db.query(Review).filter(
            Review.dish_id == dish.id
        ).all()

        avg_rating = 0
        if reviews:
            avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 2)

        trusted_reviews = sum(1 for r in reviews if r.is_trusted)

        # consensus
        from models.consensus import Consensus
        yes_count = db.query(Consensus).filter(
            Consensus.dish_id == dish.id,
            Consensus.vote    == "yes"
        ).count()
        no_count = db.query(Consensus).filter(
            Consensus.dish_id == dish.id,
            Consensus.vote    == "no"
        ).count()
        total_consensus = yes_count + no_count
        yes_percent = round((yes_count / total_consensus) * 100, 1) if total_consensus > 0 else 0

        return {
            "id"             : dish.id,
            "name"           : dish.name,
            "price"          : dish.price,
            "is_veg"         : dish.is_veg,
            "ingredients"    : dish.ingredients,
            "shop_name"      : shop.name if shop else "Unknown",
            "upvotes"        : upvotes,
            "downvotes"      : downvotes,
            "avg_rating"     : avg_rating,
            "total_reviews"  : len(reviews),
            "trusted_reviews": trusted_reviews,
            "badges"         : [b.badge_name for b in badges],
            "worth_it"       : f"{yes_percent}% say yes"
        }

    d1 = get_dish_info(dish1)
    d2 = get_dish_info(dish2)

    # --- winner per category ---
    def winner(val1, val2, label1, label2):
        if val1 > val2:
            return label1
        elif val2 > val1:
            return label2
        return "Tie"

    verdict = {
        "price"      : winner(d2["price"],       d1["price"],       d1["name"], d2["name"]),  # lower is better
        "upvotes"    : winner(d1["upvotes"],      d2["upvotes"],     d1["name"], d2["name"]),
        "avg_rating" : winner(d1["avg_rating"],   d2["avg_rating"],  d1["name"], d2["name"]),
        "trusted_reviews": winner(d1["trusted_reviews"], d2["trusted_reviews"], d1["name"], d2["name"]),
    }

    # overall winner
    wins1 = sum(1 for v in verdict.values() if v == d1["name"])
    wins2 = sum(1 for v in verdict.values() if v == d2["name"])

    if wins1 > wins2:
        overall_winner = d1["name"]
    elif wins2 > wins1:
        overall_winner = d2["name"]
    else:
        overall_winner = "Tie"

    return {
        "dish1"         : d1,
        "dish2"         : d2,
        "verdict"       : verdict,
        "overall_winner": overall_winner
    }