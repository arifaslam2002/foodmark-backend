from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from models.shop import Shop
from models.dish import Dish
from models.vote import Vote
from models.badge import Badge
import math

router = APIRouter(prefix="/nearby", tags=["Nearby Shops"])

def get_distance_meters(lat1, lng1, lat2, lng2):
    R = 6371000
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    return R * 2 * math.asin(math.sqrt(a))

@router.get("/shops")
def get_nearby_shops(
    lat   : float = Query(...),
    lng   : float = Query(...),
    radius: float = Query(5000),
    db    : Session = Depends(get_db)
):
    shops = db.query(Shop).filter(Shop.is_verified == True).all()

    print(f"Total verified shops: {len(shops)}")  # ✅ debug
    print(f"User location: {lat}, {lng}, radius: {radius}")

    nearby = []
    for shop in shops:
        distance = get_distance_meters(lat, lng, shop.latitude, shop.longitude)
        print(f"Shop {shop.name}: {round(distance, 2)}m")  # ✅ debug

        if distance <= radius:
            dishes = db.query(Dish).filter(
                Dish.shop_id     == shop.id,
                Dish.is_available == True
            ).all()

            dish_list = []
            for dish in dishes:
                upvotes = db.query(Vote).filter(
                    Vote.dish_id   == dish.id,
                    Vote.vote_type == "up"
                ).count()
                badges = db.query(Badge).filter(
                    Badge.dish_id == dish.id
                ).all()
                dish_list.append({
                    "id"     : dish.id,
                    "name"   : dish.name,
                    "price"  : dish.price,
                    "is_veg" : dish.is_veg,
                    "upvotes": upvotes,
                    "badges" : [b.badge_name for b in badges]
                })

            nearby.append({
                "id"          : shop.id,
                "name"        : shop.name,
                "address"     : shop.address,
                "cuisine_type": shop.cuisine_type,
                "district"    : shop.district,
                "state"       : shop.state,
                "distance_m"  : round(distance, 2),
                "dishes"      : dish_list
            })

    nearby.sort(key=lambda x: x["distance_m"])

    print(f"Nearby shops found: {len(nearby)}")  # ✅ debug

    return {
        "total": len(nearby),
        "shops": nearby
    }