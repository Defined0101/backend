# app/tasks/update_embeddings.py

from app.celery_app import celery_app
from app.services.qdrant_service import QdrantService
from app.core.database import SessionLocal
from sqlalchemy import text
from app.core.config import Settings
from app.services import recipe_service
from app.utils.embedding_tracker import get_users_to_update, clear_user_from_update
import logging

logger = logging.getLogger(__name__)

settings = Settings()
qdrant = QdrantService(settings)

@celery_app.task
def update_recent_users_embeddings():
    """
    Celery task to update embeddings for users who updated likes/dislikes in the last 3 minutes.
    """
    db = None
    try:
        db = SessionLocal()

        # Query recently changed users (user_id is string)
        sql = text("""
            SELECT DISTINCT user_id FROM (
                SELECT user_id FROM liked_recipes WHERE updated_at >= NOW() - INTERVAL '3 minutes'
                UNION
                SELECT user_id FROM disliked_recipes WHERE updated_at >= NOW() - INTERVAL '3 minutes'
            ) AS recent_users
        """)

        result = db.execute(sql)
        # Keep user_ids as strings, as they are in the DB
        recent_user_ids = [row[0] for row in result.fetchall()]
        redis_user_ids = get_users_to_update()
        user_ids = list(set(recent_user_ids + redis_user_ids))

        logger.info(f"Found {len(user_ids)} users with recent changes.")

        for user_id in user_ids:
            # Get liked and disliked recipe IDs from your service
            liked_recipes = recipe_service.get_user_liked_recipes_ids(db, user_id)
            disliked_recipes = recipe_service.get_user_disliked_recipes_ids(db, user_id)

            # Delete old embedding first to ensure freshness
            qdrant.delete_user_embedding(user_id)

            # Recalculate and insert the new embedding
            qdrant.upsert_user(user_id=user_id, liked=liked_recipes, disliked=disliked_recipes)
            clear_user_from_update(user_id)
            logger.info(f"Updated embedding for user {user_id}")

    except Exception as e:
        logger.exception(f"Error in update_recent_users_embeddings: {e}")