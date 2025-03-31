from pydantic import BaseModel
from typing import List, Dict, Optional, Union, Any

class Recipe(BaseModel):
    recipe_id: int
    recipe_name: Optional[str] = None
    instruction: Optional[str] = None
    ingredient: Optional[str] = None
    total_time: Optional[int] = None
    calories: Optional[float] = None
    fat: Optional[float] = None
    protein: Optional[float] = None
    carb: Optional[float] = None
    category: Optional[int] = None

class RecipeIngredient(BaseModel):
    recipe_id: int
    ingr_id: int
    quantity: Optional[float] = None
    unit: Optional[str] = None

class RecipeCard(BaseModel):
    recipe_id: int
    fields: Union[List[str], str]  # İki farklı varyant için 