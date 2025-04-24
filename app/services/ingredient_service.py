from sqlalchemy.orm import Session
from sqlalchemy import func, String, Integer
from app.models.models import Ingredient, Allergy, User, Inventory, UserAllergiesView, UserInventoryView
from typing import List, Optional, Text
from app.schemas.ingredient_schema import IngredientCreate, UserIngredients, IngredientResponse, UserAllergies, IngredientBase

def get_ingredient_names(db: Session) -> List[str]:
    """Tüm malzeme isimlerini getir"""
    ingredients = db.query(Ingredient.name)\
        .order_by(Ingredient.name)\
        .all()
    return [ingredient[0] for ingredient in ingredients]

def get_all_allergies(db: Session) -> List[str]:
    """Sistemdeki tüm alerjen malzemeleri getir"""
    allergies = db.query(Ingredient.name)\
        .join(Allergy, Allergy.ingr_id == Ingredient.ingr_id)\
        .distinct()\
        .order_by(Ingredient.name)\
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
        ingredient = db.query(Ingredient).filter(Ingredient.name == allergy_name).first()
        if not ingredient:
            # Malzeme yoksa oluştur
            ingredient = Ingredient(name=allergy_name)
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
    """Kullanıcının malzemelerini, miktarlarını ve birimlerini getir"""
    # Materialized view ve Ingredient tablosunu ingr_id üzerinden join et
    ingredients_data = db.query(
            UserInventoryView.ingr_name,
            UserInventoryView.quantity,
            UserInventoryView.unit,          # View'daki unit sütununu da seç
            Ingredient.default_unit          # Ingredient tablosundaki default_unit'i de seç
        )\
        .join(Ingredient, UserInventoryView.ingr_id == Ingredient.ingr_id)\
        .filter(UserInventoryView.user_id == user_id)\
        .order_by(UserInventoryView.ingr_name)\
        .all()

    result = []
    for name_from_view, qty, user_unit, default_unit in ingredients_data:
        # Önce view'daki unit değerine bak, null ise ingredient'teki default_unit'e bak, 
        # o da null ise "piece" kullan
        final_unit = user_unit or default_unit or "piece"
        
        result.append({
            "name": name_from_view,
            "quantity": float(qty) if qty else 1.0,
            "unit": final_unit
        })
    return result

def set_user_ingredients(db: Session, user_ingredients: UserIngredients) -> List[dict]:
    """Kullanıcının malzemelerini güncelle ve birimleri de içeren listeyi döndür"""
    # Önce mevcut malzemeleri sil
    db.query(Inventory).filter(Inventory.user_id == user_ingredients.user_id).delete()

    result = []
    # Yeni malzemeleri ekle
    for item in user_ingredients.ingredients:
        # Malzeme var mı kontrol et
        ingredient = db.query(Ingredient).filter(Ingredient.name == item.name).first()
        if not ingredient:
            # Malzeme yoksa oluştur (default_unit null olacak)
            ingredient = Ingredient(name=item.name)
            db.add(ingredient)
            db.flush()  # ID'yi almak için flush

        # Kullanıcının belirttiği unit'i kullan, yoksa ingredient'taki default'u, o da yoksa "piece"
        unit = item.unit or ingredient.default_unit or "piece"
        
        # Malzemeyi envantere ekle - unit değeri de yazılıyor
        inventory = Inventory(
            user_id=user_ingredients.user_id,
            ingr_id=ingredient.ingr_id,
            quantity=item.quantity if item.quantity else 1.0,
            unit=unit  # unit değerini de ekle
        )
        db.add(inventory)

        # Sonuç listesine aynı unit değerini ekle
        result.append({
            "name": item.name,
            "quantity": float(item.quantity) if item.quantity else 1.0,
            "unit": unit
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
        query = query.filter(Ingredient.name.ilike(search))
    
    # Toplam kayıt sayısı
    total = query.count()
    
    # Sayfalama
    query = query.order_by(Ingredient.name)
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    # Sonuçları al
    ingredients_db = query.all()

    # Process ingredients to set default_unit
    processed_ingredients = []
    for ingredient in ingredients_db:
        if not ingredient.default_unit: # Check if None or empty
            ingredient.default_unit = "piece"
        processed_ingredients.append(ingredient) # Use the modified ingredient object
    
    # Toplam sayfa sayısı
    total_pages = (total + page_size - 1) // page_size
    
    return IngredientResponse(
        items=processed_ingredients, # Pass the processed list
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1
    ) 