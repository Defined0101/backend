from sqlalchemy.orm import Session
from app.models.models import User, LikedRecipe, DislikedRecipe
from app.schemas.user_schema import UserCreate
import uuid

class UserService:
    def create_user(db: Session, user: UserCreate):
        """Create a new user in the database"""
        # Check if user with this email already exists
        existing_user = db.query(User).filter(User.e_mail == user.email).first()
        if existing_user:
            return {"error": "Email already registered"}
        
        # Create new user with a unique user_id
        # In a real system, you'd generate a proper unique ID
        # For this example, we'll use a timestamp or similar approach
        db_user = User(
            user_id=str(uuid.uuid4()),
            user_name=user.name,
            e_mail=user.email
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return {"message": "User created successfully!", "user": db_user}

    def get_users(db: Session):
        """Get all users from the database"""
        return db.query(User).all()

    def get_user_by_id(db: Session, user_id: str):
        """Get a user by ID from the database"""
        return db.query(User).filter(User.user_id == user_id).first()

    def delete_user(db: Session, user_id: str):
        """Delete a user from the database"""
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        db.delete(user)
        db.commit()
        return {"message": "User deleted successfully!"}

    def get_liked_recipes(db: Session, user_id: str) -> list[int]:
        """Return a list of recipe IDs the user liked"""
        liked = db.query(LikedRecipe.recipe_id).filter(LikedRecipe.user_id == user_id).all()
        return [recipe.recipe_id for recipe in liked]
    
    def get_disliked_recipes(db: Session, user_id: str) -> list[int]:
        """Return a list of recipe IDs the user disliked"""
        disliked = db.query(DislikedRecipe.recipe_id).filter(DislikedRecipe.user_id == user_id).all()
        return [recipe.recipe_id for recipe in disliked]