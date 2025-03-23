from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.models import Category, Recipe, UserPref, Preference, Ingredient, RecipeIngr, Allergy, User
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
        join(Preference, UserPref.pref_id == Preference.pref_id).\
        filter(UserPref.user_id == user_id).all()
    
    if not user_prefs:
        return None
    
    # Kullanıcının tercih ID'lerini döndürelim
    preferences = []
    for user_pref, preference in user_prefs:
        preferences.append(preference.pref_id)
    
    return {"user_id": user_id, "preferences": preferences}

def set_user_preferences(db: Session, preferences: UserPreferences):
    """Set or update user preferences"""
    try:
        # Kullanıcının mevcut olup olmadığını kontrol edelim
        user = db.query(User).filter(User.user_id == preferences.user_id).first()
        if not user:
            return {"error": "User not found"}
            
        # Önce kullanıcının tercihlerini silelim
        db.query(UserPref).filter(UserPref.user_id == preferences.user_id).delete()
        
        # Yeni tercihleri ekleyelim
        for pref_id in preferences.preferences:
            # Tercih ID'sinin geçerli olup olmadığını kontrol edelim
            pref = db.query(Preference).filter(Preference.pref_id == pref_id).first()
            if pref:
                db.add(UserPref(user_id=preferences.user_id, pref_id=pref_id))
        
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
    return [{"ingr_id": ingredient.ingr_id, "ingr_name": ingredient.ingr_name} for ingredient in ingredients]

def get_all_allergies(db: Session):
    """Get all possible allergies/ingredients that can be allergies"""
    # In this system, allergies are just ingredients that users can be allergic to
    return get_all_ingredients(db)

def get_user_allergies(db: Session, user_id: str):
    """Get allergies for a specific user"""
    # Get the user's allergies from the allergies table
    allergies = db.query(Allergy, Ingredient).\
        join(Ingredient, Allergy.ingr_id == Ingredient.ingr_id).\
        filter(Allergy.user_id == user_id).all()
    
    if not allergies:
        return {"user_id": user_id, "allergies": []}
    
    # Convert to response format - return ingr_ids
    return {
        "user_id": user_id,
        "allergies": [allergy.ingr_id for allergy, _ in allergies]
    }

def set_user_allergies(db: Session, user_allergies: UserAllergies):
    """Set or update user allergies"""
    try:
        # Kullanıcının mevcut olup olmadığını kontrol edelim
        user = db.query(User).filter(User.user_id == user_allergies.user_id).first()
        if not user:
            return {"error": "User not found"}
            
        # Önce kullanıcının alerjilerini silelim
        db.query(Allergy).filter(Allergy.user_id == user_allergies.user_id).delete()
        
        # Yeni alerjileri ekleyelim
        for ingr_id in user_allergies.allergies:
            # Malzeme ID'sinin geçerli olup olmadığını kontrol edelim
            ingredient = db.query(Ingredient).filter(Ingredient.ingr_id == ingr_id).first()
            if ingredient:
                db.add(Allergy(user_id=user_allergies.user_id, ingr_id=ingr_id))
        
        db.commit()
        return {"message": "Allergies updated", "allergies": user_allergies}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

def get_user_recommendations(db: Session, user_id: str = None):
    """Get recipe recommendations for a user"""
    # Kullanıcının tercihlerini alalım
    user_preferences = []
    if user_id:
        # Kullanıcı tercihlerini sorgulayalım
        prefs_result = get_user_preferences(db, user_id)
        if prefs_result:
            user_preferences = prefs_result["preferences"]
    
    # Kullanıcının alerjilerini alalım
    user_allergies = []
    if user_id:
        # Kullanıcı alerjilerini sorgulayalım
        allergies_result = get_user_allergies(db, user_id)
        if allergies_result:
            user_allergies = allergies_result["allergies"]
    
    # Tarifleri sorgulayalım
    q = db.query(Recipe)
    
    # Kullanıcı tercihleri varsa, bu tercihlere uygun tarifleri filtreleyelim
    if user_preferences:
        # Kullanıcının tercihlerine uygun tariflerin ID'lerini bulalım
        recipe_ids = db.query(RecipeIngr.recipe_id).\
            join(PrefRecipe, Recipe.recipe_id == PrefRecipe.recipe_id).\
            filter(PrefRecipe.pref_id.in_(user_preferences)).\
            distinct().all()
        
        recipe_ids = [r[0] for r in recipe_ids]
        q = q.filter(Recipe.recipe_id.in_(recipe_ids))
    
    # Kullanıcının alerjileri varsa, bu alerjilere sahip tarifleri filtreleyelim
    if user_allergies:
        # Kullanıcının alerjileri olan malzemeleri içeren tariflerin ID'lerini bulalım
        excluded_recipe_ids = db.query(RecipeIngr.recipe_id).\
            filter(RecipeIngr.ingr_id.in_(user_allergies)).\
            distinct().all()
        
        excluded_recipe_ids = [r[0] for r in excluded_recipe_ids]
        if excluded_recipe_ids:
            q = q.filter(~Recipe.recipe_id.in_(excluded_recipe_ids))
    
    # Tarifleri alalım (en fazla 10 tane)
    recipes = q.limit(10).all()
    
    # Tariflerin detaylarını alalım
    result = []
    for recipe in recipes:
        recipe_data = get_recipe_details(db, recipe.recipe_id)
        if recipe_data:
            result.append(recipe_data)
    
    return result

def get_recipes_by_query(db: Session, query_json: str, sort_field: str = None, sort_direction: str = None):
    """Get recipes by a JSON query string"""
    try:
        query_data = json.loads(query_json)
        sort_data = {}
        if sort_field:
            sort_data["field"] = sort_field
            if sort_direction:
                sort_data["direction"] = sort_direction
        
        return query_recipes(db, query_data, sort_data)
    except Exception as e:
        return {"error": str(e)}

from app.models.models import PrefRecipe 