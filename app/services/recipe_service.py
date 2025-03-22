from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.models import Category, Recipe, UserPref, Preference, Ingredient, RecipeIngr, Allergies, User, UserIngredient
from app.schemas.recipe_schema import RecipeDetails, RecipeCard, UserPreferences, RecipeQuery, UserAllergies, UserIngredients
from typing import List, Dict, Any
import json

def get_all_categories(db: Session):
    """Get all categories from the database"""
    return db.query(Category).all()

def get_all_labels(db: Session):
    """Get all preferences/labels from the database"""
    return db.query(Preference).all()

def get_recipe_details(db: Session, recipe_id: int):
    """Get full details of a recipe by ID"""
    recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
    if not recipe:
        return None
    
    # İlgili malzemeleri de alalım
    ingredients = db.query(RecipeIngr, Ingredient).\
        join(Ingredient, RecipeIngr.ingr_id == Ingredient.ingr_id).\
        filter(RecipeIngr.recipe_id == recipe_id).all()
    
    # Kategori bilgisini alalım
    category = db.query(Category).filter(Category.category_id == recipe.category).first()
    
    # Sonucu hazırlayalım
    result = {
        "recipe_id": recipe.recipe_id,
        "recipe_name": recipe.recipe_name,
        "instruction": recipe.instruction,
        "total_time": recipe.total_time,
        "calories": recipe.calories,
        "fat": recipe.fat,
        "protein": recipe.protein,
        "carb": recipe.carb,
        "category": category.cat_name if category else None,
        "ingredients": [
            {
                "name": ingredient.ingr_name,
                "quantity": recipe_ingr.quantity,
                "unit": recipe_ingr.unit
            } for recipe_ingr, ingredient in ingredients
        ]
    }
    
    return result

def get_recipe_card(db: Session, recipe_id: int, fields: List[str]):
    """Get specific fields of a recipe by ID"""
    recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
    if not recipe:
        return None
    
    result = {}
    for field in fields:
        # Veritabanındaki sütun adlarına göre dönüştürme yapalım
        db_field = field
        if field == "name":
            db_field = "recipe_name"
        
        if hasattr(recipe, db_field):
            result[field] = getattr(recipe, db_field)
        elif field == "ingredients" and recipe:
            # Malzemeleri ayrıca sorgulayalım
            ingredients = db.query(RecipeIngr, Ingredient).\
                join(Ingredient, RecipeIngr.ingr_id == Ingredient.ingr_id).\
                filter(RecipeIngr.recipe_id == recipe_id).all()
            
            result["ingredients"] = [
                {
                    "name": ingredient.ingr_name,
                    "quantity": recipe_ingr.quantity,
                    "unit": recipe_ingr.unit
                } for recipe_ingr, ingredient in ingredients
            ]
    
    return result

def get_user_preferences(db: Session, user_id: str):
    """Get user preferences by user ID"""
    # UserPref tablosundan kullanıcının tercihlerini alalım
    user_prefs = db.query(UserPref, Preference).\
        join(Preference, UserPref.pref_id == Preference.preference_id).\
        filter(UserPref.user_id == user_id).all()
    
    if not user_prefs:
        return None
    
    # Tercihleri dönüştürelim
    preferences = {}
    for user_pref, preference in user_prefs:
        pref_name = preference.name.lower() if preference.name else ""
        if pref_name == "dairy_free":
            preferences["dairy_free"] = True
        elif pref_name == "gluten_free":
            preferences["gluten_free"] = True
        elif pref_name == "pescetarian":
            preferences["pescetarian"] = True
        elif pref_name == "vegan":
            preferences["vegan"] = True
        elif pref_name == "vejetaryen":
            preferences["vejetaryen"] = True
    
    # Varsayılan değerleri ekleyelim
    preferences.setdefault("dairy_free", False)
    preferences.setdefault("gluten_free", False)
    preferences.setdefault("pescetarian", False)
    preferences.setdefault("vegan", False)
    preferences.setdefault("vejetaryen", False)
    
    return preferences

