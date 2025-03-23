from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.recipe_service import (
    get_all_categories, 
    get_all_labels, 
    get_recipe_details, 
    get_recipe_card, 
    get_user_preferences, 
    set_user_preferences, 
    query_recipes,
    get_all_ingredients,
    get_all_allergies,
    get_user_allergies,
    set_user_allergies,
    get_user_recommendations,
    get_recipes_by_query
)
from app.schemas.recipe_schema import RecipeDetails, RecipeCard, UserPreferences, RecipeQuery, UserAllergies
from typing import List, Dict, Any

router = APIRouter()

@router.get("/getCategories", 
           summary="Get all recipe categories",
           description="Returns a list of all available recipe categories in the system.",
           response_description="List of category objects with id and name")
def get_categories(db: Session = Depends(get_db)):
    """
    Retrieve all recipe categories.
    
    This endpoint returns all categories that recipes can belong to, such as:
    - Breakfast
    - Lunch
    - Dinner
    - Dessert
    - etc.
    """
    return get_all_categories(db)

@router.get("/getLabels", 
           summary="Get all dietary preference labels",
           description="Returns a list of all available dietary preference labels/tags.",
           response_description="List of preference objects with id and name")
def get_labels(db: Session = Depends(get_db)):
    """
    Retrieve all dietary preference labels.
    
    This endpoint returns all possible dietary preferences, such as:
    - Vegan
    - Vegetarian
    - Gluten-free
    - Dairy-free
    - etc.
    """
    return get_all_labels(db)

@router.get("/getRecipeDetails/{recipe_id}", 
           summary="Get recipe details by ID",
           description="Returns detailed information about a specific recipe.",
           response_description="Detailed recipe object with ingredients and nutritional information")
