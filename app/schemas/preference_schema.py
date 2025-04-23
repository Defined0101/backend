from pydantic import BaseModel
from typing import List, Dict

class UserPreferences(BaseModel):
    user_id: str
    preferences: Dict[str, bool] 