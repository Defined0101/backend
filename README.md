# Food Recommendation System API

This repository contains the backend implementation of a Food Recommendation System, developed as a graduation project. The system is built using FastAPI framework and PostgreSQL database to provide personalized recipe recommendations based on user preferences.

## Features

- Basic user management and authentication
- Comprehensive recipe details and recommendations
- Ingredient and allergy management
- User preferences and dietary restrictions
- Advanced recipe search and filtering
- Personalized recipe recommendations

## Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (Amazon RDS)
- **ORM**: SQLAlchemy
- **Documentation**: Swagger/OpenAPI

## Project Structure

```
app/
├── api/
│   ├── endpoints/
│   │   ├── ingredients.py
│   │   ├── recipes.py
│   │   └── users.py
│   └── api.py
├── core/
│   ├── config.py
│   └── database.py
├── models/
│   └── models.py
├── schemas/
│   ├── ingredient_schema.py
│   ├── preference_schema.py
│   ├── recipe_schema.py
│   └── user_schema.py
├── services/
│   ├── ingredient_service.py
│   ├── preference_service.py
│   ├── recipe_service.py
│   └── user_service.py
└── main.py
```

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
```env
DATABASE_URL=postgresql://username:password@host:port/dbname
```

5. Start the application:
```bash
uvicorn app.main:app --reload
```

## API Documentation

The API documentation is available through Swagger UI at:
```
http://localhost:8000/docs
```

### API Endpoints

#### User Management
- `GET /api/v1/users` - Get all users
- `POST /api/v1/users` - Create a new user
- `GET /api/v1/users/{user_id}` - Get user by ID
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user

#### Recipe Management
- `GET /api/v1/getRecipeDetails/{recipe_id}` - Get detailed recipe information
- `GET /api/v1/getRecipeCard/{recipe_id}` - Get recipe card with specified fields

#### Ingredient Management
- `GET /api/v1/getIngredients` - Get all available ingredients
- `GET /api/v1/getUserIngredients` - Get user's ingredients
- `POST /api/v1/setUserIngredients` - Update user's ingredients

#### Allergy Management
- `GET /api/v1/getAllergies` - Get all possible allergies
- `GET /api/v1/getUserAllergies` - Get user's allergies
- `POST /api/v1/setUserAllergies` - Update user's allergies

#### Preferences & Categories
- `GET /api/v1/getCategories` - Get all recipe categories
- `GET /api/v1/getPreferences` - Get all dietary preferences
- `GET /api/v1/getUserPreferences` - Get user's preferences
- `POST /api/v1/setUserPreferences` - Update user's preferences

## Database Schema

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
- `ingr_id` (integer)
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

The API implements comprehensive error handling with appropriate HTTP status codes:

- `400 Bad Request` - Invalid request payload
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server-side errors

## Security Features

- Input validation using Pydantic models
- Database query parameterization
- CORS middleware configuration
- Environment variable configuration

## Future Enhancements

- Firebase Authentication integration
- Enhanced recipe recommendation algorithms
- User activity tracking
- Social features (sharing recipes, following users)
- Mobile application integration
- Real-time notifications
- Recipe rating and review system
- Advanced search filters
- Recipe collections and meal planning

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.