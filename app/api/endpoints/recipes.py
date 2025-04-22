from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Union

from app.core.database import get_db
from app.services import recipe_service, preference_service
from app.schemas.recipe_schema import Recipe, RecipeCard, SaveRecipeRequest

router = APIRouter()  # tags router'da değil, include_router'da belirtilecek

@router.get("/getCategories",
    response_model=List[str],
    summary="Get Recipe Categories",
    description="""
    Retrieves all available recipe categories.
    
    Example:
    ```
    GET /api/v1/getCategories
    
    Response:
    [
        "Main Course",
        "Dessert",
        "Appetizer",
        ...
    ]
    ```
    """)
async def get_categories(db: Session = Depends(get_db)):
    """Tüm yemek kategorilerini getir"""
    return preference_service.get_categories(db)

@router.get("/getRecipeDetails", 
    response_model=Recipe,
    summary="Get Recipe Details",
    description="""
    Retrieves complete details of a specific recipe.
    
    Parameters:
    - **recipe_id**: ID of the recipe
    
    Returns:
    - Recipe name
    - Full instructions
    - List of ingredients
    - Cooking time
    - Nutritional information
    - Category
    
    Example:
    ```
    GET /api/v1/getRecipeDetails?recipe_id=1
    
    Response:
    {
        "recipe_id": 1,
        "recipe_name": "Spaghetti Carbonara",
        "instruction": "1. Boil pasta...",
        "ingredient": "spaghetti, eggs, pecorino...",
        "total_time": 30,
        "calories": 650.5,
        "fat": 24.3,
        "protein": 25.1,
        "carb": 82.4,
        "category": 1
    }
    ```
    """)
def get_recipe_details(
    recipe_id: int = Query(..., description="Recipe ID", example=1),
    db: Session = Depends(get_db)
):
    """
    Tarif detaylarını getir
    - recipe_id: Tarif ID'si
    """
    try:
        return recipe_service.get_recipe_details(db, recipe_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/getRecipeCard",
    response_model=Dict[str, Any],
    summary="Get Recipe Card",
    description="""
    Retrieves specific fields of a recipe as a recipe card.
    
    Parameters:
    - **recipe_id**: ID of the recipe
    - **fields**: Comma-separated list of desired fields
    
    Available fields:
    - recipe_name: Name of the recipe
    - instruction: Cooking instructions
    - total_time: Cooking time in minutes
    - calories: Caloric content
    - fat: Fat content
    - protein: Protein content
    - carb: Carbohydrate content
    - category: Recipe category
    - ingredients: List of ingredients with quantities
    
    Examples:
    ```
    # Basic information
    GET /api/v1/getRecipeCard?recipe_id=1&fields=recipe_name,total_time
    
    Response:
    {
        "recipe_name": "Spaghetti Carbonara",
        "total_time": 30
    }
    
    # Nutritional information
    GET /api/v1/getRecipeCard?recipe_id=1&fields=recipe_name,calories,fat,protein,carb
    
    # Full recipe card
    GET /api/v1/getRecipeCard?recipe_id=1&fields=recipe_name,ingredients,instruction,total_time
    ```
    """)
def get_recipe_card(
    recipe_id: int = Query(..., description="Recipe ID", example=1),
    fields: str = Query(..., 
        description="Comma-separated list of fields",
        example="recipe_name,total_time,calories",
        examples={
            "basic": {
                "summary": "Basic information",
                "value": "recipe_name,total_time"
            },
            "nutrition": {
                "summary": "Nutritional information",
                "value": "recipe_name,calories,fat,protein,carb"
            },
            "full": {
                "summary": "Full recipe card",
                "value": "recipe_name,ingredients,instruction,total_time"
            }
        }
    ),
    db: Session = Depends(get_db)
):
    """
    Tarif kartı bilgilerini getir
    - recipe_id: Tarif ID'si
    - fields: İstenen alanlar (virgülle ayrılmış string veya liste)
    """
    try:
        return recipe_service.get_recipe_card(db, recipe_id, fields)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/getUserSavedRecipes",
    response_model=List[Recipe],
    summary="Get User's Saved Recipes",
    description="""
    Retrieves all recipes saved by a specific user.
    
    Parameters:
    - **user_id**: ID of the user
    
    Returns:
    - List of complete recipe details for all saved recipes
    
    Example:
    ```
    GET /api/v1/getUserSavedRecipes?user_id=user123
    
    Response:
    [
        {
            "recipe_id": 1,
            "recipe_name": "Spaghetti Carbonara",
            "instruction": "1. Boil pasta...",
            "ingredient": "spaghetti, eggs, pecorino...",
            "total_time": 30,
            "calories": 650.5,
            "fat": 24.3,
            "protein": 25.1,
            "carb": 82.4,
            "category": 1
        },
        ...
    ]
    ```
    """)
