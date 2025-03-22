from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.vector_service import vector_service
from app.services.recipe_service import get_recipe_details
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

router = APIRouter()

class VectorPayload(BaseModel):
    recipe_id: str
    vector: List[float]
    metadata: Optional[Dict[str, Any]] = None

class QueryVector(BaseModel):
    vector: List[float]
    limit: Optional[int] = 10

@router.post("/vector/store", 
           summary="Store a recipe vector",
           description="Stores a recipe vector embedding in the vector database",
           response_description="Success status")
def store_vector(payload: VectorPayload):
    """
    Store a recipe vector embedding.
    
    This endpoint allows storing vector embeddings for recipes in the vector database.
    The vector can be generated from recipe text using an embedding model.
    
    The payload should include:
    - recipe_id: The ID of the recipe
    - vector: The vector embedding (list of floats)
    - metadata: Optional additional data to store with the vector
    """
    # Prepare the payload
    recipe_payload = payload.metadata or {}
    
    # Store the vector
    success = vector_service.store_recipe_vector(
        recipe_id=payload.recipe_id,
        vector=payload.vector,
        payload=recipe_payload
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to store vector")
    
    return {"message": "Vector stored successfully"}

@router.delete("/vector/{recipe_id}", 
           summary="Delete a recipe vector",
           description="Deletes a recipe vector from the vector database",
           response_description="Success status")
def delete_vector(recipe_id: str):
    """
    Delete a recipe vector.
    
    This endpoint removes a recipe vector from the vector database based on the recipe ID.
    """
    success = vector_service.delete_recipe_vector(recipe_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete vector")
    
    return {"message": "Vector deleted successfully"}

@router.post("/vector/search", 
           summary="Search similar recipes by vector",
           description="Searches for recipes similar to the provided vector embedding",
           response_description="List of similar recipes with similarity scores")
def search_similar(query: QueryVector):
    """
    Search for recipes similar to the provided vector embedding.
    
    This endpoint takes a vector embedding and returns recipes with similar embeddings.
    The results are sorted by similarity score (highest first).
    
    The payload should include:
    - vector: The query vector embedding (list of floats)
    - limit: Maximum number of results to return (default: 10)
    """
    results = vector_service.search_similar_recipes(
        query_vector=query.vector,
        limit=query.limit
    )
    
    return results

@router.get("/vector/recommend/{recipe_id}", 
           summary="Get recipe recommendations",
           description="Returns recipes similar to the specified recipe",
           response_description="List of similar recipes")
def get_recommendations(recipe_id: str, limit: int = Query(10, description="Maximum number of recommendations"), db: Session = Depends(get_db)):
    """
    Get recipe recommendations based on a specific recipe.
    
    This endpoint retrieves the vector for the specified recipe and then finds similar recipes.
    It combines vector similarity search with database details to provide comprehensive recommendations.
    """
    # Get the vector for the recipe
    recipe_vector = vector_service.get_recipe_vector(recipe_id)
    
    if not recipe_vector:
        raise HTTPException(status_code=404, detail="Recipe vector not found")
    
    # Find similar recipes
    similar_recipes = vector_service.search_similar_recipes(
        query_vector=recipe_vector,
        limit=limit + 1  # Add 1 to exclude the query recipe itself
    )
    
    # Filter out the query recipe if present
    recommendations = [recipe for recipe in similar_recipes if str(recipe.get("recipe_id")) != recipe_id]
    
    # Limit to the requested number
    recommendations = recommendations[:limit]
    
    # Fetch full details for each recommended recipe
    detailed_recommendations = []
    for recommendation in recommendations:
        recipe_detail = get_recipe_details(db, int(recommendation.get("recipe_id")))
        if recipe_detail:
            # Add the similarity score to the recipe details
            recipe_detail["similarity_score"] = recommendation.get("score")
            detailed_recommendations.append(recipe_detail)
    
    return detailed_recommendations 