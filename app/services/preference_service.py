from sqlalchemy.orm import Session
from app.models.models import Category, Preference, UserPref
from typing import List
from app.schemas.preference_schema import UserPreferences

def get_categories(db: Session) -> List[str]:
    """Tüm kategorileri getir"""
    categories = db.query(Category.cat_name)\
        .order_by(Category.cat_name)\
        .all()
    return [category[0] for category in categories if category[0]]

def get_preferences(db: Session) -> List[str]:
    """Tüm tercihleri getir"""
    preferences = db.query(Preference.pref_name)\
        .order_by(Preference.pref_name)\
        .all()
    return [pref[0] for pref in preferences if pref[0]]

def get_user_preferences(db: Session, user_id: str) -> List[str]:
    """Kullanıcının tercihlerini getir"""
    preferences = db.query(Preference.pref_name)\
        .join(UserPref, UserPref.pref_id == Preference.pref_id)\
        .filter(UserPref.user_id == user_id)\
        .order_by(Preference.pref_name)\
        .all()
    return [pref[0] for pref in preferences if pref[0]]

def set_user_preferences(db: Session, user_preferences: UserPreferences) -> List[str]:
    """Kullanıcının tercihlerini güncelle"""
    # Önce mevcut tercihleri sil
    db.query(UserPref).filter(UserPref.user_id == user_preferences.user_id).delete()
    
    # Yeni tercihleri ekle
    for pref_name in user_preferences.preferences:
        # Tercih var mı kontrol et
        preference = db.query(Preference).filter(Preference.pref_name == pref_name).first()
        if not preference:
            # Tercih yoksa oluştur
            preference = Preference(pref_name=pref_name)
            db.add(preference)
            db.flush()  # ID'yi almak için flush
        
        # Kullanıcı tercihini ekle
        user_pref = UserPref(
            user_id=user_preferences.user_id,
            pref_id=preference.pref_id
        )
        db.add(user_pref)
    
    db.commit()
    return user_preferences.preferences 