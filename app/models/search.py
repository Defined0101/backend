from pydantic import BaseModel, Field
from typing import List, Optional

class QueryClass(BaseModel):
    inputText: str = Field(..., description="The main search query text.")
    categories: List[str] = Field(default_factory=list, description="List of categories to filter by.")
    labels: List[str] = Field(default_factory=list, description="List of labels to filter by (all must match).")

class RecipeSearch(BaseModel):
    query: QueryClass
    sortByField: Optional[str] = Field(default="name", description="Field to sort the results by (e.g., 'name', 'category').")
    sortByDirection: Optional[str] = Field(default="ascending", description="Sort direction: 'ascending' or 'descending'.") 