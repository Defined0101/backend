from sqlalchemy.orm import Session, joinedload
from app.models.models import Recipe, RecipeIngr, SavedRecipes, LikedRecipe, User, DislikedRecipe, Ingredient as IngredientModel, Preference, PrefRecipe, Category as CategoryModel, RecipeCategoryLink
from app.schemas.recipe_schema import Recipe as RecipeSchema
from app.schemas.ingredient_schema import RecipeIngredientDetail
from typing import Dict, List, Any, Union, Optional
from sqlalchemy.sql import func
from sqlalchemy import Integer, text
from app.utils.embedding_tracker import mark_user_for_update

# Qdrant ve Ayarlar için importlar
from app.services.qdrant_service import QdrantService
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# --- Helper function to build the label list ---
def _build_recipe_label_list(db: Session, recipe: Recipe) -> List[str]:
    """Helper function to create the label list (names of true preferences) for a given recipe."""
    # Ensure pref_recipes and their preferences are loaded
    if not hasattr(recipe, 'pref_recipes'): # Check if relationship was loaded
         # If not loaded, query explicitly (less efficient)
         recipe_pref_links = db.query(PrefRecipe).filter(PrefRecipe.recipe_id == recipe.recipe_id).options(joinedload(PrefRecipe.preference)).all()
         recipe_pref_names = [pref_link.preference.pref_name 
                              for pref_link in recipe_pref_links 
                              if pref_link.preference and pref_link.preference.pref_name]
    else:
         # Use the pre-loaded relationship
        recipe_pref_names = [pref_recipe.preference.pref_name 
                             for pref_recipe in recipe.pref_recipes 
                             if pref_recipe.preference and pref_recipe.preference.pref_name]

    return sorted(recipe_pref_names)

# --- Yeni Helper: Recipe ID için Category ismini bulma ---
def _get_category_name_for_recipe(db: Session, recipe_id: int) -> Optional[str]:
    """Queries recipe_cat and category tables to find the category name for a given recipe_id."""
    link = db.query(RecipeCategoryLink).filter(RecipeCategoryLink.recipe_id == recipe_id).first()
    if link and link.cat_id:
        category = db.query(CategoryModel).filter(CategoryModel.category_id == link.cat_id).first()
        if category:
            return category.cat_name
    return None

def get_recipe_details(db: Session, recipe_id: int) -> RecipeSchema:
    """Tarif detaylarını getir (category string olarak)"""
    recipe = db.query(Recipe)\
        .options(
            joinedload(Recipe.recipe_ingredients).joinedload(RecipeIngr.ingredient),
            joinedload(Recipe.pref_recipes).joinedload(PrefRecipe.preference)
        )\
        .filter(Recipe.recipe_id == recipe_id).first()
    if recipe is None:
        raise ValueError(f"Recipe with id {recipe_id} not found")
    
    ingredients_list = []
    if recipe.recipe_ingredients:
        for ri in recipe.recipe_ingredients:
            if ri.ingredient:
                ingredient_detail = RecipeIngredientDetail.model_validate(ri.ingredient, context={'quantity': ri.quantity, 'unit': ri.unit})
                if not ingredient_detail.unit: # Check if None or empty string
                    ingredient_detail.unit = "piece"
                if ingredient_detail.quantity is None: # Check if quantity is None
                    ingredient_detail.quantity = 1.0
                ingredients_list.append(ingredient_detail)

    label_list = _build_recipe_label_list(db, recipe)
    category_name = _get_category_name_for_recipe(db, recipe.recipe_id)

    # Önce modelden şemayı oluştur
    recipe_data = RecipeSchema.model_validate(recipe)
    # Sonra hesaplanan alanları ata (ingredients ismiyle)
    recipe_data.ingredients = ingredients_list
    recipe_data.label = label_list
    recipe_data.category = category_name
    return recipe_data