def set_user_preferences(db: Session, preferences: UserPreferences):
    """Set or update user preferences"""
    try:
        # Önce kullanıcının tercihlerini silelim
        db.query(UserPref).filter(UserPref.user_id == preferences.user_id).delete()
        
        # Preference tablosundan tercihlerin ID'lerini alalım
        pref_map = {}
        all_prefs = db.query(Preference).all()
        for pref in all_prefs:
            pref_name = pref.name.lower() if pref.name else ""
            pref_map[pref_name] = pref.preference_id
        
        # Yeni tercihleri ekleyelim
        if preferences.dairy_free and "dairy_free" in pref_map:
            db.add(UserPref(user_id=preferences.user_id, pref_id=pref_map["dairy_free"]))
        
        if preferences.gluten_free and "gluten_free" in pref_map:
            db.add(UserPref(user_id=preferences.user_id, pref_id=pref_map["gluten_free"]))
        
        if preferences.pescetarian and "pescetarian" in pref_map:
            db.add(UserPref(user_id=preferences.user_id, pref_id=pref_map["pescetarian"]))
        
        if preferences.vegan and "vegan" in pref_map:
            db.add(UserPref(user_id=preferences.user_id, pref_id=pref_map["vegan"]))
        
        if preferences.vejetaryen and "vejetaryen" in pref_map:
            db.add(UserPref(user_id=preferences.user_id, pref_id=pref_map["vejetaryen"]))
        
        db.commit()
        return {"message": "Preferences updated", "preferences": preferences}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

def query_recipes(db: Session, query_data: Dict[str, Any] = None, sort_data: Dict[str, str] = None):
    """Query recipes based on various criteria"""
    q = db.query(Recipe)
    
    if query_data:
        # Filter by name if provided
        if "name" in query_data:
            name_val = query_data["name"]
            q = q.filter(Recipe.recipe_name.ilike(f"%{name_val}%"))
        
        # Filter by ingredients if provided
        if "ingredient" in query_data and query_data["ingredient"]:
            ingredient_list = query_data["ingredient"]
            if isinstance(ingredient_list, list) and ingredient_list:
                # Malzeme isimlerine göre filtreleme yapalım
                for ingredient_name in ingredient_list:
                    # Alt sorgu: Bu malzemeyi içeren tariflerin ID'lerini bulalım
                    subquery = db.query(RecipeIngr.recipe_id).\
                        join(Ingredient, RecipeIngr.ingr_id == Ingredient.ingr_id).\
                        filter(Ingredient.ingr_name.ilike(f"%{ingredient_name}%"))
                    
                    # Ana sorguya bu ID'leri ekleyelim
                    q = q.filter(Recipe.recipe_id.in_(subquery))
    
    # Apply sorting if provided
    if sort_data and "field" in sort_data:
        sort_field = sort_data["field"]
        sort_dir = sort_data.get("direction", "asc").lower()
        
        # Veritabanındaki sütun adlarına göre dönüştürme yapalım
        if sort_field == "name":
            sort_field = "recipe_name"
        
        if hasattr(Recipe, sort_field):
            if sort_dir == "asc":
                q = q.order_by(getattr(Recipe, sort_field).asc())
            else:
                q = q.order_by(getattr(Recipe, sort_field).desc())
    
    recipes = q.all()
    
    # Tariflerin kategorilerini ve malzemelerini de ekleyelim
    result = []
    for recipe in recipes:
        # Kategori bilgisini alalım
        category = db.query(Category).filter(Category.category_id == recipe.category).first()
        
        # Malzemeleri alalım
        ingredients = db.query(RecipeIngr, Ingredient).\
            join(Ingredient, RecipeIngr.ingr_id == Ingredient.ingr_id).\
            filter(RecipeIngr.recipe_id == recipe.recipe_id).all()
        
        # Tarif bilgilerini hazırlayalım
        recipe_data = {
            "recipe_id": recipe.recipe_id,
            "recipe_name": recipe.recipe_name,
            "instruction": recipe.instruction,
            "total_time": recipe.total_time,
            "calories": recipe.calories,
            "fat": recipe.fat,
            "protein": recipe.protein,
            "carb": recipe.carb,
            "category": category.cat_name if category else None,
            "ingredients": [
                {
                    "name": ingredient.ingr_name,
                    "quantity": recipe_ingr.quantity,
                    "unit": recipe_ingr.unit
                } for recipe_ingr, ingredient in ingredients
            ]
        }
        
        result.append(recipe_data)
    
    return result 

def get_all_ingredients(db: Session):
    """Get all ingredients from the database"""
    ingredients = db.query(Ingredient).all()
    return [ingredient.ingr_name for ingredient in ingredients]

def get_all_allergies(db: Session):
    """Get all possible allergies/ingredients that can be allergies"""
    # In this system, allergies are just ingredients that users can be allergic to
    return get_all_ingredients(db)

