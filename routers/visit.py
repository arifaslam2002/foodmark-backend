from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from  sqlalchemy.orm import Session
from auth import decode_token
from database import get_db
from models.shop import Shop
from models.visit import Visit


router = APIRouter(prefix="/visits", tags=["Most Visited Shops"])

def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token missing")
    token = authorization.split(" ")[1]
    data = decode_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return data
@router.post("/shop/{shop_id}")
def visit_shop(
    shop_id: int,
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")  
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
    existing = db.query(Visit).filter(
        Visit.shop_id  == shop_id,
        Visit.user_id  == current_user["user_id"],
        Visit.created_at >= today_start
    ).first()

    if existing:
        return {"message": "Already logged visit today!"}

    visit = Visit(
        shop_id = shop_id,
        user_id = current_user["user_id"]
    )
    db.add(visit)
    db.commit()
    return {"message": f"Visit logged for {shop.name}!"}
#over all
@router.get("/most-visited")
def most_visited(
    limit: int = Query(10, description="How many results"),
    db: Session = Depends(get_db)
):
    shops = db.query(Shop).filter(Shop.is_verified == True).all()

    if not shops:
        return {"message": "No shops found", "results": []}

    result = []
    for s in shops:
        visit_count = db.query(Visit).filter(Visit.shop_id == s.id).count()
        result.append({
            "shop_id"    : s.id,
            "name"       : s.name,
            "address"    : s.address,
            "cuisine"    : s.cuisine_type,
            "district"   : s.district,
            "state"      : s.state,
            "total_visits": visit_count
        })

    result.sort(key=lambda x: x["total_visits"], reverse=True)
    for i, r in enumerate(result[:limit]):
        r["rank"] = i + 1

    return {
        "total"  : len(result),
        "results": result[:limit]
    }
# --- Most visited this week ---
@router.get("/this-week")
def most_visited_week(
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    week_ago = datetime.utcnow() - timedelta(days=7)
    shops    = db.query(Shop).filter(Shop.is_verified == True).all()

    result = []
    for s in shops:
        visit_count = db.query(Visit).filter(
            Visit.shop_id    == s.id,
            Visit.created_at >= week_ago
        ).count()
        result.append({
            "shop_id"     : s.id,
            "name"        : s.name,
            "address"     : s.address,
            "total_visits": visit_count
        })

    result.sort(key=lambda x: x["total_visits"], reverse=True)
    for i, r in enumerate(result[:limit]):
        r["rank"] = i + 1

    return {
        "period" : "This Week",
        "results": result[:limit]
    }
# --- Most visited today ---
@router.get("/today")
def most_visited_today(
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
    shops       = db.query(Shop).filter(Shop.is_verified == True).all()

    result = []
    for s in shops:
        visit_count = db.query(Visit).filter(
            Visit.shop_id    == s.id,
            Visit.created_at >= today_start
        ).count()
        result.append({
            "shop_id"     : s.id,
            "name"        : s.name,
            "address"     : s.address,
            "total_visits": visit_count
        })

    result.sort(key=lambda x: x["total_visits"], reverse=True)
    for i, r in enumerate(result[:limit]):
        r["rank"] = i + 1

    return {
        "period" : "Today",
        "results": result[:limit]
    }
@router.get("/my-history")
def my_visit_history(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    visits = db.query(Visit).filter(
        Visit.user_id == current_user["user_id"]
    ).order_by(Visit.created_at.desc()).all()

    if not visits:
        return {"message": "No visits yet", "history": []}

    result = []
    for v in visits:
        shop = db.query(Shop).filter(Shop.id == v.shop_id).first()
        result.append({
            "shop_id"   : v.shop_id,
            "shop_name" : shop.name if shop else "Unknown",
            "visited_at": v.created_at
        })

    return {
        "total"  : len(result),
        "history": result
    }