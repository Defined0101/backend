from pydantic import BaseModel, EmailStr
from typing import Optional, List

class UserCreate(BaseModel):
    name: str
    email: EmailStr

class User(BaseModel):
    user_id: str
    user_name: str
    e_mail: EmailStr

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    user_id: str
    user_name: str
    e_mail: EmailStr

    class Config:
        from_attributes = True
