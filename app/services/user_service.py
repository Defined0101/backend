from sqlalchemy.orm import Session
from app.models.models import User
from app.schemas.user_schema import UserCreate

def create_user(db: Session, user: UserCreate):
    """Create a new user in the database"""
    # Check if user with this email already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        return {"error": "Email already registered"}
    
    # Create new user
    db_user = User(
        name=user.name,
        email=user.email
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "User created successfully!", "user": db_user}

def get_users(db: Session):
    """Get all users from the database"""
    return db.query(User).all()

def get_user_by_id(db: Session, user_id: int):
    """Get a user by ID from the database"""
    return db.query(User).filter(User.user_id == user_id).first()

def delete_user(db: Session, user_id: int):
    """Delete a user from the database"""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return {"error": "User not found"}
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully!"}