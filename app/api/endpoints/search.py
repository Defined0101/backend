from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
import logging

from app.models.search import RecipeSearch
from app.services.qdrant_service import QdrantService
from app.core.dependencies import get_qdrant_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Define a default value for missing sortable fields
DEFAULT_SORT_VALUE = ""

@router.post("/searchRecipe", response_model=List[dict]) # Endpoint path is /searchRecipe
def search_recipe_endpoint(
    search_params: RecipeSearch,
    qdrant_service: QdrantService = Depends(get_qdrant_service)
):
    """
    Searches recipes based on keywords (inputText), filters by categories and labels,
    and sorts the results according to sortByField and sortByDirection.
    Accessible via /api/v1/recipes/searchRecipe
    """
    try:
        # Initial search using keywords from Qdrant
        initial_results = qdrant_service.search_recipes_by_keywords(
            input_text=search_params.query.inputText,
            limit=50 # Fetch more results initially to allow for backend filtering
        )

        filtered_results = []
        for recipe in initial_results:
            # Category filtering (Case-insensitive)
            if search_params.query.categories:
                recipe_category = recipe.get('category', '') # Get recipe category or default to empty string
                # Check if the recipe's category matches any of the requested categories
                if not isinstance(recipe_category, str) or recipe_category.lower() not in [cat.lower() for cat in search_params.query.categories]:
                    continue # Skip if category doesn't match

            # Label filtering (All requested labels must be present, case-insensitive)
            if search_params.query.labels:
                recipe_labels = recipe.get('label') # Get recipe labels (can be list or string)
                # Normalize recipe_labels to a list of lower-case strings
                if isinstance(recipe_labels, str):
                    recipe_labels_set = {recipe_labels.lower()}
                elif isinstance(recipe_labels, list):
                    recipe_labels_set = {str(label).lower() for label in recipe_labels}
                else:
                    recipe_labels_set = set() # No labels if not string or list

                # Normalize query labels to a set of lower-case strings
                query_labels_set = {label.lower() for label in search_params.query.labels}

                # Check if all query labels are a subset of recipe labels
                if not query_labels_set.issubset(recipe_labels_set):
                    continue # Skip if not all query labels are present in the recipe's labels

            filtered_results.append(recipe)

        # Sorting
        sort_field = search_params.sortByField if search_params.sortByField else "name"
        reverse_sort = search_params.sortByDirection == "descending"

        # Define a robust sorting key function
        def sort_key(item):
            value = item.get(sort_field, DEFAULT_SORT_VALUE)
            # Prioritize numeric types for sorting if applicable
            if isinstance(value, (int, float)):
                return (0, value) # Tuple prioritizes numeric types
            elif isinstance(value, str):
                return (1, value.lower()) # Case-insensitive sort for strings
            else:
                return (2, DEFAULT_SORT_VALUE) # Fallback for other types

        try:
            sorted_results = sorted(
                filtered_results,
                key=sort_key,
                reverse=reverse_sort
            )
        except Exception as e:
            logger.error(f"Error during sorting: {e}. Field: {sort_field}")
            # Fallback to unsorted results if sorting fails
            sorted_results = filtered_results

        # Optional: Apply a final limit to the number of results returned
        # final_limit = 10
        # return sorted_results[:final_limit]
        return sorted_results

    except Exception as e:
        logger.error(f"Error in recipe search endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during the recipe search."
        ) 