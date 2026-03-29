from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models.user_badge import UserBadge
from database import get_db
from models.chat import Chat
from models.review import Review
from models.user import User
from models.vote import Vote


router = APIRouter(prefix="/ranking", tags=["User Ranking"])
def calculate_trust_score(user_id:int,db:Session) ->float:
 #trust review be in location review 
 trust_review=db.query(Review).filter(
   Review.user_id == user_id,
   Review.is_trusted
 ).count()
 #review count
 total_reviews = db.query(Review).filter(
  Review.user_id == user_id
 ).count()
 #vote count
 total_votes =db.query(Vote).filter(
  Vote.user_id == user_id
 ).count()
 #chat count
 total_chats =db.query(Chat).filter(
  Chat.user_id == user_id
 ).count()
 raw_score = (trust_review*5)+(total_reviews*2)+(total_votes*1)+(total_chats*1)
 return raw_score,trust_review,total_reviews,total_votes,total_chats
def scale_to_10(score:float,max_score:float)-> float:
  if max_score == 0:
       return 0
  scaled =(score/max_score)*10
  return round(min(scaled,10),1)

@router.get("/users")
def get_user_rankings(db:Session=Depends(get_db)):
   users =db.query(User).filter(User.role == "customer").all()
   if not users:
      return {"message": "No users found", "rankings": []}
   users_scores =[]
   for user in users:
     raw_score, trusted, total_rev, votes, chats = calculate_trust_score(user.id, db)
     users_scores.append({
        "user_id"       : user.id,
            "name"          : user.name,
            "raw_score"     : raw_score,
            "trusted_reviews": trusted,
            "total_reviews" : total_rev,
            "total_votes"   : votes,
            "total_chats"   : chats
     })

   #max score
   max_score = max(u["raw_score"] for u in users_scores)
   #scale & ranks
   for u in users_scores:
     scaled =scale_to_10(u["raw_score"],max_score)
     u["trust_score"] = scaled if scaled > 0 else 1.0
     del u["raw_score"]

   users_scores.sort(key=lambda x:x["trust_score"],reverse=True)
   for i ,u in enumerate(users_scores):
      u["rank"] = i+1
   return{
      "total":len(users_scores),
      "rankings":users_scores
   }
@router.get("/users/{user_id}")
def get_user_rank(user_id:int,db:Session =Depends(get_db)):
   user = db.query(User).filter(User.id == user_id).first()
   if not user:
        return {"message": "User not found"}
   raw_score, trusted, total_rev, votes, chats = calculate_trust_score(user_id, db)
   all_users = db.query(User).filter(User.role == "customer")
   all_scores=[]
   for u in all_users:
      s,_,_,_,_ =calculate_trust_score(u.id,db)
      all_scores.append({"user_id":u.id,"score":s})

      max_score = max(u["score"] for u in all_scores)
      trust_score = scale_to_10(raw_score, max_score)
      trust_score = trust_score if trust_score > 0 else 1.0

    # find rank position
      all_scores.sort(key=lambda x: x["score"], reverse=True)
      rank = next(i + 1 for i, u in enumerate(all_scores) if u["user_id"] == user_id)

      return {
        "user_id"        : user.id,
        "name"           : user.name,
        "rank"           : rank,
        "trust_score"    : trust_score,
        "trusted_reviews": trusted,
        "total_reviews"  : total_rev,
        "total_votes"    : votes,
        "total_chats"    : chats
    }

from models.user_badge import UserBadge
from models.dish import Dish

@router.get("/badges/{user_id}")
def get_user_badges(user_id: int, db: Session = Depends(get_db)):
    badges = db.query(UserBadge).filter(UserBadge.user_id == user_id).all()
    if not badges:
        return {"message": "No badges yet", "badges": []}

    result = []
    for b in badges:
        dish = db.query(Dish).filter(Dish.id == b.dish_id).first()
        result.append({
            "badge"     : b.badge_name,
            "dish_id"   : b.dish_id,
            "dish_name" : dish.name if dish else "Unknown",  # ✅ dish name
            "earned_at" : b.created_at
        })

    return {
        "total" : len(result),
        "badges": result
    }
