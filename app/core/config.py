import os
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # Database configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@frs.cxnifrcwbgqm.eu-north-1.rds.amazonaws.com/FRS"
    )
    
    # Qdrant configuration
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    # Allowed collections as comma-separated list
    QDRANT_COLLECTIONS: List[str] = os.getenv("QDRANT_COLLECTIONS", "user_embeddings,text_embeddings").split(",")
    QDRANT_VECTOR_SIZE: int = int(os.getenv("QDRANT_VECTOR_SIZE", 4096))
    
    # API configuration
    API_PREFIX: str = "/api"
    API_VERSION: str = "v1"
    
    # CORS configuration
    CORS_ORIGINS: list = ["*"]
    
    # Other configuration
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create settings instance
settings = Settings() 