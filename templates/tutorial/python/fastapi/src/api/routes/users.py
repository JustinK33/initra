"""User management routes for FastAPI application.

FastAPI automatically handles:
- Request body validation (using Pydantic models)
- Response serialization (converting Python to JSON)
- OpenAPI/Swagger documentation
"""
from fastapi import APIRouter, HTTPException

from src.core.config import settings


router = APIRouter(tags=["users"])

# In-memory storage (in a real app, use a database)
users_db: list[dict] = []
next_id = 1


@router.get("/users")
def list_users() -> dict[str, list]:
    """GET /users - Retrieve all users.

    The -> dict[str, list] is a type hint that FastAPI uses for:
    1. Validating the response matches this shape
    2. Generating OpenAPI documentation
    """
    return {"users": users_db}


@router.get("/users/{user_id}")
def get_user(user_id: int) -> dict:
    """GET /users/:id - Get a specific user by ID.

    FastAPI automatically converts the path parameter to int.
    If it can't convert (e.g., /users/abc), it returns a 422 error.
    """
    for user in users_db:
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")
    # HTTPException is FastAPI's way to return error responses


@router.post("/users")
def create_user(name: str) -> dict:
    """POST /users - Create a new user.

    The 'name: str' parameter comes from the request body or query string.
    FastAPI validates the type and returns 422 if invalid.
    """
    global next_id
    user = {"id": next_id, "name": name}
    users_db.append(user)
    next_id += 1
    return user