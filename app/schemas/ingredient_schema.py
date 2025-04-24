from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal

class IngredientCreate(BaseModel):
    ingr_name: str

class InventoryItem(BaseModel):
    ingr_name: str
    quantity: Optional[Decimal] = Decimal('1.0')
    unit: str

class UserIngredients(BaseModel):
    user_id: str
    ingredients: List[InventoryItem]

class UserAllergies(BaseModel):
    user_id: str
    allergies: List[str]

class IngredientBase(BaseModel):
    ingr_id: int
    ingr_name: str
    default_unit: str

    class Config:
        from_attributes = True

class IngredientResponse(BaseModel):
    items: List[IngredientBase]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool 