from fastapi import APIRouter
from app.api.endpoints import users, ingredients, recipes

api_router = APIRouter(prefix="/api/v1")

# Her router'ı ayrı ayrı ekle ve tag'lerini belirt
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(ingredients.router, tags=["ingredients"])
api_router.include_router(recipes.router, tags=["recipes"])