def get_recipe_card(db: Session, recipe_id: int, fields: Union[List[str], str]) -> Dict[str, Any]:
    """Tarif kartı bilgilerini getir (category ismi recipe_cat'ten alınır)"""
    if isinstance(fields, str):
        fields = [f.strip() for f in fields.split(',')]
    
    # Determine if related data needs loading
    query_options = []
    if 'ingredients' in fields:
        query_options.append(joinedload(Recipe.recipe_ingredients).joinedload(RecipeIngr.ingredient))

    recipe = db.query(Recipe).options(*query_options).filter(Recipe.recipe_id == recipe_id).first()
    if recipe is None:
        raise ValueError(f"Recipe with id {recipe_id} not found")
    
    result = {}
    recipe_dict = {c.name: getattr(recipe, c.name) for c in recipe.__table__.columns}

    for field in fields:
        if field == 'ingredients':
            result['ingredients'] = None # TODO: Ingredient yükleme mantığını gözden geçir
        elif field == 'category':
            result['category'] = _get_category_name_for_recipe(db, recipe_id)
        elif field in recipe_dict:
            result[field] = recipe_dict[field]
    
    return result

def get_user_saved_recipes(db: Session, user_id: str) -> List[RecipeSchema]:
    """Kullanıcının kaydettiği tarifleri getir (category string olarak)"""
    saved_recipes_query = db.query(Recipe)\
        .join(SavedRecipes)\
        .filter(SavedRecipes.user_id == user_id)\
        .options(
            joinedload(Recipe.recipe_ingredients).joinedload(RecipeIngr.ingredient),
            joinedload(Recipe.pref_recipes).joinedload(PrefRecipe.preference)
        )
    saved_recipes = saved_recipes_query.all()
    
    result_list = []
    for recipe in saved_recipes:
        ingredients_list = []
        if recipe.recipe_ingredients:
            for ri in recipe.recipe_ingredients:
                if ri.ingredient:
                    ingredient_detail = RecipeIngredientDetail.model_validate(ri.ingredient, context={'quantity': ri.quantity, 'unit': ri.unit})
                    if not ingredient_detail.unit: # Check if unit is None or empty
                        ingredient_detail.unit = "piece"
                    if ingredient_detail.quantity is None: # Check if quantity is None
                        ingredient_detail.quantity = 1.0
                    ingredients_list.append(ingredient_detail)
        
        label_list = sorted([pref_recipe.preference.pref_name
                             for pref_recipe in recipe.pref_recipes
                             if pref_recipe.preference and pref_recipe.preference.pref_name])
        category_name = _get_category_name_for_recipe(db, recipe.recipe_id)

        recipe_data = RecipeSchema.model_validate(recipe)
        recipe_data.ingredients = ingredients_list
        recipe_data.label = label_list
        recipe_data.category = category_name
        result_list.append(recipe_data)
    return result_list

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
            recipe_id=recipe_id
        )
        db.add(saved_recipe)
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise ValueError(f"Error saving recipes: {str(e)}")

def get_user_liked_recipes(db: Session, user_id: str) -> List[RecipeSchema]:
    """Kullanıcının beğendiği tarifleri getir (category string olarak)"""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise ValueError(f"User with id {user_id} not found")
        
    liked_recipes_query = db.query(Recipe)\
        .join(LikedRecipe)\
        .filter(LikedRecipe.user_id == user_id)\
        .options(
            joinedload(Recipe.recipe_ingredients).joinedload(RecipeIngr.ingredient),
            joinedload(Recipe.pref_recipes).joinedload(PrefRecipe.preference)
        )
    liked_recipes = liked_recipes_query.all()
    
    result_list = []
    for recipe in liked_recipes:
        ingredients_list = []
        if recipe.recipe_ingredients:
             for ri in recipe.recipe_ingredients:
                 if ri.ingredient:
                    ingredient_detail = RecipeIngredientDetail.model_validate(ri.ingredient, context={'quantity': ri.quantity, 'unit': ri.unit})
                    if not ingredient_detail.unit:
                        ingredient_detail.unit = "piece"
                    if ingredient_detail.quantity is None:
                        ingredient_detail.quantity = 1.0
                    ingredients_list.append(ingredient_detail)
        
        label_list = sorted([pref_recipe.preference.pref_name
                             for pref_recipe in recipe.pref_recipes
                             if pref_recipe.preference and pref_recipe.preference.pref_name])
        category_name = _get_category_name_for_recipe(db, recipe.recipe_id)

        recipe_data = RecipeSchema.model_validate(recipe)
        recipe_data.ingredients = ingredients_list
        recipe_data.label = label_list
        recipe_data.category = category_name
        result_list.append(recipe_data)
    return result_list

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
        mark_user_for_update(user_id)
    except Exception as e:
        db.rollback()
        raise ValueError(f"Error unliking recipe: {str(e)}")

