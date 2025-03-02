from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.user_schema import UserCreate, UserResponse
from app.services.user_service import create_user, get_users, get_user_by_id, delete_user
from typing import List

router = APIRouter()

@router.post("/", response_model=dict)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    return create_user(db, user)

@router.get("/", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db)):
    """Get all users"""
    return get_users(db)

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a user by ID"""
    user = get_user_by_id(db, user_id)
    if not user:
        return {"error": "User not found"}
    return user

@router.delete("/{user_id}", response_model=dict)
def remove_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user by ID"""
    return delete_user(db, user_id)
