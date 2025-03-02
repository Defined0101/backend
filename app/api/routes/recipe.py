from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.recipe_service import (
    get_all_categories, 
    get_all_labels, 
    get_recipe_details, 
    get_recipe_card, 
    get_user_preferences, 
    set_user_preferences, 
    query_recipes
)
from app.schemas.recipe_schema import RecipeDetails, RecipeCard, UserPreferences, RecipeQuery
from typing import List, Dict, Any

router = APIRouter()

@router.get("/getCategories")
def get_categories(db: Session = Depends(get_db)):
    """Get all categories"""
    return get_all_categories(db)

@router.get("/getLabels")
def get_labels(db: Session = Depends(get_db)):
    """Get all labels/preferences"""
    return get_all_labels(db)

@router.get("/getRecipeDetails/{recipe_id}")
def recipe_details(recipe_id: int, db: Session = Depends(get_db)):
    """Get full details of a recipe by ID"""
    recipe = get_recipe_details(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe

@router.post("/getRecipeDetails")
def recipe_details_post(payload: RecipeDetails, db: Session = Depends(get_db)):
    """Get full details of a recipe by ID (POST method)"""
    recipe = get_recipe_details(db, payload.recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe

@router.get("/getRecipeCard/{recipe_id}")
def recipe_card_get(recipe_id: int, fields: List[str], db: Session = Depends(get_db)):
    """Get specific fields of a recipe by ID (GET method)
    
    Example: /getRecipeCard/1?fields=name&fields=calories&fields=total_time
    """
    result = get_recipe_card(db, recipe_id, fields)
    if not result:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return result

@router.post("/getRecipeCard")
def recipe_card_post(payload: RecipeCard, db: Session = Depends(get_db)):
    """Get specific fields of a recipe by ID (POST method)"""
    result = get_recipe_card(db, payload.recipe_id, payload.fields)
    if not result:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return result

@router.get("/getUserPreferences/{user_id}")
def user_preferences(user_id: int, db: Session = Depends(get_db)):
    """Get user preferences by user ID"""
    prefs = get_user_preferences(db, user_id)
    if not prefs:
        raise HTTPException(status_code=404, detail="Preferences not found for user")
    return prefs

@router.post("/setUserPreferences")
def set_preferences(preferences: UserPreferences, db: Session = Depends(get_db)):
    """Set or update user preferences"""
    return set_user_preferences(db, preferences)

@router.post("/query")
def query(payload: RecipeQuery, db: Session = Depends(get_db)):
    """Query recipes based on various criteria"""
    return query_recipes(db, payload.query, payload.sortBy) 