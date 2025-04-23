from sqlalchemy.orm import Session
from app.models.models import Recipe, RecipeIngr, SavedRecipes, LikedRecipe, User, DislikedRecipe
from app.schemas.recipe_schema import Recipe as RecipeSchema
from typing import Dict, List, Any, Union
from sqlalchemy.sql import func
from sqlalchemy import Integer, text

# Qdrant ve Ayarlar için importlar
from app.services.qdrant_service import QdrantService
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

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
            recipe_id=recipe_id
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
        # Qdrant servisini başlat
        # Not: Ayarlar (settings) doğrudan import edildi, bu büyük uygulamalarda
        # dependency injection ile daha iyi yönetilebilir.
        qdrant_service = QdrantService(config=settings)

        # Qdrant'tan önerilen tarif bilgilerini (ID ve payload) al
        # recommend_recipe, beğenilmeyenleri zaten filtreliyor olmalı.
        recommended_data = qdrant_service.recommend_recipe(user_id=int(user_id), limit=limit)

        if not recommended_data:
            logger.info(f"No recommendations found for user {user_id} from Qdrant.")
            return []

        # Önerilen tariflerin ID'lerini çıkar
        recommended_ids = [item['id'] for item in recommended_data]
        
        if not recommended_ids:
            return []

        # Veritabanından tam tarif detaylarını çek
        recipes = db.query(Recipe).filter(Recipe.recipe_id.in_(recommended_ids)).all()
        
        # Qdrant'tan gelen sırayı korumak için ID'ye göre map oluştur
        recipe_map = {recipe.recipe_id: recipe for recipe in recipes}
        
        # Sonuçları Qdrant sırasına göre ve RecipeSchema formatında oluştur
        ordered_recipes = []
        for rec_id in recommended_ids:
            if rec_id in recipe_map:
                recipe = recipe_map[rec_id]
                ordered_recipes.append(RecipeSchema(
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
                ))
            else:
                logger.warning(f"Recipe ID {rec_id} recommended by Qdrant but not found in DB.")

        return ordered_recipes

    except ValueError as e:
        # Qdrant servisi veya DB sorgusu sırasında beklenen hatalar (örn. kullanıcı bulunamadı)
        logger.error(f"Error getting recommendations for user {user_id}: {e}")
        raise # API katmanının işlemesi için hatayı tekrar yükselt
    except Exception as e:
        # Beklenmedik diğer hatalar
        logger.exception(f"Unexpected error getting recommendations for user {user_id}: {e}")
        # Beklenmedik hatalarda boş liste dönmek daha güvenli olabilir veya hatayı yükseltmek.
        # Şimdilik boş liste dönelim.
        return [] 