from pydantic import BaseModel, EmailStr
from typing import Optional, List

class UserCreate(BaseModel):
    name: str
    email: EmailStr

class User(BaseModel):
    user_id: int
    name: str
    email: EmailStr

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    user_id: int
    name: str
    email: EmailStr

    class Config:
        from_attributes = True
