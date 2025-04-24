from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from app.core.database import get_db
from app.schemas.ingredient_schema import UserIngredients, IngredientResponse, UserAllergies, InventoryItem
from app.services import ingredient_service, preference_service
from app.models.models import User
from app.schemas.preference_schema import UserPreferences

router = APIRouter(tags=["ingredients"])

@router.get("/getIngredients", 
    response_model=IngredientResponse,
    summary="Get All Ingredients",
    description="""
    Retrieves a paginated list of all available ingredients in the system, including their default unit.
    If the default unit is not set, it defaults to 'piece'.
    
    Parameters:
    - **page**: Page number (default: 1)
    - **page_size**: Number of items per page (default: 50)
    - **search**: Optional search term to filter ingredients
    
    Returns a paginated list of ingredients with metadata.
    
    Example:
    ```
    GET /api/v1/getIngredients?page=1&page_size=20
    
    Response:
    {
        "items": [
            {"ingr_id": 1, "ingr_name": "apple", "default_unit": "piece"},
            {"ingr_id": 2, "ingr_name": "banana", "default_unit": "piece"},
            {"ingr_id": 3, "ingr_name": "flour", "default_unit": "g"},
            ...
        ],
        "total": 500,
        "page": 1,
        "page_size": 20,
        "total_pages": 25,
        "has_next": true,
        "has_previous": false
    }
    ```
    """)
async def get_ingredients(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term"),
    db: Session = Depends(get_db)
):
    return ingredient_service.get_all_ingredients(db, page, page_size, search)

@router.get("/getUserIngredients",
    summary="Get User's Ingredients",
    description="""
    Retrieves all ingredients in a user's inventory with quantities.
    
    Parameters:
    - **user_id**: ID of the user
    
    Example:
    ```
    GET /api/v1/getUserIngredients?user_id=user123
    
    Response:
    {
        "user_id": "user123",
        "ingredients": [
            {
                "ingr_name": "tomato",
                "quantity": 5,
                "unit": "piece"
            },
            {
                "ingr_name": "onion",
                "quantity": 2,
                "unit": "piece"
            }
        ]
    }
    ```
    """)
async def get_user_ingredients(
    user_id: str = Query(..., description="User ID", example="user123"),
    db: Session = Depends(get_db)
):
    user = ingredient_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    ingredients = ingredient_service.get_user_ingredients(db, user_id)
    return UserIngredients(user_id=user_id, ingredients=ingredients)

@router.post("/setUserIngredients",
    summary="Update User's Ingredients",
    description="""
    Updates or sets the ingredients in a user's inventory.
    
    - Replaces all existing ingredients with the new list
    - Quantities must be positive numbers
    
    Example:
    ```json
    POST /api/v1/setUserIngredients
    {
        "user_id": "user123",
        "ingredients": [
            {
                "ingr_name": "tomato",
                "quantity": 5,
                "unit": "piece"
            },
            {
                "ingr_name": "onion",
                "quantity": 2,
                "unit": "piece"
            }
        ]
    }
    ```
    """)