def recipe_details(recipe_id: int, db: Session = Depends(get_db)):
    """
    Retrieve full details of a recipe by its ID.
    
    This endpoint returns comprehensive information about a recipe, including:
    - Recipe name and instructions
    - List of ingredients with quantities and units
    - Nutritional information (calories, protein, fat, carbs)
    - Category
    - Preparation time
    
    If the recipe is not found, a 404 error is returned.
    """
    recipe = get_recipe_details(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe

@router.post("/getRecipeDetails", 
           summary="Get recipe details (POST)",
           description="Alternative POST method to get detailed recipe information.",
           response_description="Detailed recipe object with ingredients and nutritional information")
def recipe_details_post(payload: RecipeDetails, db: Session = Depends(get_db)):
    """
    Retrieve full details of a recipe by its ID (POST method).
    
    Functionally identical to the GET method but accepts a POST request with the recipe_id in the request body.
    """
    recipe = get_recipe_details(db, payload.recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe

@router.get("/getRecipeCard/{recipe_id}", 
           summary="Get recipe card with specific fields",
           description="Returns selected fields of a recipe for displaying in a card format.",
           response_description="Partial recipe object with requested fields only")
def recipe_card_get(
    recipe_id: int, 
    fields: List[str] = Query(..., description="List of fields to include in the response. Can include: recipe_name, calories, total_time, ingredients, etc."),
    db: Session = Depends(get_db)
):
    """
    Retrieve specific fields of a recipe by ID (GET method).
    
    This endpoint allows requesting only specific fields of a recipe, useful for displaying:
    - Recipe cards in a list
    - Summary information
    - Specific recipe attributes
    
    Example: `/getRecipeCard/1?fields=recipe_name&fields=calories&fields=total_time`
    
    If the recipe is not found, a 404 error is returned.
    """
    result = get_recipe_card(db, recipe_id, fields)
    if not result:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return result

@router.post("/getRecipeCard", 
           summary="Get recipe card (POST)",
           description="Alternative POST method to get specific fields of a recipe.",
           response_description="Partial recipe object with requested fields only")
def recipe_card_post(payload: RecipeCard, db: Session = Depends(get_db)):
    """
    Retrieve specific fields of a recipe by ID (POST method).
    
    Functionally identical to the GET method but accepts a POST request with the recipe_id 
    and fields in the request body.
    """
    result = get_recipe_card(db, payload.recipe_id, payload.fields)
    if not result:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return result

@router.get("/getUserPreferences/{user_id}", 
           summary="Get user dietary preferences",
           description="Returns the dietary preferences for a specific user.",
           response_description="User preferences object with preference IDs")
def user_preferences(user_id: str, db: Session = Depends(get_db)):
    """
    Retrieve user dietary preferences by user ID.
    
    This endpoint returns the dietary preference IDs for a user.
    
    If preferences are not found for the user, a 404 error is returned.
    """
    prefs = get_user_preferences(db, user_id)
    if not prefs:
        raise HTTPException(status_code=404, detail="Preferences not found for user")
    return prefs

@router.post("/setUserPreferences", 
           summary="Set user dietary preferences",
           description="Updates the dietary preferences for a user.",
           response_description="Success message and updated preferences")
def set_preferences(preferences: UserPreferences, db: Session = Depends(get_db)):
    """
    Set or update user dietary preferences.
    
    This endpoint allows setting preference IDs for a user.
    The request should include the user_id and a list of preference IDs.
    """
    return set_user_preferences(db, preferences)

@router.post("/query", 
           summary="Query recipes (POST)",
           description="Searches for recipes based on various criteria using POST method.",
           response_description="List of matching recipes")
def query(payload: RecipeQuery, db: Session = Depends(get_db)):
    """
    Query recipes based on various criteria (POST method).
    
    This endpoint allows searching for recipes by:
    - Recipe name
    - Ingredients
    - Other criteria
    
    The results can be sorted by various fields in ascending or descending order.
    """
    return query_recipes(db, payload.query, payload.sortBy)

@router.get("/getIngredients", 
           summary="Get all ingredients",
           description="Returns a list of all available ingredients in the system.",
           response_description="List of ingredients with ID and name")
def get_ingredients(db: Session = Depends(get_db)):
    """
    Retrieve all ingredients.
    
    This endpoint returns a list of all ingredients available in the system.
    """
    return get_all_ingredients(db)

@router.get("/getAllergies", 
           summary="Get all possible allergies",
           description="Returns a list of all ingredients that can be allergies.",
           response_description="List of ingredients with ID and name")
def get_allergies(db: Session = Depends(get_db)):
    """
    Retrieve all possible allergies.
    
    This endpoint returns all ingredients that users can select as allergies.
    In this system, allergies are represented as ingredients that users want to avoid.
    """
    return get_all_allergies(db)

@router.get("/getUserAllergies", 
           summary="Get user allergies",
           description="Returns the allergies for a specific user.",
           response_description="User allergies object with list of ingredient IDs")
def get_user_allergies_endpoint(
    user_id: str = Query(..., description="The unique identifier of the user"), 
    db: Session = Depends(get_db)
):
    """
    Retrieve allergies for a specific user.
    
    This endpoint returns a list of ingredient IDs that the user has marked as allergies.
    """
    return get_user_allergies(db, user_id)

@router.post("/setUserAllergies", 
           summary="Set user allergies",
           description="Updates the allergies for a user.",
           response_description="Success message and updated allergies")
def set_user_allergies_endpoint(allergies: UserAllergies, db: Session = Depends(get_db)):
    """
    Set or update user allergies.
    
    This endpoint allows setting a list of ingredient IDs that the user is allergic to.
    The request should include the user_id and a list of ingredient IDs.
    """
    return set_user_allergies(db, allergies)

@router.get("/getUserRecommendations", 
           summary="Get recipe recommendations",
           description="Returns personalized recipe recommendations for a user.",
           response_description="List of recommended recipes")
def get_recommendations(
    user_id: str = Query(None, description="The unique identifier of the user. If not provided, general recommendations are returned."), 
    db: Session = Depends(get_db)
):
    """
    Retrieve personalized recipe recommendations for a user.
    
    This endpoint returns a list of recipes recommended for a specific user, based on:
    - User preferences
    - User allergies
    - Popular recipes
    
    If user_id is not provided, general recommendations are returned.
    """
    return get_user_recommendations(db, user_id)

@router.get("/getPreferences", 
           summary="Get all dietary preferences",
           description="Alternative endpoint to get all dietary preference labels/tags.",
           response_description="List of preference objects with id and name")
def get_preferences(db: Session = Depends(get_db)):
    """
    Retrieve all dietary preferences.
    
    This endpoint is identical to `/getLabels` and returns all available dietary preferences.
    """
    return get_all_labels(db)

@router.get("/query", 
           summary="Query recipes (GET)",
           description="Searches for recipes based on various criteria using GET method.",
           response_description="List of matching recipes")
def query_get(
    query: str = Query(None, description="JSON-encoded query string with search criteria"), 
    sortBy_field: str = Query(None, description="Field to sort results by (e.g., recipe_name, calories)"), 
    sortBy_direction: str = Query(None, description="Sort direction: 'asc' or 'desc'"), 
    db: Session = Depends(get_db)
):
    """
    Query recipes based on various criteria (GET method).
    
    This endpoint is functionally identical to the POST /query endpoint but accepts 
    parameters via query string instead of request body.
    
    The query parameter should be a JSON-encoded string containing search criteria.
    """
    return get_recipes_by_query(db, query, sortBy_field, sortBy_direction) 