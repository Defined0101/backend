from sqlalchemy.orm import Session
from app.models.models import User
from app.schemas.user_schema import UserCreate, UserUpdate
from typing import Optional, List

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Tüm kullanıcıları getir
    """
    return db.query(User).offset(skip).limit(limit).all()

def get_user(db: Session, user_id: str) -> Optional[User]:
    """
    Kullanıcıyı ID'ye göre getir
    """
    return db.query(User).filter(User.user_id == user_id).first()

def create_user(db: Session, user_data: UserCreate) -> User:
    """
    Yeni kullanıcı oluştur
    """
    db_user = User(**user_data.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: str, user_update: UserUpdate) -> Optional[User]:
    """
    Kullanıcı bilgilerini güncelle
    """
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    # Sadece güncellenen alanları güncelle
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: str) -> bool:
    """
    Kullanıcıyı sil
    """
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True 