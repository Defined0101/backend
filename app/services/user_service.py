from typing import List, Optional
from sqlalchemy.orm import Session
import uuid

from app.models.models import User, LikedRecipe, DislikedRecipe
from app.schemas.user_schema import UserCreate, UserUpdate


class UserService:
    # ---------- READ ----------
    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Return a paginated list of users."""
        return db.query(User).offset(skip).limit(limit).all()

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """Return a single user by primary key."""
        return db.query(User).filter(User.user_id == user_id).first()

    # ---------- CREATE ----------
    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:
        """Insert a new user; raise if e‑mail already exists."""
        if db.query(User).filter(User.e_mail == user.e_mail).first():
            raise ValueError("E‑mail already registered")  # FastAPI turns this into 400
        db_user = User(
            user_id=user.user_id,
            user_name=user.user_name,
            e_mail=user.e_mail,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    # ---------- UPDATE ----------
    @staticmethod
    def update_user(
        db: Session, user_id: str, user_update: UserUpdate
    ) -> Optional[User]:
        """Patch mutable fields on an existing user."""
        db_user = db.query(User).filter(User.user_id == user_id).first()
        if not db_user:
            return None
        for field, value in user_update.model_dump(exclude_unset=True).items():
            setattr(db_user, field, value)
        db.commit()
        db.refresh(db_user)
        return db_user

    # ---------- DELETE ----------
    @staticmethod
    def delete_user(db: Session, user_id: str) -> bool:
        """Delete the user and return True on success."""
        db_user = db.query(User).filter(User.user_id == user_id).first()
        if not db_user:
            return False
        db.delete(db_user)
        db.commit()
        return True

    # ---------- EXTRA HELPERS ----------
    @staticmethod
    def get_liked_recipes(db: Session, user_id: str) -> List[int]:
        """IDs of recipes the user liked."""
        liked = (
            db.query(LikedRecipe.recipe_id)
            .filter(LikedRecipe.user_id == user_id)
            .all()
        )
        return [row.recipe_id for row in liked]

    @staticmethod
    def get_disliked_recipes(db: Session, user_id: str) -> List[int]:
        """IDs of recipes the user disliked."""
        disliked = (
            db.query(DislikedRecipe.recipe_id)
            .filter(DislikedRecipe.user_id == user_id)
            .all()
        )
        return [row.recipe_id for row in disliked]
