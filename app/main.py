from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import home, user, recipe, vector
import logging
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app with more detailed documentation
app = FastAPI(
    title="Food Recommendation System API",
    description="""
    This API provides endpoints for a Food Recommendation System backend.
    
    ## Features
    
    * **Users**: Create and manage user accounts
    * **Recipes**: Search, retrieve and filter recipes
    * **Preferences**: Set and get user dietary preferences
    * **Ingredients**: Manage user's ingredients and allergies
    * **Recommendations**: Get personalized recipe recommendations
    * **Vector Search**: Semantic search for recipes using vector embeddings
    
    ## Authentication
    
    Currently, the API does not require authentication. User identification is done through user_id parameters.
    
    ## How to use the API
    
    Use the interactive documentation below to test and understand the available endpoints.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "Development Team",
        "email": "your.email@example.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup graceful shutdown handlers
def handle_sigterm(*args):
    """Handle SIGTERM signal to gracefully shut down the application"""
    logger.info("SIGTERM received - shutting down gracefully")
    sys.exit(0)

def handle_sigint(*args):
    """Handle SIGINT signal (Ctrl+C) to gracefully shut down the application"""
    logger.info("SIGINT received - shutting down gracefully")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigint)

# Include routers
app.include_router(home.router, tags=["Home"])
app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(recipe.router, tags=["Recipes and Recommendations"])
app.include_router(vector.router, tags=["Vector Search"])

@app.on_event("startup")
async def startup_event():
    """Actions to perform on application startup"""
    logger.info("Food Recommendation System API starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    """Actions to perform on application shutdown"""
    logger.info("Food Recommendation System API shutting down...") 