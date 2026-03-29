from typing import Optional

from database import get_db
from fastapi import APIRouter, Depends, Query
from models.badge import Badge
from models.dish import Dish
from models.shop import Shop
from models.vote import Vote
from sqlalchemy.orm import Session

router = APIRouter(prefix="/filter", tags=["Dietary Filter & Mood"])


# --- Dietary Filter ---
@router.get("/dietary")
def dietary_filter(
    is_vegan: Optional[bool] = Query(None),
    is_gluten_free: Optional[bool] = Query(None),
    is_diabetic_friendly: Optional[bool] = Query(None),
    is_veg: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Dish).filter(Dish.is_available == True)

    if is_vegan is not None:
        query = query.filter(Dish.is_vegan == is_vegan)
    if is_gluten_free is not None:
        query = query.filter(Dish.is_gluten_free == is_gluten_free)
    if is_diabetic_friendly is not None:
        query = query.filter(Dish.is_diabetic_friendly == is_diabetic_friendly)
    if is_veg is not None:
        query = query.filter(Dish.is_veg == is_veg)

    dishes = query.all()

    if not dishes:
        return {"message": "No dishes found", "results": []}

    result = []
    for d in dishes:
        s = db.query(Shop).filter(Shop.id == d.shop_id).first()
        upvotes = (
            db.query(Vote).filter(Vote.dish_id == d.id, Vote.vote_type == "up").count()
        )
        badges = db.query(Badge).filter(Badge.dish_id == d.id).all()

        result.append(
            {
                "dish_id": d.id,
                "name": d.name,
                "price": d.price,
                "spice_level": d.spice_level,
                "is_veg": d.is_veg,
                "is_vegan": d.is_vegan,
                "is_gluten_free": d.is_gluten_free,
                "is_diabetic_friendly": d.is_diabetic_friendly,
                "upvotes": upvotes,
                "badges": [b.badge_name for b in badges],
                "shop_name": s.name if s else "Unknown",
            }
        )

    result.sort(key=lambda x: x["upvotes"], reverse=True)

    return {"total": len(result), "results": result}


# --- Mood Based Recommendation ---
@router.get("/mood")
def mood_filter(
    mood: str = Query(..., description="spicy / light / sweet / heavy "),
    db: Session = Depends(get_db),
):
    # mood maps to spice level and dish type
    mood_map = {
    "spicy": {"spice_level": "high"},                # spicy → high spice_level
    "light": {"spice_level": "low", "is_veg": True}, # light → low spice & veg
    "sweet": {"spice_level": "low"},                 # sweet → low spice (desserts/drinks)
    "heavy": {"spice_level": "medium"},  
    }

    if mood not in mood_map:
        return {"message": "Mood not found", "valid_moods": list(mood_map.keys())}

    filters = mood_map[mood]
    query = db.query(Dish).filter(Dish.is_available == True)

    if "spice_level" in filters:
        query = query.filter(Dish.spice_level == filters["spice_level"])
    if "is_veg" in filters:
        query = query.filter(Dish.is_veg == filters["is_veg"])

    dishes = query.all()

    if not dishes:
        return {"message": f"No dishes found for mood: {mood}", "results": []}

    result = []
    for d in dishes:
        s = db.query(Shop).filter(Shop.id == d.shop_id).first()
        upvotes = (
            db.query(Vote).filter(Vote.dish_id == d.id, Vote.vote_type == "up").count()
        )

        result.append(
            {
                "dish_id": d.id,
                "name": d.name,
                "price": d.price,
                "spice_level": d.spice_level,
                "is_veg": d.is_veg,
                "upvotes": upvotes,
                "shop_name": s.name if s else "Unknown",
            }
        )

    result.sort(key=lambda x: x["upvotes"], reverse=True)

    return {"mood": mood, "total": len(result), "results": result}
