from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from app.core.database import get_db
from app.schemas.ingredient import UserIngredients, IngredientResponse, UserAllergies, InventoryItem
from app.services import ingredient_service, preference_service
from app.models.models import User
from app.schemas.preference_schema import UserPreferences

router = APIRouter(tags=["ingredients"])

@router.get("/getIngredients", response_model=List[str])
async def get_ingredients(
    db: Session = Depends(get_db)
):
    """
    Tüm malzemeleri getir
    """
    return ingredient_service.get_ingredient_names(db)

@router.get("/getUserIngredients")
async def get_user_ingredients(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Kullanıcının malzemelerini getir
    """
    user = ingredient_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    ingredients = ingredient_service.get_user_ingredients(db, user_id)
    return UserIngredients(
        user_id=user_id,
        ingredients=[InventoryItem(**item) for item in ingredients]
    )

@router.post("/setUserIngredients")
async def set_user_ingredients(
    ingredients: UserIngredients,
    db: Session = Depends(get_db)
):
    """
    Kullanıcının malzemelerini güncelle
    """
    user = ingredient_service.get_user(db, ingredients.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    updated_ingredients = ingredient_service.set_user_ingredients(db, ingredients)
    return UserIngredients(
        user_id=ingredients.user_id,
        ingredients=[InventoryItem(**item) for item in updated_ingredients]
    )

# Alerji endpoint'leri
@router.get("/getAllergies", response_model=List[str])
async def get_all_allergies(
    db: Session = Depends(get_db)
):
    """
    Sistemdeki tüm alerjen malzemeleri getir
    """
    return ingredient_service.get_all_allergies(db)

@router.get("/getUserAllergies")
async def get_user_allergies(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Kullanıcının alerjik olduğu malzemeleri getir
    """
    user = ingredient_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    allergies = ingredient_service.get_user_allergies(db, user_id)
    return UserAllergies(user_id=user_id, allergies=allergies)

@router.post("/setUserAllergies")
async def set_user_allergies(
    allergies: UserAllergies,
    db: Session = Depends(get_db)
):
    """
    Kullanıcının alerjik olduğu malzemeleri güncelle
    """
    user = ingredient_service.get_user(db, allergies.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    updated_allergies = ingredient_service.set_user_allergies(db, allergies)
    return UserAllergies(user_id=allergies.user_id, allergies=updated_allergies)

@router.get("/getCategories", response_model=List[str])
async def get_categories(
    db: Session = Depends(get_db)
):
    """
    Tüm kategorileri getir
    """
    return preference_service.get_categories(db)

@router.get("/getPreferences", response_model=List[str])
async def get_preferences(
    db: Session = Depends(get_db)
):
    """
    Tüm tercihleri getir
    """
    return preference_service.get_preferences(db)

@router.get("/getUserPreferences", response_model=List[str])
async def get_user_preferences(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Kullanıcının tercihlerini getir
    """
    return preference_service.get_user_preferences(db, user_id)

@router.post("/setUserPreferences", response_model=List[str])
async def set_user_preferences(
    preferences: UserPreferences,
    db: Session = Depends(get_db)
):
    """
    Kullanıcının tercihlerini güncelle
    """
    return preference_service.set_user_preferences(db, preferences)