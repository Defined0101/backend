from sqlalchemy.orm import Session
from app.models.models import Recipe, RecipeIngr, SavedRecipes
from app.schemas.recipe_schema import Recipe as RecipeSchema
from typing import Dict, List, Any, Union

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