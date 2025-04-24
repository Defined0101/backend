from pydantic import BaseModel
from typing import List, Dict, Optional, Union, Any
from .ingredient_schema import RecipeIngredientDetail

class Recipe(BaseModel):
    recipe_id: int
    recipe_name: str
    instruction: Optional[str] = None
    ingredient: Optional[List[RecipeIngredientDetail]] = None
    total_time: Optional[int] = None
    calories: Optional[float] = None
    fat: Optional[float] = None
    protein: Optional[float] = None
    carb: Optional[float] = None
    category: Optional[int] = None
    label: Optional[List[str]] = None

    class Config:
        from_attributes = True

class RecipeIngredient(BaseModel):
    recipe_id: int
    ingr_id: int
    quantity: Optional[float] = None
    unit: Optional[str] = None

class RecipeCard(BaseModel):
    recipe_id: int
    fields: Union[List[str], str]  # İki farklı varyant için 

class SaveRecipeRequest(BaseModel):
    recipe_ids: List[int]

    class Config:
        from_attributes = True 