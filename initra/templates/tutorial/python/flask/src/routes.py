"""Route handlers for Flask application.

A Blueprint is a way to organize related routes together.
Think of it like a chapter in a book - it groups related pages.
"""
from flask import Blueprint, jsonify, request

from src.config import settings
from src.db import users


# Create a blueprint named 'health' - all routes here start with /health (if prefixed)
health_bp = Blueprint("health", __name__)

# Track the next user ID for creating new users
next_id = 1


@health_bp.get("/")
def health() -> tuple[dict[str, str], int]:
    """Health check endpoint - returns status and environment info."""
    return jsonify(status="ok", project="{{project_name}}", env=settings.env), 200
    # 200 is the HTTP status code for "OK"


@health_bp.get("/users")
def list_users() -> tuple[dict[str, object], int]:
    """GET /users - List all users in the system."""
    return jsonify(users=users), 200


@health_bp.get("/users/<int:user_id>")
def get_user(user_id: int) -> tuple[dict[str, object], int]:
    """GET /users/:id - Get a specific user by ID.

    The <int:user_id> part tells Flask to:
    1. Match URLs like /users/1, /users/42
    2. Convert the ID to an integer
    3. Pass it to the function as user_id
    """
    for user in users:
        if user["id"] == user_id:
            return jsonify(user), 200
    return jsonify(error="User not found"), 404
    # 404 is "Not Found" - the user doesn't exist


@health_bp.post("/users")
def create_user() -> tuple[dict[str, object], int]:
    """POST /users - Create a new user.

    request.get_json() extracts JSON data from the request body.
    Example: {"name": "Alice", "email": "alice@example.com"} becomes that dict
    """
    global next_id
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip()

    # Simple validation
    if len(name) < 2 or "@" not in email:
        return jsonify(error="Invalid name or email"), 400
        # 400 is "Bad Request" - the input wasn't valid

    user = {"id": next_id, "name": name, "email": email.lower()}
    next_id += 1
    users.append(user)

    return jsonify(user), 201
    # 201 is "Created" - a new resource was successfully created


@health_bp.put("/users/<int:user_id>")
def update_user(user_id: int) -> tuple[dict[str, object], int]:
    """PUT /users/:id - Update an existing user."""
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip()

    if len(name) < 2 or "@" not in email:
        return jsonify(error="Invalid name or email"), 400

    for user in users:
        if user["id"] == user_id:
            user["name"] = name
            user["email"] = email.lower()
            return jsonify(user), 200
    return jsonify(error="User not found"), 404


@health_bp.delete("/users/<int:user_id>")
def delete_user(user_id: int) -> tuple[dict[str, str], int]:
    """DELETE /users/:id - Delete a user by ID."""
    for index, user in enumerate(users):
        if user["id"] == user_id:
            users.pop(index)
            return jsonify(status="deleted"), 200
    return jsonify(error="User not found"), 404