async def get_user_saved_recipes(
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Kullanıcının kaydettiği tarifleri getir
    - user_id: Kullanıcı ID'si
    """
    try:
        return recipe_service.get_user_saved_recipes(db, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/setUserSavedRecipes",
    response_model=Dict[str, str],
    summary="Set User's Saved Recipes",
    description="""
    Updates the list of recipes saved by a specific user.
    This will replace all currently saved recipes with the new list.
    
    Parameters:
    - **user_id**: ID of the user (query parameter)
    - **recipe_ids**: List of recipe IDs to save (in request body)
    
    Example:
    ```
    POST /api/v1/setUserSavedRecipes?user_id=user123
    
    Request Body:
    {
        "recipe_ids": [1, 2, 3, 4]
    }
    
    Response:
    {
        "message": "Saved recipes updated successfully"
    }
    ```
    """)
async def set_user_saved_recipes(
    user_id: str = Query(..., description="User ID"),
    request: SaveRecipeRequest = None,
    db: Session = Depends(get_db)
):
    """
    Kullanıcının kaydettiği tarifleri güncelle
    - user_id: Kullanıcı ID'si
    - recipe_ids: Kaydedilecek tarif ID'leri listesi
    """
    try:
        recipe_service.set_user_saved_recipes(db, user_id, request.recipe_ids if request else [])
        return {"message": "Saved recipes updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Like/Unlike Endpoints

@router.get("/getUserLikedRecipes",
    response_model=List[Recipe],
    summary="Get User's Liked Recipes",
    description="""
    Retrieves all recipes liked by a specific user.
    
    Parameters:
    - **user_id**: ID of the user
    
    Returns:
    - List of complete recipe details for all liked recipes
    """)
async def get_user_liked_recipes(
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    try:
        return recipe_service.get_user_liked_recipes(db, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/likeRecipe",
    response_model=Dict[str, str],
    summary="Like a Recipe",
    description="""
    Marks a recipe as liked by a user.
    If already liked, updates the timestamp.
    
    Parameters:
    - **user_id**: ID of the user (query parameter)
    - **recipe_id**: ID of the recipe to like (query parameter)
    """)
async def like_recipe(
    user_id: str = Query(..., description="User ID"),
    recipe_id: int = Query(..., description="Recipe ID"),
    db: Session = Depends(get_db)
):
    try:
        recipe_service.like_recipe(db, user_id, recipe_id)
        return {"message": "Recipe liked successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/unlikeRecipe",
    response_model=Dict[str, str],
    summary="Unlike a Recipe",
    description="""
    Removes the like status of a recipe for a user.
    
    Parameters:
    - **user_id**: ID of the user (query parameter)
    - **recipe_id**: ID of the recipe to unlike (query parameter)
    """)
async def unlike_recipe(
    user_id: str = Query(..., description="User ID"),
    recipe_id: int = Query(..., description="Recipe ID"),
    db: Session = Depends(get_db)
):
    try:
        recipe_service.unlike_recipe(db, user_id, recipe_id)
        return {"message": "Recipe unliked successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Dislike/Undislike Endpoints

@router.get("/getUserDislikedRecipes",
    response_model=List[Recipe],
    summary="Get User's Disliked Recipes",
    description="""
    Retrieves all recipes disliked by a specific user.
    
    Parameters:
    - **user_id**: ID of the user
    
    Returns:
    - List of complete recipe details for all disliked recipes
    """)
async def get_user_disliked_recipes(
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    try:
        return recipe_service.get_user_disliked_recipes(db, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/dislikeRecipe",
    response_model=Dict[str, str],
    summary="Dislike a Recipe",
    description="""
    Marks a recipe as disliked by a user.
    If already disliked, updates the timestamp.
    If the recipe was liked, the like is removed.
    
    Parameters:
    - **user_id**: ID of the user (query parameter)
    - **recipe_id**: ID of the recipe to dislike (query parameter)
    """)
async def dislike_recipe(
    user_id: str = Query(..., description="User ID"),
    recipe_id: int = Query(..., description="Recipe ID"),
    db: Session = Depends(get_db)
):
    try:
        recipe_service.dislike_recipe(db, user_id, recipe_id)
        return {"message": "Recipe disliked successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/unDislikeRecipe",
    response_model=Dict[str, str],
    summary="Undislike a Recipe",
    description="""
    Removes the dislike status of a recipe for a user.
    
    Parameters:
    - **user_id**: ID of the user (query parameter)
    - **recipe_id**: ID of the recipe to undislike (query parameter)
    """)
async def undislike_recipe(
    user_id: str = Query(..., description="User ID"),
    recipe_id: int = Query(..., description="Recipe ID"),
    db: Session = Depends(get_db)
):
    try:
        recipe_service.undislike_recipe(db, user_id, recipe_id)
        return {"message": "Recipe undisliked successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Save/Unsave Endpoints

@router.post("/saveRecipe",
    response_model=Dict[str, str],
    summary="Save a Single Recipe",
    description="""
    Saves a single recipe for a user.
    If already saved, updates the timestamp.
    
    Parameters:
    - **user_id**: ID of the user (query parameter)
    - **recipe_id**: ID of the recipe to save (query parameter)
    """)
async def save_recipe(
    user_id: str = Query(..., description="User ID"),
    recipe_id: int = Query(..., description="Recipe ID"),
    db: Session = Depends(get_db)
):
    try:
        recipe_service.save_recipe(db, user_id, recipe_id)
        return {"message": "Recipe saved successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/unsaveRecipe",
    response_model=Dict[str, str],
    summary="Unsave a Single Recipe",
    description="""
    Removes a single saved recipe for a user.
    
    Parameters:
    - **user_id**: ID of the user (query parameter)
    - **recipe_id**: ID of the recipe to unsave (query parameter)
    """)
async def unsave_recipe(
    user_id: str = Query(..., description="User ID"),
    recipe_id: int = Query(..., description="Recipe ID"),
    db: Session = Depends(get_db)
):
    try:
        recipe_service.unsave_recipe(db, user_id, recipe_id)
        return {"message": "Recipe unsaved successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Surprise Recipe Endpoint

@router.get("/getSurpriseRecipe",
    response_model=Recipe,
    summary="Get Surprise Recipe",
    description="""
    Retrieves a random recipe object, potentially excluding those disliked by the user.
    
    Parameters:
    - **user_id**: ID of the user (query parameter)
    
    Returns:
    - A single random Recipe object
    """)
async def get_surprise_recipe(
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    try:
        recipe = recipe_service.get_surprise_recipe_id(db, user_id)
        return recipe
    except ValueError as e:
        # If user not found or no recipes exist at all
        raise HTTPException(status_code=404, detail=str(e)) 