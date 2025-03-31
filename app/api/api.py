from fastapi import APIRouter
from app.api.endpoints import users, ingredients

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(ingredients.router, tags=["ingredients"]) 