from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from auth import decode_token
from models.badge import Badge
from models.dish import Dish
from models.vote import Vote
from database import get_db
from schemas.vote import VoteSchema


router = APIRouter(prefix="/votes", tags=["Votes & Badges"])

def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token missing")
    token = authorization.split(" ")[1]
    data = decode_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return data
#vote 
@router.post("/vote")
def vote_dish(
    data: VoteSchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    dish = db.query(Dish).filter(Dish.id == data.dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")

    existing = db.query(Vote).filter(
        Vote.user_id == current_user["user_id"],
        Vote.dish_id == data.dish_id
    ).first()

    if existing:
        if existing.vote_type == data.vote_type:
            raise HTTPException(status_code=400, detail="You already voted this")
        # change vote
        existing.vote_type = data.vote_type
        db.commit()
        assign_badge(data.dish_id, db)
        return {"message": "Vote changed!"}

    # new vote
    vote = Vote(
        user_id=current_user["user_id"],
        dish_id=data.dish_id,
        vote_type=data.vote_type
    )
    db.add(vote)
    db.commit()
    assign_badge(data.dish_id, db)
    return {"message": "Vote added!"}
#get votes fro a dish
@router.get("/{dish_id}")
def get_votes(dish_id:int,db:Session=Depends(get_db)):
    upvotes = db.query(Vote).filter(
              Vote.dish_id == dish_id,
              Vote.vote_type=="up").count()
    downvotes = db.query(Vote).filter(
              Vote.dish_id == dish_id,
              Vote.vote_type=="down").count()
    badges = db.query(Badge).filter(Badge.dish_id == dish_id).all()
    return{
        "dish_id":dish_id,
        "upvotes":upvotes,
        "downvotes":downvotes,
        "badges":[b.badge_name for b in badges]
    }
# badge working 
def assign_badge(dish_id,db:Session):
    upvotes = db.query(Vote).filter(
        Vote.dish_id == dish_id,
        Vote.vote_type =="up"
    ).count()
    badge_rules={
         "All Time Fav" : upvotes >= 100,
        "Masterpiece"  : upvotes >= 500,
        "Trending"     : upvotes >= 50,
        "Hidden Gem"   : upvotes >= 20,
        "Crowd Pleaser": upvotes >= 10,
    }
    for badge_name,earned in badge_rules.items():
        if earned:
            exists = db.query(Badge).filter(
                Badge.dish_id ==dish_id,
                Badge.badge_name== badge_name
            ).first()
            if not exists:
                db.add(Badge(dish_id=dish_id,badge_name=badge_name))
    db.commit()