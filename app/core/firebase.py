import firebase_admin
from firebase_admin import credentials, auth
from app.core.config import settings

# Firebase Admin SDK'yı başlat
cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(cred)

def verify_firebase_token(token: str) -> dict:
    """
    Firebase ID token'ını doğrula ve kullanıcı bilgilerini döndür
    """
    try:
        decoded_token = auth.verify_id_token(token)
        return {
            "uid": decoded_token["uid"],
            "email": decoded_token.get("email"),
            "name": decoded_token.get("name"),
            "picture": decoded_token.get("picture")
        }
    except Exception as e:
        raise Exception(f"Invalid token: {str(e)}") 