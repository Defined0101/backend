from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.models import User
from app.schemas.user_schema import UserCreate, UserUpdate, UserResponse
from app.services import user_service

router = APIRouter(tags=["users"])

@router.get("/", 
    response_model=List[UserResponse],
    summary="Get All Users",
    description="""
    Retrieves a list of all users in the system.
    
    Parameters:
    - **skip**: Number of users to skip (for pagination)
    - **limit**: Maximum number of users to return
    
    Example:
    ```
    GET /api/v1/users?skip=0&limit=10
    ```
    """)
async def get_all_users(
    skip: int = Query(0, description="Number of users to skip", example=0),
    limit: int = Query(100, description="Maximum number of users to return", example=10),
    db: Session = Depends(get_db)
):
    """
    Tüm kullanıcıları listele
    """
    return user_service.get_users(db, skip=skip, limit=limit)

@router.get("/{user_id}", 
    response_model=UserResponse,
    summary="Get User Details",
    description="""
    Retrieves details of a specific user.
    
    Parameters:
    - **user_id**: ID of the user to retrieve
    
    Example:
    ```
    GET /api/v1/users/user123
    ```
    """)
async def get_user(
    user_id: str = Path(..., description="User ID to retrieve", example="user123"),
    db: Session = Depends(get_db)
):
    """
    Belirli bir kullanıcının bilgilerini getir
    """
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    return user

@router.post("/", 
    response_model=UserResponse,
    summary="Create New User",
    description="""
    Creates a new user in the system.
    
    Required fields:
    - **user_id**: Unique identifier for the user
    
    Optional fields:
    - **e_mail**: User's email address
    - **user_name**: Display name
    - **user_bday**: Birthday (YYYY-MM-DD)
    - **tel_no**: Phone number
    
    Example:
    ```json
    POST /api/v1/users
    {
        "user_id": "user123",
        "e_mail": "user@example.com",
        "user_name": "John Doe",
        "user_bday": "1990-01-01",
        "tel_no": 5551234567
    }
    ```
    """)
async def create_user(
    user_data: UserCreate = Body(..., example={
        "user_id": "user123",
        "e_mail": "user@example.com",
        "user_name": "John Doe",
        "user_bday": "1990-01-01",
        "tel_no": 5551234567
    }),
    db: Session = Depends(get_db)
):
    """
    Yeni kullanıcı oluştur
    """
    return user_service.create_user(db, user_data)

@router.put("/{user_id}", 
    response_model=UserResponse,
    summary="Update User",
    description="""
    Updates information for an existing user.
    
    Parameters:
    - **user_id**: ID of the user to update
    
    Updatable fields:
    - **e_mail**: User's email address
    - **user_name**: Display name
    - **user_bday**: Birthday (YYYY-MM-DD)
    - **tel_no**: Phone number
    
    Example:
    ```json
    PUT /api/v1/users/user123
    {
        "user_name": "John Smith",
        "tel_no": 5559876543
    }
    ```
    """)
async def update_user(
    user_id: str = Path(..., description="User ID to update", example="user123"),
    user_update: UserUpdate = Body(..., example={
        "user_name": "John Smith",
        "tel_no": 5559876543
    }),
    db: Session = Depends(get_db)
):
    """
    Kullanıcı bilgilerini güncelle
    """
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    return user_service.update_user(db, user_id, user_update)

@router.delete("/{user_id}",
    summary="Delete User",
    description="""
    Deletes a user from the system.
    
    Parameters:
    - **user_id**: ID of the user to delete
    
    Example:
    ```
    DELETE /api/v1/users/user123
    ```
    """)
async def delete_user(
    user_id: str = Path(..., description="User ID to delete", example="user123"),
    db: Session = Depends(get_db)
):
    """
    Kullanıcıyı sil
    """
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    user_service.delete_user(db, user_id)
    return {"message": "Kullanıcı başarıyla silindi"}