from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.models import User
from app.schemas.user_schema import UserCreate, UserUpdate, UserResponse
from app.services import user_service

router = APIRouter()

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Tüm kullanıcıları listele
    """
    return user_service.get_users(db, skip=skip, limit=limit)

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Belirli bir kullanıcının bilgilerini getir
    """
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    return user

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Yeni kullanıcı oluştur
    """
    return user_service.create_user(db, user_data)

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db)
):
    """
    Kullanıcı bilgilerini güncelle
    """
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    return user_service.update_user(db, user_id, user_update)

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
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