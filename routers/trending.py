from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from models.dish import Dish
from models.review import Review
from models.shop import Shop
from models.vote import Vote

router = APIRouter(prefix="/trending", tags=["Trending"])

def get_shop_score(shop_id:int,db:Session=Depends(get_db)):
    dishes = db.query(Dish).filter(Dish.shop_id == shop_id).all()
    total_votes = 0
    for dish in dishes:
        total_votes+=db.query(Vote).filter(
            Vote.dish_id == dish.id,
            Vote.vote_type =="up"
            ).count()
    trusted_reviews =db.query(Review).filter(
       Review.shop_id == shop_id,
       Review.is_trusted
    ).count()
    return (total_votes * 2) + (trusted_reviews * 5)
def build_trending(shops, db, limit):
    scored = []
    for shop in shops:
        score = get_shop_score(shop.id, db)

        # top dish of this shop
        dishes = db.query(Dish).filter(
            Dish.shop_id == shop.id,
            Dish.is_available
        ).all()

        top_dish = None
        top_votes = 0
        for dish in dishes:
            votes = db.query(Vote).filter(
                Vote.dish_id == dish.id,
                Vote.vote_type == "up"
            ).count()
            if votes > top_votes:
                top_votes = votes
                top_dish = dish.name

        scored.append({
            "shop_id"     : shop.id,
            "name"        : shop.name,
            "address"     : shop.address,
            "cuisine_type": shop.cuisine_type,
            "district"    : shop.district,
            "state"       : shop.state,
            "country"     : shop.country,
            "score"       : score,
            "top_dish"    : top_dish
        })

    # sort by score
    scored.sort(key=lambda x: x["score"], reverse=True)

    # add rank
    for i, s in enumerate(scored[:limit]):
        s["rank"] = i + 1

    return scored[:limit]
@router.get("/district")
def trending_district(
    district: str = Query(..., description="District name eg: Thiruvananthapuram"),
    limit: int = Query(10, description="How many results"),
    db: Session = Depends(get_db)
):
    shops = db.query(Shop).filter(
        Shop.district == district,
        Shop.is_verified
    ).all()

    if not shops:
        return {"message": f"No shops found in {district}", "trending": []}

    return {
        "district": district,
        "trending": build_trending(shops, db, limit)
    }


# --- Trending by State ---
@router.get("/state")
def trending_state(
    state: str = Query(..., description="State name eg: Kerala"),
    limit: int = Query(10, description="How many results"),
    db: Session = Depends(get_db)
):
    shops = db.query(Shop).filter(
        Shop.state == state,
        Shop.is_verified
    ).all()

    if not shops:
        return {"message": f"No shops found in {state}", "trending": []}

    return {
        "state"   : state,
        "trending": build_trending(shops, db, limit)
    }


# --- Trending by Country ---
@router.get("/country")
def trending_country(
    country: str = Query("India", description="Country name"),
    limit: int = Query(10, description="How many results"),
    db: Session = Depends(get_db)
):
    shops = db.query(Shop).filter(
        Shop.country == country,
        Shop.is_verified
    ).all()

    if not shops:
        return {"message": f"No shops found in {country}", "trending": []}

    return {
        "country" : country,
        "trending": build_trending(shops, db, limit)
    }


# --- Trending Dishes by District ---
@router.get("/dishes/district")
def trending_dishes_district(
    district: str = Query(..., description="District name"),
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    shops = db.query(Shop).filter(
        Shop.district == district,
        Shop.is_verified
    ).all()

    if not shops:
        return {"message": f"No shops found in {district}", "trending": []}

    shop_ids = [s.id for s in shops]
    dishes = db.query(Dish).filter(
        Dish.shop_id.in_(shop_ids),
        Dish.is_available
    ).all()

    scored = []
    for dish in dishes:
        upvotes = db.query(Vote).filter(
            Vote.dish_id == dish.id,
            Vote.vote_type == "up"
        ).count()

        shop = next(s for s in shops if s.id == dish.shop_id)

        scored.append({
            "dish_id"  : dish.id,
            "dish_name": dish.name,
            "price"    : dish.price,
            "is_veg"   : dish.is_veg,
            "shop_name": shop.name,
            "upvotes"  : upvotes
        })

    scored.sort(key=lambda x: x["upvotes"], reverse=True)
    for i, d in enumerate(scored[:limit]):
        d["rank"] = i + 1

    return {
        "district": district,
        "trending_dishes": scored[:limit]
    }
@router.get("/dishes/state")
def trending_dishes_state(
    state: str = Query(..., description="State name"),
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    shops = db.query(Shop).filter(
        Shop.state == state,
        Shop.is_verified
    ).all()

    if not shops:
        return {"message": f"No shops found in {state}", "trending": []}

    shop_ids = [s.id for s in shops]
    dishes = db.query(Dish).filter(
        Dish.shop_id.in_(shop_ids),
        Dish.is_available
    ).all()

    scored = []
    for dish in dishes:
        upvotes = db.query(Vote).filter(
            Vote.dish_id == dish.id,
            Vote.vote_type == "up"
        ).count()

        shop = next(s for s in shops if s.id == dish.shop_id)

        scored.append({
            "dish_id"  : dish.id,
            "dish_name": dish.name,
            "price"    : dish.price,
            "is_veg"   : dish.is_veg,
            "shop_name": shop.name,
            "upvotes"  : upvotes
        })

    scored.sort(key=lambda x: x["upvotes"], reverse=True)
    for i, d in enumerate(scored[:limit]):
        d["rank"] = i + 1

    return {
        "state": state,
        "trending_dishes": scored[:limit]
    }



@router.get("/dishes/country")
def trending_dishes_country(
    country: str = Query(..., description="Country name"),
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    shops = db.query(Shop).filter(
        Shop.country == country,   # ✅ FIXED
        Shop.is_verified == True   # ✅ also make explicit
    ).all()

    if not shops:
        return {"message": f"No shops found in {country}", "trending_dishes": []}

    shop_ids = [s.id for s in shops]

    dishes = db.query(Dish).filter(
        Dish.shop_id.in_(shop_ids),
        Dish.is_available == True
    ).all()

    scored = []
    for dish in dishes:
        upvotes = db.query(Vote).filter(
            Vote.dish_id == dish.id,
            Vote.vote_type == "up"
        ).count()

        shop = next((s for s in shops if s.id == dish.shop_id), None)

        scored.append({
            "dish_id"  : dish.id,
            "dish_name": dish.name,
            "price"    : dish.price,
            "is_veg"   : dish.is_veg,
            "shop_name": shop.name if shop else "Unknown",
            "upvotes"  : upvotes
        })

    scored.sort(key=lambda x: x["upvotes"], reverse=True)

    for i, d in enumerate(scored[:limit]):
        d["rank"] = i + 1

    return {
        "country": country,
        "trending_dishes": scored[:limit]
    }