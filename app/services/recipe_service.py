from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.models import Category, Recipe, UserPref, Preference, Ingredient, RecipeIngr
from app.schemas.recipe_schema import RecipeDetails, RecipeCard, UserPreferences, RecipeQuery
from typing import List, Dict, Any

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

def get_user_preferences(db: Session, user_id: int):
    """Get user preferences by user ID"""
    # UserPref tablosundan kullanıcının tercihlerini alalım
    user_prefs = db.query(UserPref, Preference).\
        join(Preference, UserPref.pref_id == Preference.preference_id).\
        filter(UserPref.user_id == str(user_id)).all()
    
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
        db.query(UserPref).filter(UserPref.user_id == str(preferences.user_id)).delete()
        
        # Preference tablosundan tercihlerin ID'lerini alalım
        pref_map = {}
        all_prefs = db.query(Preference).all()
        for pref in all_prefs:
            pref_name = pref.name.lower() if pref.name else ""
            pref_map[pref_name] = pref.preference_id
        
        # Yeni tercihleri ekleyelim
        if preferences.dairy_free and "dairy_free" in pref_map:
            db.add(UserPref(user_id=str(preferences.user_id), pref_id=pref_map["dairy_free"]))
        
        if preferences.gluten_free and "gluten_free" in pref_map:
            db.add(UserPref(user_id=str(preferences.user_id), pref_id=pref_map["gluten_free"]))
        
        if preferences.pescetarian and "pescetarian" in pref_map:
            db.add(UserPref(user_id=str(preferences.user_id), pref_id=pref_map["pescetarian"]))
        
        if preferences.vegan and "vegan" in pref_map:
            db.add(UserPref(user_id=str(preferences.user_id), pref_id=pref_map["vegan"]))
        
        if preferences.vejetaryen and "vejetaryen" in pref_map:
            db.add(UserPref(user_id=str(preferences.user_id), pref_id=pref_map["vejetaryen"]))
        
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