async def set_user_ingredients(
    ingredients: UserIngredients = Body(...,
        example={
            "user_id": "user123",
            "ingredients": [
                {"ingr_name": "tomato", "quantity": 5.0, "unit": "piece"},
                {"ingr_name": "onion", "quantity": 2.0, "unit": "piece"}
            ]
        }),
    db: Session = Depends(get_db)
):
    user = ingredient_service.get_user(db, ingredients.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    updated_ingredients = ingredient_service.set_user_ingredients(db, ingredients)
    return UserIngredients(user_id=ingredients.user_id, ingredients=updated_ingredients)

# Alerji endpoint'leri
@router.get("/getAllergies",
    response_model=List[str],
    summary="Get All Allergenic Ingredients",
    description="""
    Retrieves a list of all ingredients marked as potential allergens.
    
    Example:
    ```
    GET /api/v1/getAllergies
    
    Response:
    [
        "peanuts",
        "milk",
        "eggs",
        ...
    ]
    ```
    """)
async def get_all_allergies(db: Session = Depends(get_db)):
    return ingredient_service.get_all_allergies(db)

@router.get("/getUserAllergies",
    summary="Get User's Allergies",
    description="""
    Retrieves all allergies registered for a specific user.
    
    Parameters:
    - **user_id**: ID of the user
    
    Example:
    ```
    GET /api/v1/getUserAllergies?user_id=user123
    
    Response:
    {
        "user_id": "user123",
        "allergies": [
            "peanuts",
            "milk"
        ]
    }
    ```
    """)
async def get_user_allergies(
    user_id: str = Query(..., description="User ID", example="user123"),
    db: Session = Depends(get_db)
):
    user = ingredient_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    allergies = ingredient_service.get_user_allergies(db, user_id)
    return UserAllergies(user_id=user_id, allergies=allergies)

@router.post("/setUserAllergies",
    summary="Update User's Allergies",
    description="""
    Updates the list of allergies for a user.
    
    - Replaces all existing allergies with the new list
    - Allergies must be from the available allergens list
    
    Example:
    ```json
    POST /api/v1/setUserAllergies
    {
        "user_id": "user123",
        "allergies": [
            "peanuts",
            "milk"
        ]
    }
    ```
    """)
async def set_user_allergies(
    allergies: UserAllergies = Body(...,
        example={
            "user_id": "user123",
            "allergies": ["peanuts", "milk"]
        }),
    db: Session = Depends(get_db)
):
    user = ingredient_service.get_user(db, allergies.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    updated_allergies = ingredient_service.set_user_allergies(db, allergies)
    return UserAllergies(user_id=allergies.user_id, allergies=updated_allergies)

@router.get("/getPreferences",
    response_model=List[str],
    summary="Get Available Preferences",
    description="""
    Retrieves all available dietary preferences.
    
    Example:
    ```
    GET /api/v1/getPreferences
    
    Response:
    [
        "Vegetarian",
        "Vegan",
        "Gluten-free",
        ...
    ]
    ```
    """)
async def get_preferences(db: Session = Depends(get_db)):
    return preference_service.get_preferences(db)

@router.get("/getUserPreferences",
    response_model=UserPreferences,
    summary="Get User's Preferences",
    description="""
    Retrieves dietary preferences for a specific user as a dictionary.
    
    Parameters:
    - **user_id**: ID of the user
    
    Example:
    ```
    GET /api/v1/getUserPreferences?user_id=user123
    
    Response:
    {
        "user_id": "user123",
        "preferences": {
            "Vegetarian": true,
            "Gluten-free": true,
            "Vegan": false 
        }
    }
    ```
    """)
async def get_user_preferences(
    user_id: str = Query(..., description="User ID", example="user123"),
    db: Session = Depends(get_db)
):
    user = ingredient_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all available preferences
    all_prefs = preference_service.get_preferences(db)
    # Get user's selected preferences as a list
    user_prefs_list = preference_service.get_user_preferences(db, user_id)
    
    # Construct the dictionary response
    prefs_dict = {pref: (pref in user_prefs_list) for pref in all_prefs}
    
    return UserPreferences(user_id=user_id, preferences=prefs_dict)

@router.post("/setUserPreferences",
    response_model=UserPreferences,
    summary="Update User's Preferences",
    description="""
    Updates the dietary preferences for a user using a dictionary format.
    
    - Replaces all existing preferences based on the provided dictionary.
    - Keys should be valid preference names. Values should be boolean.
    
    Example:
    ```json
    POST /api/v1/setUserPreferences
    {
        "user_id": "user123",
        "preferences": {
            "Vegetarian": true,
            "Gluten-free": true,
            "Vegan": false
        }
    }
    ```
    """)
async def set_user_preferences(
    preferences: UserPreferences = Body(...,
        example={
            "user_id": "user123",
            "preferences": {
                "Vegetarian": True, 
                "Gluten-free": True,
                "Vegan": False
            }
        }),
    db: Session = Depends(get_db)
):
    user = ingredient_service.get_user(db, preferences.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # The service now handles the dictionary and returns it
    updated_prefs_dict = preference_service.set_user_preferences(db, preferences)
    # Return the full UserPreferences object
    return UserPreferences(user_id=preferences.user_id, preferences=updated_prefs_dict)