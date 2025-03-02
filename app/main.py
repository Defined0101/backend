from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import home, user, recipe

# Create FastAPI app
app = FastAPI(
    title="Food Recommendation API", 
    version="1.0",
    description="API for food recommendation system with PostgreSQL database"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(home.router, tags=["Home"])
app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(recipe.router, tags=["Recipes"])  # No prefix to match the requested endpoint paths 