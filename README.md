# Food Recommendation System API

This repository contains the backend implementation of a Food Recommendation System, developed as a graduation project. The system is built using FastAPI framework and PostgreSQL database to provide personalized recipe recommendations based on user preferences.

## Features

- Comprehensive recipe details retrieval
- Customizable recipe card information
- Category and label management
- User preference tracking and personalization
- Advanced recipe search and filtering capabilities
- Ingredient-based recipe recommendations
- Nutritional information tracking

## Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (Amazon RDS)
- **ORM**: SQLAlchemy
- **Validation**: Pydantic
- **Documentation**: Swagger/OpenAPI

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
Create a `.env` file in the root directory with the following variables:
```
DATABASE_URL=postgresql://username:password@host:port/dbname
```

5. Start the application:
```bash
uvicorn app.main:app --reload
```

## API Documentation

### Interactive Documentation

The API comes with built-in interactive documentation:
```
http://localhost:8000/docs
```

### Endpoints

#### Recipe Management

**Get Recipe Details**
```
GET /getRecipeDetails/{recipe_id}
```
Returns comprehensive information about a specific recipe, including ingredients, nutritional values, and preparation instructions.

**Get Recipe Card**
```
GET /getRecipeCard/{recipe_id}?fields=recipe_name&fields=calories&fields=total_time&fields=ingredients
```
Returns specific fields of a recipe for displaying in a card format. Fields can be customized through query parameters.

#### Category and Label Management

**Get All Categories**
```
GET /getCategories
```
Returns all available recipe categories.

**Get All Labels**
```
GET /getLabels
```
Returns all available dietary preference labels (vegan, gluten-free, etc.).

#### User Preference Management

**Get User Preferences**
```
GET /getUserPreferences/{user_id}
```
Returns the dietary preferences for a specific user.

**Set User Preferences**
```
POST /setUserPreferences
Content-Type: application/json

{
  "user_id": "user123",
  "dairy_free": true,
  "gluten_free": false,
  "pescetarian": false,
  "vegan": false,
  "vegetarian": true
}
```
Updates a user's dietary preferences.

#### Recipe Search and Filtering

**Query Recipes**
```
POST /query
Content-Type: application/json

{
  "query": {
    "name": "chicken",
    "ingredient": ["garlic", "onion"]
  },
  "sortBy": {
    "field": "recipe_name",
    "direction": "asc"
  }
}
```
Searches for recipes based on name and ingredients, with sorting options.

## API Endpoints

### Users
- `GET /api/v1/users` - Get all users
- `POST /api/v1/users` - Create a new user
- `GET /api/v1/users/{user_id}` - Get user by ID
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user

### Ingredients & Preferences
- `GET /api/v1/getIngredients` - Get all ingredients
- `GET /api/v1/getUserIngredients` - Get user's ingredients
- `POST /api/v1/setUserIngredients` - Set user's ingredients
- `GET /api/v1/getAllergies` - Get all allergies
- `GET /api/v1/getUserAllergies` - Get user's allergies
- `POST /api/v1/setUserAllergies` - Set user's allergies
- `GET /api/v1/getCategories` - Get all categories
- `GET /api/v1/getPreferences` - Get all preferences
- `GET /api/v1/getUserPreferences` - Get user's preferences
- `POST /api/v1/setUserPreferences` - Set user's preferences

## Database Schema

The system utilizes a relational database with the following key tables:

- **users**: User account information
- **recipe**: Recipe details including nutritional information
- **ingredient**: Ingredient information
- **recipe_ingr**: Many-to-many relationship between recipes and ingredients
- **category**: Recipe categories
- **preference**: Dietary preference options
- **user_pref**: User-preference relationships
- **saved_recipes**: User-saved recipes
- **liked_recipes**: User-liked recipes
- **allergies**: User-ingredient allergies
- **pref_recipe**: Preference-recipe relationships

### Users Table
- `user_id` (text, primary key)
- `e_mail` (text)
- `user_name` (text)
- `user_bday` (date)
- `tel_no` (bigint)

### Ingredient Table
- `ingr_id` (integer, primary key)
- `ingr_name` (text)

### Inventory Table
- `user_id` (text, foreign key)
- `ingr_id` (text)
- `quantity` (numeric)

### Allergy Table
- `user_id` (text, foreign key)
- `ingr_id` (integer, foreign key)

### Category Table
- `category_id` (integer, primary key)
- `cat_name` (text)

### Preference Table
- `pref_id` (integer, primary key)
- `pref_name` (text)

### User Preferences Table
- `user_id` (text, foreign key)
- `pref_id` (integer, foreign key)

## Error Handling

The API implements comprehensive error handling with appropriate HTTP status codes and descriptive error messages to facilitate debugging and provide a better developer experience.

## Security

- Input validation using Pydantic models
- Database query parameterization to prevent SQL injection
- CORS middleware configuration

## Future Enhancements

- Authentication and authorization
- Recipe recommendation algorithm improvements
- User activity tracking
- Social features (sharing recipes, following users)
- Mobile application integration

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.