def get_user_disliked_recipes(db: Session, user_id: str) -> List[RecipeSchema]:
    """Kullanıcının beğenmediği tarifleri getir (category string olarak)"""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise ValueError(f"User with id {user_id} not found")
        
    disliked_recipes_query = db.query(Recipe)\
        .join(DislikedRecipe)\
        .filter(DislikedRecipe.user_id == user_id)\
        .options(
            joinedload(Recipe.recipe_ingredients).joinedload(RecipeIngr.ingredient),
            joinedload(Recipe.pref_recipes).joinedload(PrefRecipe.preference)
        )
    disliked_recipes = disliked_recipes_query.all()
    
    result_list = []
    for recipe in disliked_recipes:
        ingredients_list = []
        if recipe.recipe_ingredients:
             for ri in recipe.recipe_ingredients:
                 if ri.ingredient:
                    ingredient_detail = RecipeIngredientDetail.model_validate(ri.ingredient, context={'quantity': ri.quantity, 'unit': ri.unit})
                    if not ingredient_detail.unit:
                        ingredient_detail.unit = "piece"
                    if ingredient_detail.quantity is None:
                        ingredient_detail.quantity = 1.0
                    ingredients_list.append(ingredient_detail)
        
        label_list = sorted([pref_recipe.preference.pref_name
                             for pref_recipe in recipe.pref_recipes
                             if pref_recipe.preference and pref_recipe.preference.pref_name])
        category_name = _get_category_name_for_recipe(db, recipe.recipe_id)

        recipe_data = RecipeSchema.model_validate(recipe)
        recipe_data.ingredients = ingredients_list
        recipe_data.label = label_list
        recipe_data.category = category_name
        result_list.append(recipe_data)
    return result_list

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
        mark_user_for_update(user_id)
    except Exception as e:
        db.rollback()
        raise ValueError(f"Error undisliking recipe: {str(e)}")
    
def get_user_liked_recipes_ids(db: Session, user_id: str) -> List[int]:
    """Return list of liked recipe IDs (for embedding only)"""
    liked = db.query(LikedRecipe.recipe_id)\
        .filter(LikedRecipe.user_id == user_id).all()
    return [r.recipe_id for r in liked]

def get_user_disliked_recipes_ids(db: Session, user_id: str) -> List[int]:
    """Return list of disliked recipe IDs (for embedding only)"""
    disliked = db.query(DislikedRecipe.recipe_id)\
        .filter(DislikedRecipe.user_id == user_id).all()
    return [int(r.recipe_id) for r in disliked]

def save_recipe(db: Session, user_id: str, recipe_id: int):
    """Kullanıcının tek bir tarifi kaydetmesini sağla"""
    # Kullanıcı ve tarif var mı kontrol et
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise ValueError(f"User with id {user_id} not found")
    recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
    if not recipe:
        raise ValueError(f"Recipe with id {recipe_id} not found")

    # Daha önce kaydedilmiş mi kontrol et
    existing_save = db.query(SavedRecipes)\
        .filter(SavedRecipes.user_id == user_id, SavedRecipes.recipe_id == recipe_id)\
        .first()

    if existing_save:
        # Zaten kaydedilmiş, bir şey yapmaya gerek yok (veya hata verilebilir)
        pass
    else:
        # Yeni kayıt ekle
        new_save = SavedRecipes(
            user_id=user_id,
            recipe_id=recipe_id
        )
        db.add(new_save)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise ValueError(f"Error saving recipe: {str(e)}")

def unsave_recipe(db: Session, user_id: str, recipe_id: int):
    """Kullanıcının tek bir tarif kaydını silmesini sağla"""
    # Kullanıcı ve tarif var mı kontrol et
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise ValueError(f"User with id {user_id} not found")
    recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
    if not recipe:
        raise ValueError(f"Recipe with id {recipe_id} not found")

    # Kayıtlı tarifi bul ve sil
    save_record = db.query(SavedRecipes)\
        .filter(SavedRecipes.user_id == user_id, SavedRecipes.recipe_id == recipe_id)\
        .first()

    if not save_record:
        raise ValueError(f"Recipe {recipe_id} is not saved by user {user_id}")

    db.delete(save_record)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise ValueError(f"Error unsaving recipe: {str(e)}")

