from database import Base, engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from routers import (
    announcement,
    chat,
    dish,
    dish_journey,
    dish_of_day,
    feedback,
    nearby,
    ranking,
    rating,
    report,
    review,
    search,
    shop,
    timing,
    trending,
    user,
    vote,
    consensus,
    follow,
    visit,
    profile,
    filter,
    battle
)

app = FastAPI(title="Foodmark")

# ✅ CORS added here
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://foodmark-frontend-665v.vercel.app",  # ✅ your vercel URL
        "https://foodmark-frontend.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(user.router)
app.include_router(shop.router)
app.include_router(review.router)
app.include_router(dish.router)
app.include_router(vote.router)
app.include_router(chat.router)
app.include_router(nearby.router)
app.include_router(feedback.router)
app.include_router(ranking.router)
app.include_router(trending.router)
app.include_router(search.router)
app.include_router(timing.router)
app.include_router(rating.router)
app.include_router(dish_journey.router)
app.include_router(report.router)
app.include_router(announcement.router)
app.include_router(dish_of_day.router)
app.include_router(consensus.router)
app.include_router(follow.router)
app.include_router(visit.router)
app.include_router(profile.router)
app.include_router(filter.router)
app.include_router(battle.router)
@app.get("/test-db")
def test_db():
    try:
        with engine.connect() as conn:
            return {"message": "Database connected! ✅"}
    except Exception as e:
        return {"error": str(e)}
@app.get("/")
def home():
    return {"message": "Foodmark is running!"}

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title="Foodmark", version="1.0.0", routes=app.routes)
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }
    for path in schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi