from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, index=True)
    user_name = Column(String, nullable=True)
    e_mail = Column(String, unique=True, index=True, nullable=True)
    user_bday = Column(String, nullable=True)
    tel_no = Column(Integer, nullable=True)
    
    # İlişkiler
    user_prefs = relationship("UserPref", back_populates="user")
    saved_recipes = relationship("SavedRecipes", back_populates="user")
    liked_recipes = relationship("LikedRecipe", back_populates="user")
    allergies = relationship("Allergies", back_populates="user")

class UserPref(Base):
    __tablename__ = "user_pref"
    
    user_id = Column(String, ForeignKey("users.user_id"), primary_key=True)
    pref_id = Column(Integer, ForeignKey("preference.preference_id"), primary_key=True)
    
    # İlişkiler
    user = relationship("User", back_populates="user_prefs")
    preference = relationship("Preference", back_populates="user_prefs")

class Category(Base):
    __tablename__ = "category"
    
    category_id = Column(Integer, primary_key=True, index=True)
    cat_name = Column(String, nullable=True)
    
    # İlişkiler
    recipes = relationship("Recipe", back_populates="category_relation")

class Recipe(Base):
    __tablename__ = "recipe"
    
    recipe_id = Column(Integer, primary_key=True, index=True)
    recipe_name = Column(String, nullable=True)
    instruction = Column(String, nullable=True)
    ingredient = Column(String, nullable=True)  # Bu alan muhtemelen kullanılmıyor, recipe_ingr tablosu üzerinden ilişki var
    total_time = Column(Integer, nullable=True)
    calories = Column(Float, nullable=True)
    fat = Column(Float, nullable=True)
    protein = Column(Float, nullable=True)
    carb = Column(Float, nullable=True)
    category = Column(Integer, ForeignKey("category.category_id"), nullable=True)
    
    # İlişkiler
    category_relation = relationship("Category", back_populates="recipes")
    recipe_ingredients = relationship("RecipeIngr", back_populates="recipe")
    saved_by = relationship("SavedRecipes", back_populates="recipe")
    liked_by = relationship("LikedRecipe", back_populates="recipe")
    pref_recipes = relationship("PrefRecipe", back_populates="recipe")

class Ingredient(Base):
    __tablename__ = "ingredient"
    
    ingr_id = Column(Integer, primary_key=True, index=True)
    ingr_name = Column(String, nullable=True)
    
    # İlişkiler
    recipe_ingredients = relationship("RecipeIngr", back_populates="ingredient")
    allergies = relationship("Allergies", back_populates="ingredient")

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
    
    user_id = Column(String, ForeignKey("users.user_id"), primary_key=True)
    recipe_id = Column(Integer, ForeignKey("recipe.recipe_id"), primary_key=True)
    
    # İlişkiler
    user = relationship("User", back_populates="liked_recipes")
    recipe = relationship("Recipe", back_populates="liked_by")

class Allergies(Base):
    __tablename__ = "allergies"
    
    user_id = Column(String, ForeignKey("users.user_id"), primary_key=True)
    ingr_id = Column(Integer, ForeignKey("ingredient.ingr_id"), primary_key=True)
    
    # İlişkiler
    user = relationship("User", back_populates="allergies")
    ingredient = relationship("Ingredient", back_populates="allergies")

class Preference(Base):
    __tablename__ = "preference"
    
    preference_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    
    # İlişkiler
    pref_recipes = relationship("PrefRecipe", back_populates="preference")
    user_prefs = relationship("UserPref", back_populates="preference")

class PrefRecipe(Base):
    __tablename__ = "pref_recipe"
    
    recipe_id = Column(Integer, ForeignKey("recipe.recipe_id"), primary_key=True)
    pref_id = Column(Integer, ForeignKey("preference.preference_id"), primary_key=True)
    
    # İlişkiler
    preference = relationship("Preference", back_populates="pref_recipes")
    recipe = relationship("Recipe", back_populates="pref_recipes") 