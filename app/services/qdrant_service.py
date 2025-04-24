# app/services/qdrant_service.py
from typing import List, Optional
import qdrant_client
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter as HttpFilter, MinShould
from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
    VectorParams,
    PointStruct,
)
import logging
from qdrant_client.http.models import VectorParams, PointStruct
import qdrant_client.models
from app.core.config import Settings
import torch
import os
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QdrantService:
    def __init__(self, config:Settings):
        self.config = config
        self.client = self._init_qdrant()
        self.vector_size = self.config.QDRANT_VECTOR_SIZE
        self.user_collection = self.config.QDRANT_COLLECTIONS[0]
        self.recipe_collection = self.config.QDRANT_COLLECTIONS[1]
        
    
    def _init_qdrant(self) -> QdrantClient:
        
        host       = os.getenv("QDRANT_HOST", "localhost")
        port       = int(os.getenv("QDRANT_PORT", 6333))
        grpc_port  = int(os.getenv("QDRANT_GRPC_PORT", 6334))
        prefer_grpc = os.getenv("PREFER_GRPC", "false").lower() in ("1","true","yes")
        timeout    = int(os.getenv("QDRANT_TIMEOUT", 300))

        # HTTP URL’i hazırlıyoruz
        url = f"http://{host}:{port}"

        logging.info(f"Initializing QdrantClient → url={url}, grpc_port={grpc_port}, prefer_grpc={prefer_grpc}")

        return QdrantClient(
            url=url,
            grpc_port=grpc_port,
            prefer_grpc=prefer_grpc,
            timeout=timeout
        )

    def _ensure_collection(self, collection_name: str) -> bool:
        existing_collections = [c.name for c in self.client.get_collections().collections]
        if collection_name not in existing_collections:
            return False
        else:
            return True

    # Get recipe embedding from the collection
    def get_recipe_embedding(self, recipe_id: int) -> Optional[List[float]]:
        if self._ensure_collection(self.recipe_collection) == False:
            return "No collection found"
        
        """
        Retrieves embedding vector for given recipe ID from Qdrant.
        Returns None if recipe or vector not found.
        """
        try:
            point = self.client.retrieve(
                collection_name = self.recipe_collection,
                ids=[recipe_id],
                with_vectors=True
            )
            if point and point[0].vector:
                return point[0].vector
            return None
        except Exception as e:
            return None
    
    # Get user embedding from the collection    
    def get_user_embedding(self, user_id: int) -> Optional[List[float]]:
        if self._ensure_collection(self.user_collection) == False:
            return "No collection found"
        
        """
        Retrieves embedding vector for given recipe ID from Qdrant.
        Returns None if recipe or vector not found.
        """
        try:
            point = self.client.retrieve(
                collection_name = self.user_collection,
                ids=[user_id],
                with_vectors=True
            )
            if point and point[0].vector:
                return point[0].vector
            return None
        except Exception as e:
            return None

    # Calculate user embedding based on liked and disliked recipes
    def calculate_user_embeddings(
        self, liked: list[int]=None, disliked: list[int]=None
    ) -> Optional[List[float]]:
        self._ensure_collection(self.user_collection)
        
        liked_embedding = []
        if liked:
            for recipe_id in liked:
                liked_vector = self.get_recipe_embedding(recipe_id)
                if liked_vector is not None:
                    liked_embedding.append(liked_vector)

        disliked_embedding = []
        if disliked:
            for recipe_id in disliked:
                disliked_vector = self.get_recipe_embedding(recipe_id)
                if disliked_vector is not None:
                    disliked_embedding.append(disliked_vector)
        
        if not liked_embedding and not disliked_embedding:
            return None

        liked_tensor = torch.tensor(liked_embedding).mean(dim=0) if liked_embedding else torch.zeros(self.vector_size)
        disliked_tensor = torch.tensor(disliked_embedding).mean(dim=0) if disliked_embedding else torch.zeros(self.vector_size)

        user_vector = (liked_tensor - disliked_tensor).numpy().tolist()
        return user_vector
    
    def delete_user_embedding(self, user_id: str) -> dict:
        """
        Deletes a user embedding from the user collection in Qdrant.
        """
        if not self._ensure_collection(self.user_collection):
            return {"status": "error", "message": "User collection does not exist."}

        try:
            self.client.delete(
                self.user_collection,     # 1. arg. → collection_name
                [int(user_id)],           # 2. arg. → points_selector (ID listesi)
                wait=True
            )
            return {"status": "deleted", "collection": self.user_collection, "id": user_id}
        except Exception as e:
            logger.error(f"Error deleting user embedding for user {user_id}: {e}")
            return {"status": "error", "message": str(e)}

    def upsert_user(self, user_id: str, liked: list[int] = None, disliked: list[int] = None) -> dict:
        user_vector = self.calculate_user_embeddings(liked, disliked)
        if not user_vector:
            user_vector = [0.0] * self.vector_size

        if not self._ensure_collection(self.user_collection):
            self.client.create_collection(
                collection_name=self.user_collection,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance="Cosine"
                )
            )

        point = PointStruct(
            id=int(user_id),
            vector=user_vector,
            payload={
                "user_id": int(user_id),
                "liked_recipes": liked or [],
                "disliked_recipes": disliked or []
            }
        )

        self.client.upsert(
            collection_name=self.user_collection,
            points=[point],
            wait=True
        )

        return {"status": "inserted", "collection": self.user_collection, "id": user_id}


    # Search for recipes based on various filters
    def search_recipes(
        self,
        query_vec_param: Optional[List[float]] = None,
        query: Optional[int] = None,
        ingredients: Optional[List[str]] = None,
        query_type: Optional[str] = "none",  # It can be "exact", "partial" or "none".
        labels: Optional[List[str]] = None,
        category: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.0,
        upper_threshold: Optional[float] = None,
    ) -> List[dict]:
        try:
            filters = self._create_filters(
                ingredients=ingredients,
                query_type=query_type,
                labels=labels,
                category=category
            )
            query_vector = self.get_recipe_embedding(query) if query else None
            
            if not query_vector:
                query_vector = query_vec_param

            if query_vector:
                search_response = self.client.query_points(
                    collection_name=self.recipe_collection,
                    query=query_vector,
                    query_filter=filters,
                    limit=limit,
                    with_payload=True,
                )

                return self._process_search_results(
                    search_response.points, similarity_threshold, upper_threshold
                )
            else:
                search_response = self.client.scroll(
                    collection_name=self.recipe_collection,
                    scroll_filter=filters,
                    limit=limit,
                    with_payload=True,
                )
                return self._process_scroll_results(search_response[0])

        except Exception as e:
            logger.error(f"Search error: {e}")
            raise

    def _create_filters(
        self,
        ingredients: Optional[List[str]] = None,
        query_type: str = "none",
        labels: Optional[List[str]] = None,
        category: Optional[str] = None,
    ) -> Filter:
        conditions = []

        # Ingredients filter
        if ingredients:
            if query_type == "exact":
                # For exact match, first the IngredientsCount field in the payload should be equal to the length of the given ingredients list.
                conditions.append(
                    FieldCondition(key="IngredientsCount", match=MatchValue(value=len(ingredients)))
                )
                # Then, each ingredient must match exactly.
                conditions.extend(
                    [FieldCondition(key="Ingredients", match=MatchValue(value=ing)) for ing in ingredients]
                )
            elif query_type == "partial":
                # For partial match, any of the given ingredients can match.
                conditions.extend(
                    [FieldCondition(key="Ingredients", match=MatchValue(value=ing)) for ing in ingredients]
                )
            # If query_type is "none", no ingredient filter is added.

        # Labels filter: each label must match exactly (must contain all elements).
        if labels:
            conditions.extend(
                [FieldCondition(key="Label", match=MatchValue(value=label)) for label in labels]
            )

        # For Category, direct exact match
        if category:
            conditions.append(
                FieldCondition(key="Category", match=MatchValue(value=category))
            )

        return Filter(must=conditions)

    # Process search results for similarity checked filter results
    def _process_search_results(
        self,
        points: List[qdrant_client.models.ScoredPoint],
        similarity_threshold: float,
        upper_threshold: Optional[float],
    ) -> List[dict]:
        results = []
        for point in points:
            if (
                similarity_threshold is not None
                and point.score < similarity_threshold
                or upper_threshold is not None
                and point.score > upper_threshold
            ):
                continue
            try:
                results.append(
                    {
                        "id": point.id,
                        "name": point.payload.get('Name', 'No name available'),
                        "category": point.payload.get('Category', 'No category available'),
                        "label": point.payload.get('Label', 'No label available'),
                        "score": point.score,
                        "ingredients": point.payload.get('Ingredients', 'No ingredient names available'),
                    }
                )
            except Exception as e:
                print(f"The data field(s) is damaged: {e}")
                continue
        return results
    
    # Process scroll results for only filter results. No similarity check
    def _process_scroll_results(
        self,
        points: List[qdrant_client.models.ScrollResult],
    ) -> List[dict]:
        results = []
        for point in points:
            try:
                results.append(
                    {
                        "name": point.payload.get("Name", "No name available"),
                        "category": point.payload.get("Category", "No category available"),
                        "label": point.payload.get("Label", "No label available"),
                        "ingredients": point.payload.get("Ingredients", "No ingredient names available"),
                    }
                )
            except Exception as e:
                logger.error(f"The data field(s) is damaged: {e}")
                continue
        return results
    
    # This search for similar users.
    def _find_similar_users(
        self, user_id: int, top_n: Optional[int] = 3, threshold: Optional[float] = -1.0
    ) -> Optional[List[tuple]]:
        """
        Find similar users for given user id.
        """
        user_embedding = self.get_user_embedding(user_id=user_id)
        search_response = self.client.query_points(
            collection_name=self.user_collection,
            query=user_embedding,
            limit=top_n,
            with_payload=True,
            score_threshold=threshold,
        )
        similar_users = [(hit.payload["user_id"], hit.score) 
                        for hit in search_response.points 
                        if hit.payload["user_id"] != user_id]
        
        if similar_users:
            return similar_users
        
        return None
    
    # It returns liked and disliked recipes.
    def _get_liked_disliked_recipes(self, user_id: int) -> Optional[dict]:
        response = self.client.scroll(
            collection_name=self.user_collection,
            scroll_filter=Filter(
                                    must=[
                                        FieldCondition(key="user_id", match=MatchValue(value=user_id))
                                    ]
                                ),
            with_vectors=True,
            with_payload=True,
        )
        
        liked_list = []
        disliked_list = []
        
        for point in response[0]:
            liked_list = point.payload.get("liked_recipes", "No Liked Recipes Avaliable")
            disliked_list = point.payload.get("disliked_recipes", "No Disliked Recipes Avaliable")
        return {
            "Liked": liked_list,
            "Disliked": disliked_list
        }
    
    def recommend_recipe(
        self, 
        user_id: int,
        ingredients: Optional[List[str]] = None,
        query_type: str = "none",  # It can be "exact", "partial" or "none".
        labels: Optional[List[str]] = None,
        category: Optional[str] = None, 
        limit: int = 3) -> List[dict]:
        
        """
        Suggests a recipe to the user.
        1. If there is a similar user(s), first a large list of candidates is drawn with that user's embedding.
        The scores of the candidate recipes are then adjusted according to the likes and dislikes of similar users.
        2. If there are no similar users, the candidates are queried directly with the user's embedding.
        Each suggestion is returned as a dictionary with recipe information.
        """

        # Step 1: Find similar users.
        similar_users = self._find_similar_users(user_id=user_id)

        # Step 2: Get user embedding.
        user_vector = self.get_user_embedding(user_id=user_id)
        
        if not user_vector:
            return []

        # Search candidate recipes with user embedding, inventory and preferences.
        candidate_limit = limit * 10
        candidate_recipes = []
        try:
            candidate_recipes = self.search_recipes(
                ingredients=ingredients, 
                query_type=query_type,
                labels=labels,
                category=category,
                query_vec_param=user_vector,
                limit=candidate_limit 
                )
    
        except Exception as e:
            return []

        # Adjust recipe scores with similar users.
        if similar_users:
            for recipe in candidate_recipes:
                recipe_id = recipe["id"]
                adjusted_score = recipe["score"]
                for similar_user_id, similarity_score in similar_users:
                    similar_interactions = self._get_liked_disliked_recipes(similar_user_id)
                    if similar_interactions:
                        liked_recipes = similar_interactions.get("Liked")
                        disliked_recipes = similar_interactions.get("Disliked")
                        if liked_recipes and isinstance(liked_recipes, list) and recipe_id in liked_recipes:
                            adjusted_score += similarity_score
                        if disliked_recipes and isinstance(disliked_recipes, list) and recipe_id in disliked_recipes:
                            adjusted_score -= similarity_score
                recipe["final_score"] = adjusted_score
            # Sort recipes according to their scores.
            candidate_recipes.sort(key=lambda x: x["final_score"], reverse=True)
        else:
            # If similar user is not found, we use base score according to user embedding query.
            candidate_recipes.sort(key=lambda x: x["score"], reverse=True)

        top_recipes = candidate_recipes[:limit]
        return top_recipes

    # This is to be used by search bar.
    def search_recipes_by_keywords(
        self,
        input_text: str,
        limit: int = 10
    ) -> List[dict]:
        """
        1) Find recipes whose payload fields contain the full input_text.
        2) Find recipes containing any individual word.
        3) Merge both sets (full-string hits first), dedupe by id, and return up to `limit`.
        """
        text = input_text.strip().lower()
        if not text:
            return []

        # Phase 1: full-string match
        full_conditions = [
            FieldCondition(key=key, match=MatchValue(value=text))
            for key in ["Name", "Category", "Label", "Ingredients"]
        ]
        full_filter = HttpFilter(
            min_should=MinShould(conditions=full_conditions, min_count=1)
        )
        full_scroll = self.client.scroll(
            collection_name=self.recipe_collection,
            scroll_filter=full_filter,
            limit=limit,
            with_payload=True,
        )
        full_hits = full_scroll[0] if full_scroll else []

        # Phase 2: per-word OR search
        words = [w for w in text.split() if w]
        word_conditions = []
        for word in words:
            for key in ["Name", "Category", "Label", "Ingredients"]:
                word_conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=word))
                )
        word_filter = HttpFilter(
            min_should=MinShould(conditions=word_conditions, min_count=1)
        )
        word_scroll = self.client.scroll(
            collection_name=self.recipe_collection,
            scroll_filter=word_filter,
            limit=limit,
            with_payload=True,
        )
        word_hits = word_scroll[0] if word_scroll else []

        # Merge and dedupe by point.id, preserving order (full first)
        seen_ids = set()
        merged = []
        for hit in full_hits + word_hits:
            if hit.id not in seen_ids:
                seen_ids.add(hit.id)
                merged.append(hit)
            if len(merged) >= limit:
                break

        # Process and return as scroll results (no scores)
        return self._process_scroll_results(merged)
    
    #Cleanup resources
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.client.close()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")