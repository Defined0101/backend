from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class RecipeDetails(BaseModel):
    recipe_id: int

class RecipeCard(BaseModel):
    recipe_id: int
    fields: List[str]

class UserPreferences(BaseModel):
    user_id: str
    preferences: List[int]  # pref_id listesi

class UserAllergies(BaseModel):
    user_id: str
    allergies: List[int]  # ingr_id listesi

class UserIngredients(BaseModel):
    user_id: str
    ingredients: List[int]  # ingr_id listesi

class GetQueryRequest(BaseModel):
    query: str  # JSON-encoded query
    sortBy: Dict[str, str]

class RecipeQuery(BaseModel):
    query: Optional[Dict[str, Any]] = None
    sortBy: Optional[Dict[str, str]] = None

class CategoryResponse(BaseModel):
    category_id: int
    cat_name: str

    class Config:
        from_attributes = True

class PreferenceResponse(BaseModel):
    pref_id: int
    pref_name: str

    class Config:
        from_attributes = True

class RecipeResponse(BaseModel):
    recipe_id: int
    recipe_name: str
    calories: Optional[float] = None
    total_time: Optional[int] = None
    instruction: Optional[str] = None
    ingredient: Optional[str] = None
    category: Optional[int] = None
    fat: Optional[float] = None
    protein: Optional[float] = None
    carb: Optional[float] = None

    class Config:
        from_attributes = True 