# app/tasks/update_embeddings.py

from app.celery_app import celery_app
from app.services.qdrant_service import QdrantService
# Artık kullanılmadığı için UserService importunu ve global instance'ı kaldır
# from app.services.user_service import UserService 
from app.core.database import SessionLocal
from sqlalchemy import text
from app.core.config import Settings
import logging

logger = logging.getLogger(__name__)

settings = Settings()
qdrant = QdrantService(settings)
# user_service = UserService(settings) # <<< KALDIRILDI

@celery_app.task
def update_recent_users_embeddings():
    """
    Celery task to update embeddings for users who updated likes/dislikes in the last 5 minutes.
    """
    db = None
    try:
        db = SessionLocal()

        # Query recently changed users
        sql = text("""
            SELECT DISTINCT user_id FROM (
                SELECT user_id FROM liked_recipes WHERE updated_at >= NOW() - INTERVAL '5 minutes'
                UNION
                SELECT user_id FROM disliked_recipes WHERE updated_at >= NOW() - INTERVAL '5 minutes'
            ) AS recent_users
        """)

        result = db.execute(sql)
        user_ids = [row[0] for row in result.fetchall()]

        logger.info(f"Found {len(user_ids)} users with recent changes.")

        for user_id in user_ids:
            liked_results = db.query(text("SELECT recipe_id FROM liked_recipes WHERE user_id=:uid")).params(uid=user_id).all()
            liked_ids = [row[0] for row in liked_results]
            
            disliked_results = db.query(text("SELECT recipe_id FROM disliked_recipes WHERE user_id=:uid")).params(uid=user_id).all()
            disliked_ids = [int(row[0]) for row in disliked_results]
            
            user_id_int = int(user_id)
            
            qdrant.delete_user_embedding(user_id_int)
            qdrant.upsert_user(user_id_int, liked_ids, disliked_ids)
            logger.info(f"Updated embedding for user {user_id}")

    except Exception as e:
        logger.exception(f"Embedding update failed for some users: {e}")
    finally:
        if db is not None:
            db.close()
