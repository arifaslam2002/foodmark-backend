
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from models.badge import Badge
from models.dish import Dish
from models.shop import Shop
from models.vote import Vote


router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/shops")
def search_shops(
    q: str = Query(..., description="Shop name to search"),
    db: Session = Depends(get_db)
):
    shops = db.query(Shop).filter(
        Shop.name.ilike(f"%{q}%"),
        Shop.is_verified == True
    ).all()

    if not shops:
        return {"message": f"No shops found for '{q}'", "results": []}

    results = []
    for s in shops:                     # ✅ changed shop to s
        results.append({
            "shop_id"     : s.id,
            "name"        : s.name,
            "address"     : s.address,
            "cuisine_type": s.cuisine_type,
            "district"    : s.district,
            "state"       : s.state,
        })

    return {"query": q, "total": len(results), "results": results}


@router.get("/dishes")
def search_dishes(
    q: str = Query(..., description="Dish name to search"),
    db: Session = Depends(get_db)
):
    dishes = db.query(Dish).filter(
        Dish.name.ilike(f"%{q}%"),      # case insensitive search
        Dish.is_available == True
    ).all()

    if not dishes:
        return {"message": f"No dishes found for '{q}'", "results": []}

    results = []
    for d in dishes:
        shop = db.query(Shop).filter(Shop.id == d.shop_id).first()

        upvotes = db.query(Vote).filter(
            Vote.dish_id == d.id,
            Vote.vote_type == "up"
        ).count()

        badges = db.query(Badge).filter(
            Badge.dish_id == d.id
        ).all()

        results.append({
            "dish_id"  : d.id,
            "name"     : d.name,
            "price"    : d.price,
            "is_veg"   : d.is_veg,
            "upvotes"  : upvotes,
            "badges"   : [b.badge_name for b in badges],
            "shop_name": shop.name if shop else None,
            "shop_id"  : shop.id if shop else None,
        })

    # sort by upvotes
    results.sort(key=lambda x: x["upvotes"], reverse=True)

    return {
        "query"  : q,
        "total"  : len(results),
        "results": results
    }
@router.get("/all")
def search_all(
    q: str = Query(..., description="Search shops and dishes together"),
    db: Session = Depends(get_db)
):
    # shops
    shops = db.query(Shop).filter(
        Shop.name.ilike(f"%{q}%"),
        Shop.is_verified == True
    ).all()

    shop_results = []
    for s in shops:
        shop_results.append({
            "shop_id"     : s.id,
            "name"        : s.name,
            "address"     : s.address,
            "cuisine_type": s.cuisine_type,
        })

    # dishes
    dishes = db.query(Dish).filter(
        Dish.name.ilike(f"%{q}%"),
        Dish.is_available == True
    ).all()

    dish_results = []
    for d in dishes:
        shop = db.query(Shop).filter(Shop.id == d.shop_id).first()
        upvotes = db.query(Vote).filter(
            Vote.dish_id == d.id,
            Vote.vote_type == "up"
        ).count()
        dish_results.append({
            "dish_id"  : d.id,
            "name"     : d.name,
            "price"    : d.price,
            "is_veg"   : d.is_veg,
            "upvotes"  : upvotes,
            "shop_name": shop.name if shop else None,
        })

    return {
        "query"  : q,
        "shops"  : shop_results,
        "dishes" : dish_results,
        "total"  : len(shop_results) + len(dish_results)
    }
