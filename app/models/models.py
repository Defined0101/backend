from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, Text, Date, Numeric
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Text, primary_key=True)
    e_mail = Column(Text)
    user_name = Column(Text)
    user_bday = Column(Date)
    tel_no = Column(Integer)
    
    # İlişkiler
    user_prefs = relationship("UserPref", back_populates="user")
    saved_recipes = relationship("SavedRecipes", back_populates="user")
    liked_recipes = relationship("LikedRecipe", back_populates="user")
    allergies = relationship("Allergy", back_populates="user")

class UserPref(Base):
    __tablename__ = "user_pref"
    
    user_id = Column(String, ForeignKey("users.user_id"), primary_key=True)
    pref_id = Column(Integer, ForeignKey("preference.pref_id"), primary_key=True)
    
    # İlişkiler
    user = relationship("User", back_populates="user_prefs")
    preference = relationship("Preference", back_populates="user_prefs")

class Category(Base):
    __tablename__ = "category"
    
    category_id = Column(Integer, primary_key=True, index=True)
    cat_name = Column(String, nullable=True)
    
    # Category ilişkisi recipe'de Foreign Key olarak belirtilmiş ama
    # veritabanında kısıtlama (constraint) yok

class Recipe(Base):
    __tablename__ = "recipe"
    
    recipe_id = Column(Integer, primary_key=True, index=True)
    recipe_name = Column(String, nullable=True)
    instruction = Column(Text, nullable=True)
    ingredient = Column(Text, nullable=True)  # Dokümanda bu alan text olarak belirtilmiş
    total_time = Column(Integer, nullable=True)
    calories = Column(Float, nullable=True)
    fat = Column(Float, nullable=True)
    protein = Column(Float, nullable=True)
    carb = Column(Float, nullable=True)
    category = Column(Integer, nullable=True)  # FK constraint yok
    
    # İlişkiler
    recipe_ingredients = relationship("RecipeIngr", back_populates="recipe")
    saved_by = relationship("SavedRecipes", back_populates="recipe")
    liked_by = relationship("LikedRecipe", back_populates="recipe")
    pref_recipes = relationship("PrefRecipe", back_populates="recipe")

class Ingredient(Base):
    __tablename__ = "ingredient"
    
    ingr_id = Column(Integer, primary_key=True)
    ingr_name = Column(Text)
    
    # İlişkiler
    recipe_ingredients = relationship("RecipeIngr", back_populates="ingredient")
    allergies = relationship("Allergy", back_populates="ingredient")

class RecipeIngr(Base):
    __tablename__ = "recipe_ingr"
    
    recipe_id = Column(Integer, ForeignKey("recipe.recipe_id"), primary_key=True)
    ingr_id = Column(Integer, ForeignKey("ingredient.ingr_id"), primary_key=True)
    quantity = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    
    # İlişkiler
    recipe = relationship("Recipe", back_populates="recipe_ingredients")
    ingredient = relationship("Ingredient", back_populates="recipe_ingredients")

class SavedRecipes(Base):
    __tablename__ = "saved_recipes"
    
    recipe_id = Column(Integer, ForeignKey("recipe.recipe_id"), primary_key=True)
    user_id = Column(String, ForeignKey("users.user_id"), primary_key=True)
    
    # İlişkiler
    recipe = relationship("Recipe", back_populates="saved_by")
    user = relationship("User", back_populates="saved_recipes")

class LikedRecipe(Base):
    __tablename__ = "liked_recipes"
    
    recipe_id = Column(Integer, ForeignKey("recipe.recipe_id"), primary_key=True)
    user_id = Column(String, ForeignKey("users.user_id"), primary_key=True)
    
    # İlişkiler
    user = relationship("User", back_populates="liked_recipes")
    recipe = relationship("Recipe", back_populates="liked_by")

class Allergy(Base):
    __tablename__ = "allergy"
    
    user_id = Column(Text, ForeignKey("users.user_id"), primary_key=True)
    ingr_id = Column(Integer, ForeignKey("ingredient.ingr_id"), primary_key=True)
    
    # İlişkiler
    user = relationship("User", back_populates="allergies")
    ingredient = relationship("Ingredient", back_populates="allergies")

class Preference(Base):
    __tablename__ = "preference"
    
    pref_id = Column(Integer, primary_key=True, index=True)
    pref_name = Column(String, nullable=True)
    
    # İlişkiler
    pref_recipes = relationship("PrefRecipe", back_populates="preference")
    user_prefs = relationship("UserPref", back_populates="preference")

class PrefRecipe(Base):
    __tablename__ = "pref_recipe"
    
    recipe_id = Column(Integer, ForeignKey("recipe.recipe_id"), primary_key=True)
    pref_id = Column(Integer, ForeignKey("preference.pref_id"), primary_key=True)
    
    # İlişkiler
    preference = relationship("Preference", back_populates="pref_recipes")
    recipe = relationship("Recipe", back_populates="pref_recipes")

class Inventory(Base):
    __tablename__ = "inventory"
    
    user_id = Column(Text, ForeignKey("users.user_id"), primary_key=True)
    ingr_id = Column(Text, primary_key=True)
    quantity = Column(Numeric)

    user = relationship("User", backref="inventory_items") 