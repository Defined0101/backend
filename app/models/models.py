import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, Text, DateTime, Date, BigInteger, TIMESTAMP, Numeric

from sqlalchemy.orm import relationship
from app.core.database import Base

# Ara Tablo: recipe_cat için model
class RecipeCategoryLink(Base):
    __tablename__ = 'recipe_cat'
    # Varsayılan olarak composite primary key (recipe_id, cat_id)
    recipe_id = Column(Integer, ForeignKey('recipe.recipe_id'), primary_key=True)
    cat_id = Column(Integer, ForeignKey('category.category_id'), primary_key=True)

    # İsteğe bağlı: İlişkileri tanımlayabiliriz, ancak servis katmanında doğrudan sorgu da yapabiliriz.
    # recipe = relationship("Recipe", back_populates="category_link") # Recipe'de category_link tanımlanmalı
    # category = relationship("Category", back_populates="recipe_links") # Category'de recipe_links tanımlanmalı

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Text, primary_key=True)
    e_mail = Column(Text)
    user_name = Column(Text)
    user_bday = Column(Date)
    tel_no = Column(Integer)
    
    # İlişkiler
    user_prefs = relationship("UserPref", back_populates="user", cascade="all, delete-orphan")
    saved_recipes = relationship("SavedRecipes", back_populates="user", cascade="all, delete-orphan")
    liked_recipes = relationship("LikedRecipe", back_populates="user", cascade="all, delete-orphan")
    disliked_recipes = relationship("DislikedRecipe", back_populates="user", cascade="all, delete-orphan")
    allergies = relationship("Allergy", back_populates="user", cascade="all, delete-orphan")

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
    
    # İlişki kaldırıldı (veya RecipeCategoryLink'e göre güncellenebilir)
    # recipes = relationship(
    #     "Recipe",
    #     back_populates="category"
    # )

class Recipe(Base):
    __tablename__ = "recipe"
    
    recipe_id = Column(Integer, primary_key=True, index=True)
    recipe_name = Column(String, nullable=True)
    instruction = Column(Text, nullable=True)
    ingredient = Column(Text, nullable=True)
    total_time = Column(Integer, nullable=True)
    calories = Column(Float, nullable=True)
    fat = Column(Float, nullable=True)
    protein = Column(Float, nullable=True)
    carb = Column(Float, nullable=True)
    
    # İlişkiler
    recipe_ingredients = relationship("RecipeIngr", back_populates="recipe")
    saved_by = relationship("SavedRecipes", back_populates="recipe")
    liked_by = relationship("LikedRecipe", back_populates="recipe")
    disliked_by = relationship("DislikedRecipe", back_populates="recipe")
    pref_recipes = relationship("PrefRecipe", back_populates="recipe")

class Ingredient(Base):
    __tablename__ = "ingredient"
    
    ingr_id = Column(Integer, primary_key=True)
    ingr_name = Column(Text)
    default_unit = Column(String, nullable=True)
    
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
    
    recipe_id = Column(Integer, ForeignKey('recipe.recipe_id'), primary_key=True)
    user_id = Column(Text, ForeignKey('users.user_id'), primary_key=True)
    
    # İlişkiler
    recipe = relationship("Recipe", back_populates="saved_by")
    user = relationship("User", back_populates="saved_recipes")

class LikedRecipe(Base):
    __tablename__ = "liked_recipes"
    
    recipe_id = Column(Integer, ForeignKey("recipe.recipe_id"), primary_key=True)
    user_id = Column(String, ForeignKey("users.user_id"), primary_key=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    
    # İlişkiler
    user = relationship("User", back_populates="liked_recipes")
    recipe = relationship("Recipe", back_populates="liked_by")

class DislikedRecipe(Base):
    __tablename__ = "disliked_recipes"

    user_id = Column(String, ForeignKey("users.user_id"), primary_key=True)
    recipe_id = Column(Integer, ForeignKey("recipe.recipe_id"), primary_key=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    # İlişkiler
    user = relationship("User", back_populates="disliked_recipes")
    recipe = relationship("Recipe", back_populates="disliked_by")


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
    ingr_id = Column(Integer, ForeignKey("ingredient.ingr_id"), primary_key=True)
    quantity = Column(Numeric)
    unit = Column(String, nullable=True)
    
    user = relationship("User", backref="inventory_items")
    
# Materialized Views
class UserAllergiesView(Base):
    __tablename__ = "user_allergies"
    
    user_id = Column(Text, primary_key=True)
    ingr_id = Column(Integer, primary_key=True)
    ingr_name = Column(Text)

class UserInventoryView(Base):
    __tablename__ = "user_inventory"
    
    user_id = Column(Text, primary_key=True)
    ingr_id = Column(Integer, primary_key=True)
    ingr_name = Column(Text)
    quantity = Column(Numeric)
    unit = Column(String, nullable=True) 