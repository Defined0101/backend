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

        # Query recently changed users (user_id is string)
        sql = text("""
            SELECT DISTINCT user_id FROM (
                SELECT user_id FROM liked_recipes WHERE updated_at >= NOW() - INTERVAL '5 minutes'
                UNION
                SELECT user_id FROM disliked_recipes WHERE updated_at >= NOW() - INTERVAL '5 minutes'
            ) AS recent_users
        """)

        result = db.execute(sql)
        # Keep user_ids as strings, as they are in the DB
        user_ids = [row[0] for row in result.fetchall()]

        logger.info(f"Found {len(user_ids)} users with recent changes.")

        for user_id_str in user_ids: # Rename variable for clarity
            # Keep user_id as string for DB queries
            
            # Convert to int ONLY for Qdrant operations and logging check
            try:
                user_id_int = int(user_id_str) 
            except ValueError:
                logger.error(f"Could not convert user_id '{user_id_str}' to int. Skipping.")
                continue

            # Log before update for user_id 1 (checking integer version)
            if user_id_int == 1:
                try:
                    embedding_before = qdrant.get_user_embedding(user_id_int) 
                    logger.info(f"User ID 1 (str: {user_id_str}): Embedding before update: {embedding_before}")
                except Exception as e:
                    logger.error(f"User ID 1 (str: {user_id_str}): Failed to get embedding before update: {e}")

            # Use string user_id for DB queries with standard parameters, but cast parameter to text
            liked_results = db.execute(
                text("SELECT recipe_id FROM liked_recipes WHERE user_id = :uid::text"),
                {"uid": user_id_str} 
            ).all()
            liked_ids = [row[0] for row in liked_results]
            
            # Use string user_id for DB queries with standard parameters, but cast parameter to text
            disliked_results = db.execute(
                text("SELECT recipe_id FROM disliked_recipes WHERE user_id = :uid::text"),
                {"uid": user_id_str}
            ).all()
            disliked_ids = [int(row[0]) for row in disliked_results] # recipe_id is likely int
            
            # Use integer user_id for Qdrant operations
            qdrant.delete_user_embedding(user_id_int)
            qdrant.upsert_user(user_id_int, liked_ids, disliked_ids)
            logger.info(f"Updated embedding for user {user_id_str} (int: {user_id_int})")

            # Log after update for user_id 1 (checking integer version)
            if user_id_int == 1:
                try:
                    embedding_after = qdrant.get_user_embedding(user_id_int) 
                    logger.info(f"User ID 1 (str: {user_id_str}): Embedding after update: {embedding_after}")
                except Exception as e:
                    logger.error(f"User ID 1 (str: {user_id_str}): Failed to get embedding after update: {e}")

    except Exception as e:
        # Log the exception with the correct user_id context if possible
        user_id_context = user_id_str if 'user_id_str' in locals() else 'unknown'
        logger.exception(f"Embedding update failed (current user context: {user_id_context}): {e}")
    finally:
        if db is not None:
            db.close()
