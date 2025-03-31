from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Union

from app.core.database import get_db
from app.services import recipe_service
from app.schemas.recipe_schema import Recipe, RecipeCard

router = APIRouter()  # tags router'da değil, include_router'da belirtilecek

@router.get("/getRecipeDetails", 
    response_model=Recipe,
    summary="Get Recipe Details",
    description="""
    Retrieves detailed information about a specific recipe.
    
    Parameters:
    - **recipe_id**: ID of the recipe to retrieve
    
    Returns all available information about the recipe including:
    - Recipe name
    - Instructions
    - Ingredients
    - Nutritional information (calories, fat, protein, carbs)
    - Total cooking time
    - Category
    
    Example:
    ```
    GET /api/v1/getRecipeDetails?recipe_id=1
    ```
    """)
def get_recipe_details(
    recipe_id: int = Query(..., description="The ID of the recipe to retrieve", example=1),
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
    - **fields**: Comma-separated list of fields to include in the response
    
    Available fields:
    - recipe_name: Name of the recipe
    - instruction: Cooking instructions
    - total_time: Total cooking time in minutes
    - calories: Caloric content
    - fat: Fat content
    - protein: Protein content
    - carb: Carbohydrate content
    - category: Recipe category
    - ingredients: List of ingredients with quantities
    
    Examples:
    ```
    # Get only recipe name
    GET /api/v1/getRecipeCard?recipe_id=1&fields=recipe_name
    
    # Get multiple fields
    GET /api/v1/getRecipeCard?recipe_id=1&fields=recipe_name,total_time,calories
    
    # Get recipe with ingredients
    GET /api/v1/getRecipeCard?recipe_id=1&fields=recipe_name,ingredients
    ```
    """)
def get_recipe_card(
    recipe_id: int = Query(..., description="The ID of the recipe to retrieve", example=1),
    fields: str = Query(..., 
        description="Comma-separated list of fields to include", 
        example="recipe_name,total_time,calories",
        examples={
            "basic": {
                "summary": "Basic recipe information",
                "value": "recipe_name,total_time"
            },
            "nutrition": {
                "summary": "Nutritional information",
                "value": "recipe_name,calories,fat,protein,carb"
            },
            "full": {
                "summary": "Full recipe card with ingredients",
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