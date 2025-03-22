from qdrant_client import QdrantClient
from qdrant_client.http import models
import os
from typing import List, Dict, Any, Optional
from app.core.config import settings

class VectorService:
    def __init__(self):
        # Get Qdrant connection details from settings
        host = settings.QDRANT_HOST
        port = settings.QDRANT_PORT
        
        # Initialize Qdrant client
        self.client = QdrantClient(host=host, port=port)
        
        # Collection name for recipe vectors
        self.collection_name = "recipes"
    
    def search_similar_recipes(self, query_vector: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for recipes similar to the given vector embedding
        
        Args:
            query_vector (List[float]): The query vector embedding
            limit (int): Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of similar recipes with similarity scores
        """
        try:
            # Search for similar vectors in the collection
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit
            )
            
            # Extract and return the results
            results = []
            for scored_point in search_result:
                # Combine the payload with the score
                result = {
                    "recipe_id": scored_point.id,
                    "score": scored_point.score,
                    **scored_point.payload
                }
                results.append(result)
                
            return results
        except Exception as e:
            print(f"Error searching similar recipes: {e}")
            return []
    
    def get_recipe_vector(self, recipe_id: str) -> Optional[List[float]]:
        """
        Get the vector embedding for a specific recipe
        
        Args:
            recipe_id (str): The ID of the recipe
            
        Returns:
            Optional[List[float]]: The vector embedding if found, otherwise None
        """
        try:
            # Get the points by IDs
            points = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[recipe_id],
                with_vectors=True
            )
            
            if points and len(points) > 0:
                return points[0].vector
            return None
        except Exception as e:
            print(f"Error getting recipe vector: {e}")
            return None
    
    def store_recipe_vector(self, recipe_id: str, vector: List[float], payload: Dict[str, Any]) -> bool:
        """
        Store a recipe vector embedding in the vector database
        
        Args:
            recipe_id (str): The ID of the recipe
            vector (List[float]): The vector embedding
            payload (Dict[str, Any]): Additional data to store with the vector
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create the collection if it doesn't exist
            self._ensure_collection_exists()
            
            # Store the vector
            operation_info = self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=recipe_id,
                        vector=vector,
                        payload=payload
                    )
                ]
            )
            
            return operation_info.status == "completed"
        except Exception as e:
            print(f"Error storing recipe vector: {e}")
            return False
    
    def delete_recipe_vector(self, recipe_id: str) -> bool:
        """
        Delete a recipe vector from the database
        
        Args:
            recipe_id (str): The ID of the recipe to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Delete the vector
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=[recipe_id]
                )
            )
            return True
        except Exception as e:
            print(f"Error deleting recipe vector: {e}")
            return False
    
    def _ensure_collection_exists(self):
        """
        Create the collection if it doesn't exist
        """
        # Check if collection exists
        collections = self.client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if self.collection_name not in collection_names:
            # Create the collection with appropriate parameters
            # Assuming recipe vectors are 384-dimensional (typical for sentence-transformers)
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=384,  # Adjust based on your actual vector dimensions
                    distance=models.Distance.COSINE
                )
            )

# Singleton instance
vector_service = VectorService() 