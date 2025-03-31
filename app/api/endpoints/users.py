from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.firebase import verify_firebase_token
from app.schemas.user import User, UserCreate, UserUpdate
from app.services import user_service

router = APIRouter()

async def get_current_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    try:
        firebase_user = verify_firebase_token(token)
        user = user_service.get_user(db, firebase_user["uid"])
        if not user:
            # Kullanıcı yoksa oluştur
            user_data = UserCreate(
                user_id=firebase_user["uid"],
                email=firebase_user.get("email"),
                user_name=firebase_user.get("name")
            )
            user = user_service.create_user(db, user_data)
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/users/", response_model=User)
async def create_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Firebase token'ı ile kullanıcı oluştur
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    try:
        firebase_user = verify_firebase_token(token)
        user_data = UserCreate(
            user_id=firebase_user["uid"],
            email=firebase_user.get("email"),
            user_name=firebase_user.get("name")
        )
        return user_service.create_user(db, user_data)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Mevcut kullanıcının bilgilerini getir
    """
    return current_user

@router.put("/users/me", response_model=User)
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mevcut kullanıcının bilgilerini güncelle
    """
    updated_user = user_service.update_user(db, current_user.user_id, user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user 