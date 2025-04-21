from sqlalchemy.orm import Session
from app.models.models import Recipe, RecipeIngr, SavedRecipes, LikedRecipe, User, DislikedRecipe
from app.schemas.recipe_schema import Recipe as RecipeSchema
from typing import Dict, List, Any, Union
from sqlalchemy.sql import func
from sqlalchemy import Integer

def get_recipe_details(db: Session, recipe_id: int) -> RecipeSchema:
    """Tarif detaylarını getir"""
    recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
    if recipe is None:
        raise ValueError(f"Recipe with id {recipe_id} not found")
    
    # SQLAlchemy modelini dict'e çevir
    recipe_dict = {
        "recipe_id": recipe.recipe_id,
        "recipe_name": recipe.recipe_name,
        "instruction": recipe.instruction,
        "ingredient": recipe.ingredient,
        "total_time": recipe.total_time,
        "calories": recipe.calories,
        "fat": recipe.fat,
        "protein": recipe.protein,
        "carb": recipe.carb,
        "category": recipe.category
    }
    
    # Dict'i Pydantic modeline çevir
    return RecipeSchema(**recipe_dict)

def get_recipe_card(db: Session, recipe_id: int, fields: Union[List[str], str]) -> Dict[str, Any]:
    """Tarif kartı bilgilerini getir"""
    # Eğer fields bir string ise, virgülle ayrılmış liste olarak böl
    if isinstance(fields, str):
        fields = [f.strip() for f in fields.split(',')]
    
    # Tarifi getir
    recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
    if recipe is None:
        raise ValueError(f"Recipe with id {recipe_id} not found")
    
    # İstenen alanları döndür
    result = {}
    recipe_dict = vars(recipe)
    for field in fields:
        if field in recipe_dict:
            result[field] = recipe_dict[field]
    
    # Eğer malzemeler istendiyse, recipe_ingr tablosundan malzemeleri getir
    if 'ingredients' in fields:
        ingredients = db.query(RecipeIngr)\
            .filter(RecipeIngr.recipe_id == recipe_id)\
            .all()
        result['ingredients'] = [
            {
                'ingr_id': ingr.ingr_id,
                'quantity': ingr.quantity,
                'unit': ingr.unit
            } for ingr in ingredients
        ]
    
    return result

def get_user_saved_recipes(db: Session, user_id: str) -> List[RecipeSchema]:
    """Kullanıcının kaydettiği tarifleri getir"""
    saved_recipes = db.query(Recipe)\
        .join(SavedRecipes)\
        .filter(SavedRecipes.user_id == user_id)\
        .all()
    
    return [RecipeSchema(
        recipe_id=recipe.recipe_id,
        recipe_name=recipe.recipe_name,
        instruction=recipe.instruction,
        ingredient=recipe.ingredient,
        total_time=recipe.total_time,
        calories=recipe.calories,
        fat=recipe.fat,
        protein=recipe.protein,
        carb=recipe.carb,
        category=recipe.category
    ) for recipe in saved_recipes]

def set_user_saved_recipes(db: Session, user_id: str, recipe_ids: List[int]):
    """Kullanıcının kaydettiği tarifleri güncelle"""
    # Önce kullanıcının tüm kayıtlı tariflerini sil
    db.query(SavedRecipes).filter(SavedRecipes.user_id == user_id).delete()
    
    # Yeni tarifleri ekle
    for recipe_id in recipe_ids:
        # Tarif ID'sinin geçerli olduğunu kontrol et
        recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
        if not recipe:
            raise ValueError(f"Recipe with id {recipe_id} not found")
            
        saved_recipe = SavedRecipes(
            user_id=user_id,
            recipe_id=recipe_id,
            updated_at=func.now()  # Güncel zaman damgası ekle - Celery tarafından kullanılacak
        )
        db.add(saved_recipe)
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise ValueError(f"Error saving recipes: {str(e)}")

def get_user_liked_recipes(db: Session, user_id: str) -> List[RecipeSchema]:
    """Kullanıcının beğendiği tarifleri getir"""
    # Kullanıcı var mı kontrol et
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise ValueError(f"User with id {user_id} not found")
        
    liked_recipes = db.query(Recipe)\
        .join(LikedRecipe)\
        .filter(LikedRecipe.user_id == user_id)\
        .all()
    
    return [RecipeSchema(
        recipe_id=recipe.recipe_id,
        recipe_name=recipe.recipe_name,
        instruction=recipe.instruction,
        ingredient=recipe.ingredient,
        total_time=recipe.total_time,
        calories=recipe.calories,
        fat=recipe.fat,
        protein=recipe.protein,
        carb=recipe.carb,
        category=recipe.category
    ) for recipe in liked_recipes]

