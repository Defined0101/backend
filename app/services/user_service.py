import uuid
from sqlalchemy.orm import Session
from app.models.models import User, LikedRecipe, DislikedRecipe
from app.schemas.user_schema import UserCreate, UserUpdate
from typing import Optional, List

class UserService:
    
    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Tüm kullanıcıları getir (sayfalandırma ile)
        """
        return db.query(User).offset(skip).limit(limit).all()

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """
        Kullanıcıyı ID'ye göre getir
        """
        return db.query(User).filter(User.user_id == user_id).first()

    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> dict: # Changed return type
        """
        Yeni kullanıcı oluştur, email kontrolü ve UUID ile
        """
        # Check if user with this email already exists
        existing_user = db.query(User).filter(User.e_mail == user_data.e_mail).first() # Use user_data
        if existing_user:
            return {"error": "Email already registered"}

        # Create new user with a unique user_id
        db_user = User(
            user_id=str(uuid.uuid4()),
            user_name=user_data.user_name, # Use user_data
            e_mail=user_data.e_mail  # Use user_data
            # user_bday and tel_no can be added if they are in UserCreate
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        # Return dict consistent with original provided version
        return {"message": "User created successfully!", "user": db_user} 

    @staticmethod
    def update_user(db: Session, user_id: str, user_update: UserUpdate) -> Optional[User]:
        """
        Kullanıcı bilgilerini güncelle
        """
        db_user = UserService.get_user_by_id(db, user_id) # Use class method
        if not db_user:
            return None
        
        # Sadece güncellenen alanları güncelle
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def delete_user(db: Session, user_id: str) -> dict: # Changed return type
        """
        Kullanıcıyı sil
        """
        db_user = UserService.get_user_by_id(db, user_id) # Use class method
        if not db_user:
            return {"error": "User not found"}
        
        db.delete(db_user)
        db.commit()
        # Return dict consistent with original provided version
        return {"message": "User deleted successfully!"} 

    @staticmethod
    def get_liked_recipes(db: Session, user_id: str) -> list[int]:
        """
        Return a list of recipe IDs the user liked
        """
        liked = db.query(LikedRecipe.recipe_id).filter(LikedRecipe.user_id == user_id).all()
        return [recipe.recipe_id for recipe in liked]
    
    @staticmethod
    def get_disliked_recipes(db: Session, user_id: str) -> list[int]:
        """
        Return a list of recipe IDs the user disliked
        """
        disliked = db.query(DislikedRecipe.recipe_id).filter(DislikedRecipe.user_id == user_id).all()
        return [recipe.recipe_id for recipe in disliked] 