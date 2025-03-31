from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date

class UserBase(BaseModel):
    user_id: str
    email: Optional[EmailStr] = None
    user_name: Optional[str] = None
    user_bday: Optional[date] = None
    tel_no: Optional[int] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    user_name: Optional[str] = None
    user_bday: Optional[date] = None
    tel_no: Optional[int] = None

class User(UserBase):
    class Config:
        from_attributes = True 