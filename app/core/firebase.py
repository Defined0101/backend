import firebase_admin
from firebase_admin import credentials, auth
from app.core.config import settings
import os

# Firebase credentials dosyasının yolu
cred_path = os.path.join(os.path.dirname(__file__), "firebase-credentials.json")

# Firebase Admin SDK'yı başlat
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

def verify_firebase_token(token: str) -> dict:
    """
    Firebase ID token'ı doğrula
    """
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise Exception(f"Invalid token: {str(e)}")

def create_custom_token(uid: str) -> str:
    """
    Firebase Custom Token oluştur
    """
    try:
        custom_token = auth.create_custom_token(uid)
        return custom_token.decode('utf-8')
    except Exception as e:
        raise Exception(f"Failed to create custom token: {str(e)}") 