def like_recipe(db: Session, user_id: str, recipe_id: int):
    """Kullanıcının bir tarifi beğenmesini sağla"""
    # Kullanıcı ve tarif var mı kontrol et
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise ValueError(f"User with id {user_id} not found")
    recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
    if not recipe:
        raise ValueError(f"Recipe with id {recipe_id} not found")
        
    # Daha önce beğenilmiş mi kontrol et
    existing_like = db.query(LikedRecipe)\
        .filter(LikedRecipe.user_id == user_id, LikedRecipe.recipe_id == recipe_id)\
        .first()
        
    if existing_like:
        # Zaten beğenilmiş, sadece zaman damgasını güncelle (veya hata ver)
        existing_like.updated_at = func.now()
    else:
        # Yeni beğeni ekle
        new_like = LikedRecipe(
            user_id=user_id,
            recipe_id=recipe_id,
            updated_at=func.now() # Celery için
        )
        db.add(new_like)
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise ValueError(f"Error liking recipe: {str(e)}")

def unlike_recipe(db: Session, user_id: str, recipe_id: int):
    """Kullanıcının bir tarif beğenisini geri almasını sağla"""
    # Kullanıcı ve tarif var mı kontrol et
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise ValueError(f"User with id {user_id} not found")
    recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
    if not recipe:
        raise ValueError(f"Recipe with id {recipe_id} not found")
        
    # Beğeni kaydını bul ve sil
    like_record = db.query(LikedRecipe)\
        .filter(LikedRecipe.user_id == user_id, LikedRecipe.recipe_id == recipe_id)\
        .first()
        
    if not like_record:
        raise ValueError(f"Recipe {recipe_id} is not liked by user {user_id}")
        
    db.delete(like_record)
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise ValueError(f"Error unliking recipe: {str(e)}")

def get_user_disliked_recipes(db: Session, user_id: str) -> List[RecipeSchema]:
    """Kullanıcının beğenmediği tarifleri getir"""
    # Kullanıcı var mı kontrol et
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise ValueError(f"User with id {user_id} not found")
        
    disliked_recipes = db.query(Recipe)\
        .join(DislikedRecipe, Recipe.recipe_id == DislikedRecipe.recipe_id.cast(Integer))\
        .filter(DislikedRecipe.user_id == user_id)\
        .all()
    
    # TODO: Pydantic şeması Recipe yerine daha minimal bir şey olabilir mi?
    return [RecipeSchema(
        recipe_id=recipe.recipe_id,
        recipe_name=recipe.recipe_name,
        instruction=recipe.instruction,
        ingredient=recipe.ingredient,
        total_time=recipe.total_time,
        calories=recipe.calories,
        fat=recipe.fat,
        protein=recipe.protein,
        carb=recipe.carb,
        category=recipe.category
    ) for recipe in disliked_recipes]

def dislike_recipe(db: Session, user_id: str, recipe_id: int):
    """Kullanıcının bir tarifi beğenmemesini sağla"""
    # Kullanıcı ve tarif var mı kontrol et
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise ValueError(f"User with id {user_id} not found")
    recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
    if not recipe:
        raise ValueError(f"Recipe with id {recipe_id} not found")
        
    # Daha önce beğenilmemiş mi kontrol et
    existing_dislike = db.query(DislikedRecipe)\
        .filter(DislikedRecipe.user_id == user_id, DislikedRecipe.recipe_id.cast(Integer) == recipe_id)\
        .first()
        
    if existing_dislike:
        # Zaten beğenilmemiş, sadece zaman damgasını güncelle
        existing_dislike.updated_at = func.now()
    else:
        # Yeni beğenmeme kaydı ekle
        new_dislike = DislikedRecipe(
            user_id=user_id,
            recipe_id=str(recipe_id), # Veritabanı text beklediği için string'e çevirerek ekle
            updated_at=func.now() # Celery için
        )
        db.add(new_dislike)
        
        # Eğer tarif daha önce beğenildiyse, beğeniyi kaldır
        like_record = db.query(LikedRecipe)\
            .filter(LikedRecipe.user_id == user_id, LikedRecipe.recipe_id == recipe_id)\
            .first()
        if like_record:
            db.delete(like_record)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise ValueError(f"Error disliking recipe: {str(e)}")

def undislike_recipe(db: Session, user_id: str, recipe_id: int):
    """Kullanıcının bir tarif beğenmemesini geri almasını sağla"""
    # Kullanıcı ve tarif var mı kontrol et
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise ValueError(f"User with id {user_id} not found")
    recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
    if not recipe:
        raise ValueError(f"Recipe with id {recipe_id} not found")
        
    # Beğenmeme kaydını bul ve sil
    dislike_record = db.query(DislikedRecipe)\
        .filter(DislikedRecipe.user_id == user_id, DislikedRecipe.recipe_id.cast(Integer) == recipe_id)\
        .first()
        
    if not dislike_record:
        raise ValueError(f"Recipe {recipe_id} is not disliked by user {user_id}")
        
    db.delete(dislike_record)
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise ValueError(f"Error undisliking recipe: {str(e)}") 