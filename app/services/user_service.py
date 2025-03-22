from sqlalchemy.orm import Session
from app.models.models import User
from app.schemas.user_schema import UserCreate
import uuid

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