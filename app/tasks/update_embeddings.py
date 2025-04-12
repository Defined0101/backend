# app/tasks/update_embeddings.py

from app.celery_app import celery_app
from app.services.qdrant_service import QdrantService
from app.services.user_service import UserService
from app.database import get_db_session
from sqlalchemy import text
from config import Settings
import logging

logger = logging.getLogger(__name__)

settings = Settings()
qdrant = QdrantService(settings)
user_service = UserService(settings)

@celery_app.task
def update_recent_users_embeddings():
    """
    Celery task to update embeddings for users who updated likes/dislikes in the last 5 minutes.
    """
    try:
        db = get_db_session()

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
            liked = user_service.get_liked_recipes(db, user_id)
            disliked = user_service.get_disliked_recipes(db, user_id)
            qdrant.delete_user_embedding(user_id)
            qdrant.upsert_user(user_id, liked, disliked)
            logger.info(f"Updated embedding for user {user_id}")

    except Exception as e:
        logger.error(f"Embedding update failed: {e}")
