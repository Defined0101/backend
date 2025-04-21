from sqlalchemy.orm import Session
from sqlalchemy import func, String, Integer
from app.models.models import Ingredient, Allergy, User, Inventory
from typing import List, Optional, Text
from app.schemas.ingredient_schema import IngredientCreate, UserIngredients, IngredientResponse, UserAllergies

def get_ingredient_names(db: Session) -> List[str]:
    """Tüm malzeme isimlerini getir"""
    ingredients = db.query(Ingredient.ingr_name)\
        .order_by(Ingredient.ingr_name)\
        .all()
    return [ingredient[0] for ingredient in ingredients]

def get_all_allergies(db: Session) -> List[str]:
    """Sistemdeki tüm alerjen malzemeleri getir"""
    allergies = db.query(Ingredient.ingr_name)\
        .join(Allergy, Allergy.ingr_id == Ingredient.ingr_id)\
        .distinct()\
        .order_by(Ingredient.ingr_name)\
        .all()
    return [allergy[0] for allergy in allergies]

def get_user_allergies(db: Session, user_id: str) -> List[str]:
    """Kullanıcının alerjik olduğu malzemeleri getir"""
    # Materialized view kullan
    allergies = db.query(func.distinct(UserAllergiesView.ingr_name))\
        .filter(UserAllergiesView.user_id == user_id)\
        .order_by(UserAllergiesView.ingr_name)\
        .all()
    return [allergy[0] for allergy in allergies]

def set_user_allergies(db: Session, user_allergies: UserAllergies) -> List[str]:
    """Kullanıcının alerjik olduğu malzemeleri güncelle"""
    # Önce mevcut alerjileri sil
    db.query(Allergy).filter(Allergy.user_id == user_allergies.user_id).delete()
    
    # Yeni alerjileri ekle
    for allergy_name in user_allergies.allergies:
        # Malzeme var mı kontrol et
        ingredient = db.query(Ingredient).filter(Ingredient.ingr_name == allergy_name).first()
        if not ingredient:
            # Malzeme yoksa oluştur
            ingredient = Ingredient(ingr_name=allergy_name)
            db.add(ingredient)
            db.flush()  # ID'yi almak için flush
        
        # Alerjiyi ekle
        allergy = Allergy(
            user_id=user_allergies.user_id,
            ingr_id=ingredient.ingr_id
        )
        db.add(allergy)
    
    db.commit()
    return user_allergies.allergies

def get_user_ingredients(db: Session, user_id: str) -> List[dict]:
    """Kullanıcının malzemelerini ve miktarlarını getir"""
    # Materialized view kullan
    ingredients = db.query(UserInventoryView.ingr_name, UserInventoryView.quantity)\
        .filter(UserInventoryView.user_id == user_id)\
        .order_by(UserInventoryView.ingr_name)\
        .all()
    return [{"ingredient_name": name, "quantity": float(qty) if qty else 1.0} 
            for name, qty in ingredients]

def set_user_ingredients(db: Session, user_ingredients: UserIngredients) -> List[dict]:
    """Kullanıcının malzemelerini güncelle"""
    # Önce mevcut malzemeleri sil
    db.query(Inventory).filter(Inventory.user_id == user_ingredients.user_id).delete()
    
    result = []
    # Yeni malzemeleri ekle
    for item in user_ingredients.ingredients:
        # Malzeme var mı kontrol et
        ingredient = db.query(Ingredient).filter(Ingredient.ingr_name == item.ingredient_name).first()
        if not ingredient:
            # Malzeme yoksa oluştur
            ingredient = Ingredient(ingr_name=item.ingredient_name)
            db.add(ingredient)
            db.flush()  # ID'yi almak için flush
        
        # Malzemeyi envantere ekle
        inventory = Inventory(
            user_id=user_ingredients.user_id,
            ingr_id=str(ingredient.ingr_id),  # inventory tablosunda ingr_id text olarak tanımlı
            quantity=item.quantity if item.quantity else 1.0
        )
        db.add(inventory)
        result.append({
            "ingredient_name": item.ingredient_name,
            "quantity": float(item.quantity) if item.quantity else 1.0
        })
    
    db.commit()
    return result

def get_user(db: Session, user_id: str) -> Optional[User]:
    """Kullanıcıyı ID'ye göre getir"""
    return db.query(User).filter(User.user_id == user_id).first()

def get_all_ingredients(db: Session, page: int = 1, page_size: int = 50, search: str = None) -> IngredientResponse:
    """
    Malzemeleri sayfalı şekilde getir
    
    Args:
        db (Session): Veritabanı oturumu
        page (int): Sayfa numarası
        page_size (int): Sayfa başına malzeme sayısı
        search (str, optional): Malzeme adına göre arama
        
    Returns:
        IngredientResponse: Sayfalanmış malzeme listesi ve meta bilgiler
    """
    # Base query
    query = db.query(Ingredient)
    
    # Arama filtresi
    if search:
        search = f"%{search}%"
        query = query.filter(Ingredient.ingr_name.ilike(search))
    
    # Toplam kayıt sayısı
    total = query.count()
    
    # Sayfalama
    query = query.order_by(Ingredient.ingr_name)
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    # Sonuçları al
    ingredients = query.all()
    
    # Toplam sayfa sayısı
    total_pages = (total + page_size - 1) // page_size
    
    return IngredientResponse(
        items=ingredients,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1
    ) 