def get_user_allergies(db: Session, user_id: str):
    """Get allergies for a specific user"""
    # Get the user's allergies from the allergies table
    allergies = db.query(Allergies, Ingredient).\
        join(Ingredient, Allergies.ingr_id == Ingredient.ingr_id).\
        filter(Allergies.user_id == user_id).all()
    
    if not allergies:
        return {"user_id": user_id, "allergies": []}
    
    # Convert to response format
    return {
        "user_id": user_id,
        "allergies": [ingredient.ingr_name for _, ingredient in allergies]
    }

def set_user_allergies(db: Session, user_allergies: UserAllergies):
    """Set or update user allergies"""
    try:
        # First, remove existing allergies for this user
        db.query(Allergies).filter(Allergies.user_id == user_allergies.user_id).delete()
        
        # Then add new allergies
        for allergy_name in user_allergies.allergies:
            # Find ingredient by name
            ingredient = db.query(Ingredient).filter(Ingredient.ingr_name.ilike(f"%{allergy_name}%")).first()
            if ingredient:
                db.add(Allergies(user_id=user_allergies.user_id, ingr_id=ingredient.ingr_id))
        
        db.commit()
        return {"message": "Allergies updated", "allergies": user_allergies}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

def get_user_recommendations(db: Session, user_id: str = None):
    """Get recipe recommendations for a user
    
    This is a simple implementation. In a real system, you might use more complex algorithms
    taking into account user preferences, allergies, past interactions, etc.
    """
    # For simplicity, return top 10 recipes
    # In a real system, you would implement a proper recommendation algorithm
    recipes = db.query(Recipe).limit(10).all()
    
    result = []
    for recipe in recipes:
        # Get the recipe category
        category = db.query(Category).filter(Category.category_id == recipe.category).first()
        
        # Get the recipe ingredients
        ingredients = db.query(RecipeIngr, Ingredient).\
            join(Ingredient, RecipeIngr.ingr_id == Ingredient.ingr_id).\
            filter(RecipeIngr.recipe_id == recipe.recipe_id).all()
        
        # Create recipe data
        recipe_data = {
            "recipe_id": recipe.recipe_id,
            "recipe_name": recipe.recipe_name,
            "instruction": recipe.instruction,
            "total_time": recipe.total_time,
            "calories": recipe.calories,
            "fat": recipe.fat,
            "protein": recipe.protein,
            "carb": recipe.carb,
            "category": category.cat_name if category else None,
            "ingredients": [
                {
                    "name": ingredient.ingr_name,
                    "quantity": recipe_ingr.quantity,
                    "unit": recipe_ingr.unit
                } for recipe_ingr, ingredient in ingredients
            ]
        }
        
        result.append(recipe_data)
    
    return result

def get_recipes_by_query(db: Session, query_json: str, sort_field: str = None, sort_direction: str = None):
    """Parse the JSON query string and query recipes"""
    try:
        # Parse the JSON query
        query_data = json.loads(query_json) if query_json else {}
        
        # Prepare sort data
        sort_data = None
        if sort_field:
            sort_data = {
                "field": sort_field,
                "direction": sort_direction or "asc"
            }
        
        # Use the existing query_recipes function
        return query_recipes(db, query_data, sort_data)
    except Exception as e:
        return {"error": str(e)}

def get_user_ingredients(db: Session, user_id: str):
    """Get ingredients for a specific user"""
    # Get the user's ingredients from the user_ingredients table
    user_ingredients = db.query(UserIngredient, Ingredient).\
        join(Ingredient, UserIngredient.ingr_id == Ingredient.ingr_id).\
        filter(UserIngredient.user_id == user_id).all()
    
    if not user_ingredients:
        return {"user_id": user_id, "ingredients": []}
    
    # Convert to response format
    return {
        "user_id": user_id,
        "ingredients": [ingredient.ingr_name for _, ingredient in user_ingredients]
    }

def set_user_ingredients(db: Session, user_ingredients: UserIngredients):
    """Set or update user ingredients"""
    try:
        # First, remove existing ingredients for this user
        db.query(UserIngredient).filter(UserIngredient.user_id == user_ingredients.user_id).delete()
        
        # Then add new ingredients
        for ingredient_name in user_ingredients.ingredients:
            # Find ingredient by name
            ingredient = db.query(Ingredient).filter(Ingredient.ingr_name.ilike(f"%{ingredient_name}%")).first()
            if ingredient:
                db.add(UserIngredient(user_id=user_ingredients.user_id, ingr_id=ingredient.ingr_id))
        
        db.commit()
        return {"message": "Ingredients updated", "ingredients": user_ingredients}
    except Exception as e:
        db.rollback()
        return {"error": str(e)} 