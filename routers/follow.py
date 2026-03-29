from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from auth import decode_token
from database import get_db
from models.follow import Follow
from models.user import User


router = APIRouter(prefix="/follow", tags=["User Follow"])
def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token missing")
    token = authorization.split(" ")[1]
    data = decode_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return data
@router.post("/{user_id}")
def follow_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if user_id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="You cannot follow yourself")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    existing = db.query(Follow).filter(
    Follow.follower_id  == current_user["user_id"],
    Follow.following_id == user_id
    ).first()
    if existing:
     db.delete(existing)
     db.commit()
     return {"message": f"Unfollowed {user.name}!"}

    # follow
    follow = Follow(
        follower_id  = current_user["user_id"],
        following_id = user_id
    )
    db.add(follow)
    db.commit()
    return {"message": f"Now following {user.name}!"}

@router.get("/followers/{user_id}")
def get_followers(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    followers = db.query(Follow).filter(
        Follow.following_id == user_id
    ).all()

    result = []
    for f in followers:
        follower = db.query(User).filter(User.id == f.follower_id).first()
        result.append({
            "user_id"   : follower.id,
            "name"      : follower.name,
            "followed_at": f.created_at
        })

    return {
        "user"      : user.name,
        "total"     : len(result),
        "followers" : result
    }
@router.get("/following/{user_id}")
def get_following(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    followings = db.query(Follow).filter(
        Follow.follower_id == user_id
    ).all()

    result = []
    for f in followings:
        following = db.query(User).filter(User.id == f.following_id).first()
        result.append({
            "user_id"    : following.id,
            "name"       : following.name,
            "followed_at": f.created_at
        })

    return {
        "user"      : user.name,
        "total"     : len(result),
        "following" : result
    }
#counts
@router.get("/stats/{user_id}")
def get_follow_stats(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    followers_count  = db.query(Follow).filter(Follow.following_id == user_id).count()
    following_count  = db.query(Follow).filter(Follow.follower_id  == user_id).count()

    return {
        "user"           : user.name,
        "followers"      : followers_count,
        "following"      : following_count
    }