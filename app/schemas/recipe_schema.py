from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class RecipeDetails(BaseModel):
    recipe_id: int

class RecipeCard(BaseModel):
    recipe_id: int
    fields: List[str]

class UserPreferences(BaseModel):
    user_id: int
    dairy_free: bool
    gluten_free: bool
    pescetarian: bool
    vegan: bool
    vejetaryen: bool

class RecipeQuery(BaseModel):
    query: Optional[Dict[str, Any]] = None
    sortBy: Optional[Dict[str, str]] = None

class CategoryResponse(BaseModel):
    category_id: int
    category_name: str

    class Config:
        from_attributes = True

class PreferenceResponse(BaseModel):
    preference_id: int
    name: str

    class Config:
        from_attributes = True

class RecipeResponse(BaseModel):
    recipe_id: int
    name: str
    calories: Optional[int] = None
    total_time: Optional[int] = None
    description: Optional[str] = None
    steps: Optional[str] = None
    category_id: Optional[int] = None

    class Config:
        from_attributes = True 