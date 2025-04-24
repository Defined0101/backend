from functools import lru_cache
from app.core.config import settings, Settings
from app.services.qdrant_service import QdrantService

# Cache the Qdrant client instance to avoid reconnecting on every request
@lru_cache()
def get_qdrant_service() -> QdrantService:
    """
    Dependency function to get an instance of QdrantService.
    Uses lru_cache to return the same instance for subsequent calls.
    """
    return QdrantService(config=settings) 