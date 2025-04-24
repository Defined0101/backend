from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from decimal import Decimal

class IngredientCreate(BaseModel):
    name: str = Field(validation_alias='ingr_name')

    model_config = ConfigDict(populate_by_name=True)

class InventoryItem(BaseModel):
    name: str = Field(validation_alias='ingr_name')
    quantity: Optional[Decimal] = Decimal('1.0')
    unit: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)

class UserIngredients(BaseModel):
    user_id: str
    ingredients: List[InventoryItem]

class UserAllergies(BaseModel):
    user_id: str
    allergies: List[str]

class IngredientBase(BaseModel):
    ingr_id: int
    name: str = Field(validation_alias='ingr_name')
    default_unit: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class IngredientResponse(BaseModel):
    items: List[IngredientBase]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

# Schema for representing an ingredient within a recipe context
class RecipeIngredientDetail(BaseModel):
    name: str = Field(validation_alias='ingr_name')
    quantity: Optional[float] = None
    unit: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    ) 