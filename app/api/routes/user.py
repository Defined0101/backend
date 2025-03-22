from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.user_schema import UserCreate, UserResponse
from app.services.user_service import create_user, get_users, get_user_by_id, delete_user
from typing import List

router = APIRouter()

@router.post("/", 
           response_model=dict,
           summary="Register a new user",
           description="Creates a new user account in the system.",
           response_description="Success message and user object")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    This endpoint creates a new user account with:
    - Name
    - Email address
    
    If the email is already registered, an error message is returned.
    """
    return create_user(db, user)

@router.get("/", 
           response_model=List[UserResponse],
           summary="Get all users",
           description="Returns a list of all registered users.",
           response_description="List of user objects")
def list_users(db: Session = Depends(get_db)):
    """
    Get all users.
    
    This endpoint returns a list of all users registered in the system.
    Each user object includes:
    - User ID
    - Name
    - Email
    """
    return get_users(db)

@router.get("/{user_id}", 
           response_model=UserResponse,
           summary="Get user by ID",
           description="Returns details of a specific user.",
           response_description="User object")
def get_user(user_id: str, db: Session = Depends(get_db)):
    """
    Get a user by ID.
    
    This endpoint returns detailed information about a specific user, including:
    - User ID
    - Name
    - Email
    
    If the user is not found, an error message is returned.
    """
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/{user_id}", 
           response_model=dict,
           summary="Delete user",
           description="Removes a user account from the system.",
           response_description="Success message")
def remove_user(user_id: str, db: Session = Depends(get_db)):
    """
    Delete a user by ID.
    
    This endpoint completely removes a user account and all associated data, including:
    - User preferences
    - Allergies
    - Saved recipes
    - Liked recipes
    - User ingredients
    
    If the user is not found, an error message is returned.
    """
    return delete_user(db, user_id)
