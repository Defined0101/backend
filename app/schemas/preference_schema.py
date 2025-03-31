from pydantic import BaseModel
from typing import List

class UserPreferences(BaseModel):
    user_id: str
    preferences: List[str] 