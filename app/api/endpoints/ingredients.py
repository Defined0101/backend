from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Dict
from app.core.database import get_db
from app.schemas.ingredient_schema import UserIngredients, IngredientResponse, UserAllergies, InventoryItem
from app.services import ingredient_service, preference_service
from app.models.models import User
from app.schemas.preference_schema import UserPreferences

router = APIRouter(tags=["ingredients"])

@router.get("/getIngredients", 
    response_model=List[str],
    summary="Get All Ingredients",
    description="""
    Retrieves a list of all available ingredients in the system.
    
    Returns a simple list of ingredient names.
    
    Example:
    ```
    GET /api/v1/getIngredients
    
    Response:
    [
        "tomato",
        "onion",
        "olive oil",
        ...
    ]
    ```
    """)
async def get_ingredients(db: Session = Depends(get_db)):
    return ingredient_service.get_ingredient_names(db)

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
                "ingredient_name": "tomato",
                "quantity": 5
            },
            {
                "ingredient_name": "onion",
                "quantity": 2
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
                "ingredient_name": "tomato",
                "quantity": 5
            },
            {
                "ingredient_name": "onion",
                "quantity": 2
            }
        ]
    }
    ```
    """)
async def set_user_ingredients(
    ingredients: UserIngredients = Body(..., example={
        "user_id": "user123",
        "ingredients": [
            {"ingredient_name": "tomato", "quantity": 5},
            {"ingredient_name": "onion", "quantity": 2}
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
    response_model=List[str],
    summary="Get User's Preferences",
    description="""
    Retrieves dietary preferences for a specific user.
    
    Parameters:
    - **user_id**: ID of the user
    
    Example:
    ```
    GET /api/v1/getUserPreferences?user_id=user123
    
    Response:
    [
        "Vegetarian",
        "Gluten-free"
    ]
    ```
    """)
async def get_user_preferences(
    user_id: str = Query(..., description="User ID", example="user123"),
    db: Session = Depends(get_db)
):
    user = ingredient_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return preference_service.get_user_preferences(db, user_id)

@router.post("/setUserPreferences",
    response_model=List[str],
    summary="Update User's Preferences",
    description="""
    Updates the dietary preferences for a user.
    
    - Replaces all existing preferences with the new list
    - Preferences must be from the available preferences list
    
    Example:
    ```json
    POST /api/v1/setUserPreferences
    {
        "user_id": "user123",
        "preferences": [
            "Vegetarian",
            "Gluten-free"
        ]
    }
    ```
    """)
async def set_user_preferences(
    preferences: UserPreferences = Body(...,
        example={
            "user_id": "user123",
            "preferences": ["Vegetarian", "Gluten-free"]
        }),
    db: Session = Depends(get_db)
):
    user = ingredient_service.get_user(db, preferences.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return preference_service.set_user_preferences(db, preferences)