def get_surprise_recipe_id(db: Session, user_id: str) -> RecipeSchema:
    """Kullanıcı için sürpriz bir tarif önerisi getir (beğenmedikleri hariç)"""
    # TODO: Bu fonksiyon sadece ID dönmeli ve ismi get_surprise_recipe_id olmalı.
    # Mevcut hali RecipeSchema dönüyor, bu API katmanında düzeltilmeli.
    
    # Kullanıcının beğenmediği tariflerin ID'lerini al
    disliked_recipe_ids_query = db.query(DislikedRecipe.recipe_id).filter(DislikedRecipe.user_id == user_id)
    disliked_recipe_ids = [int(r[0]) for r in disliked_recipe_ids_query.all()]
    
    # Beğenilmeyenler dışındaki rastgele bir tarifi seç
    # order_by(func.random()) veritabanına göre değişebilir (PostgreSQL için çalışır)
    random_recipe = db.query(Recipe)\
        .filter(Recipe.recipe_id.notin_(disliked_recipe_ids))\
        .order_by(func.random())\
        .first()
        
    if not random_recipe:
        # Eğer beğenilmeyenler dışında tarif kalmadıysa veya hiç tarif yoksa
        # herhangi bir rastgele tarif seç
        random_recipe = db.query(Recipe).order_by(func.random()).first()
        
    if not random_recipe:
        raise ValueError("No recipes available in the database")
        
    # TODO: API bunu sadece ID olarak istemişti, şimdilik tam objeyi schema'ya çevirip dönüyoruz.
    return RecipeSchema(
        recipe_id=random_recipe.recipe_id,
        recipe_name=random_recipe.recipe_name,
        instruction=random_recipe.instruction,
        ingredient=random_recipe.ingredient,
        total_time=random_recipe.total_time,
        calories=random_recipe.calories,
        fat=random_recipe.fat,
        protein=random_recipe.protein,
        carb=random_recipe.carb,
        category=random_recipe.category
    )

# --- YENİ FONKSİYON --- 
def get_user_recommendations(db: Session, user_id: str, limit: int = 10) -> List[RecipeSchema]:
    """Kullanıcı için Qdrant vektör araması kullanarak tarif önerileri getirir."""
    try:
        qdrant_service = QdrantService(config=settings)
        recommended_data = qdrant_service.recommend_recipe(user_id=int(user_id), limit=limit)

        if not recommended_data:
            logger.info(f"No recommendations found for user {user_id} from Qdrant.")
            return []

        recommended_ids = [item['id'] for item in recommended_data]
        
        if not recommended_ids:
            return []

        recipes = db.query(Recipe)\
            .filter(Recipe.recipe_id.in_(recommended_ids))\
            .options(
                joinedload(Recipe.recipe_ingredients).joinedload(RecipeIngr.ingredient),
                joinedload(Recipe.pref_recipes).joinedload(PrefRecipe.preference)
            )\
            .all()
        
        recipe_map = {recipe.recipe_id: recipe for recipe in recipes}
        
        ordered_recipes = []
        for rec_id in recommended_ids:
            if rec_id in recipe_map:
                recipe = recipe_map[rec_id]
                ingredients_list = []
                if recipe.recipe_ingredients:
                    for ri in recipe.recipe_ingredients:
                        if ri.ingredient:
                            ingredient_detail = RecipeIngredientDetail.model_validate(ri.ingredient, context={'quantity': ri.quantity, 'unit': ri.unit})
                            if not ingredient_detail.unit:
                                ingredient_detail.unit = "piece"
                            if ingredient_detail.quantity is None:
                                ingredient_detail.quantity = 1.0
                            ingredients_list.append(ingredient_detail)
                
                # --- Build label list directly from pre-loaded data ---
                label_list = sorted([pref_recipe.preference.pref_name 
                                     for pref_recipe in recipe.pref_recipes 
                                     if pref_recipe.preference and pref_recipe.preference.pref_name])
                
                category_name = _get_category_name_for_recipe(db, recipe.recipe_id)
                
                # Düzeltme: Önce validate et, sonra ata
                recipe_data = RecipeSchema.model_validate(recipe)
                recipe_data.ingredients = ingredients_list
                recipe_data.label = label_list
                recipe_data.category = category_name
                ordered_recipes.append(recipe_data)
            else:
                logger.warning(f"Recipe ID {rec_id} recommended by Qdrant but not found in DB.")

        return ordered_recipes

    except ValueError as e:
        logger.error(f"Error getting recommendations for user {user_id}: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error getting recommendations for user {user_id}: {e}")
        return [] 