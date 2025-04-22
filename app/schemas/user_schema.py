from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date

class UserBase(BaseModel):
    e_mail: Optional[EmailStr] = None
    user_name: Optional[str] = None
    user_bday: Optional[date] = None
    tel_no: Optional[int] = None

class UserCreate(UserBase):
    user_id: str

class UserUpdate(UserBase):
    pass

class UserResponse(UserBase):
    user_id: str

    class Config:
        from_attributes = True 